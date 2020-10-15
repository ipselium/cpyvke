#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright © 2016-2018 Cyril Desjouy <ipselium@free.fr>
#
# This file is part of cpyvke
#
# cpyvke is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# cpyvke is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with cpyvke.  If not, see <http://www.gnu.org/licenses/>.
#
#
# Creation Date : Fri Nov  4 21:49:15 2016
# Last Modified : lun. 09 avril 2018 21:32:29 CEST
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import os
import sys
import threading
import socket
import argparse
import logging
import psutil
from time import sleep
from queue import Queue
from logging.handlers import RotatingFileHandler
from jupyter_client import find_connection_file

from .utils.kernel import init_kernel, connect_kernel, print_kernel_list, \
    start_new_kernel, set_kid
from .utils.kd import is_kd_running, find_lost_pid, kdwrite, kdread
from .utils.comm import send_msg, recv_msg
from .utils.daemon3x import Daemon
from .utils.config import cfg_setup
from .utils.term_colors import RED, BLUE, CYAN, RESET

logger = logging.getLogger('kd5')


class Watcher(threading.Thread):
    """
    Daemon : watch the kernel input and update variable list.
    The client may also request for the content of a variable.
    """

    def __init__(self, kc, delay=0.1, sport=15557, rport=15556):
        """ Class constructor """

        logger.info('++++++++++++++++++++++++++++')
        logger.info('Initialize Watcher')

        # Init Thread
        threading.Thread.__init__(self)
        threading.Thread.daemon = True

        logger.info('Watcher sent to thread')

        # Events
        self._stop = threading.Event()
        self._pause = threading.Event()
        logger.info('Events created')

        # Inputs
        self.kc = kc
        self.delay = delay

        # Queue
        self.kernel_queue = Queue()
        logger.info('Queue created')


        # Init Main Socket
        try:
            self.MainSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.MainSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.MainSock.bind(('', sport))
            self.MainSock.listen(5)
            self.MainSock.setblocking(0)
            self.client_main = None
            logger.info('Main socket created')
        except Exception as e:
            logger.info(e)
            logger.info('Exiting...')
            sys.exit(1)

        # Init Request Socket
        try:
            self.RequestSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.RequestSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.RequestSock.bind(('', rport))
            self.RequestSock.listen(5)
            self.RequestSock.setblocking(0)
            self.client_request = None
            logger.info('Request socket created')
        except Exception as e:
            logger.info(e)
            logger.info('Exiting...')
            sys.exit(1)


        logger.info('++++++++++++++++++++++++++++')
        logger.info('Daemon started !')
        logger.info('Delay set to {} s.'.format(self.delay))
        logger.info('Kernel : {}'.format(self.kc.connection_file))
        logger.info('Streaming on {}'.format(sport))
        logger.info('Listening on {}'.format(rport))
        logger.info('++++++++++++++++++++++++++++')

        # Init variables
        self.msg = 0
        self.check_input()
        self.variables = ''

    def run(self):
        """ Run the variable explorer daemon """

        # Launch streamer
        streamer = threading.Thread(target=self.stream_data)
        streamer.start()

        while True:

            # Look for connection to request socket
            self.listen_request_sock()

            # Watch RequestSock for code request OR kernel changes
            if self.client_request:
                self.fetch_request()

            # Terminate daemon
            if self._stop.isSet():
                logger.info('Request Socket closed !')
                break

            sleep(self.delay)

        streamer.join()
        # Close connection to clients
        self.MainSock.shutdown()
        self.RequestSock.shutdown()
        # Destroy socket
        self.MainSock.close()
        self.RequestSock.close()
        logger.info('Exited')

    def stream_data(self):
        """ Stream 'whos' output to client. """

        while True:

            # Pause if client has a request
            self.pause()

#            # Check if reset has been invoked
#            if 'empty' in self.variables:
#                init_kernel(self.kc)

            # Look for connection to main socket
            self.listen_main_sock()

            # Listen to kernel changes
            if self.kernel_queue.qsize() > 0:
                self.kernel_change(self.kernel_queue.get())

            # Check in new entries in kernel
            self.check_input()

            # If new entries, update variables
            if self.msg == 1:
                self.send_variables()

            # Terminate daemon
            if self._stop.isSet():
                logger.info('Stream Socket closed !')
                break

            sleep(self.delay)

    def pause(self):
        """ Pause streamer when client has a request. """

        if self._pause.isSet():

            logger.debug('Streamer paused...')

            while self._pause.isSet():
                sleep(self.delay)

            logger.debug('Streamer active')

            # Force Update var list
            self.send_variables()

    def check_input(self):
        """ Check the iopub msgs available """

        self.msg = 0
        while self.kc.iopub_channel.msg_ready():
            data = self.kc.get_iopub_msg(timeout=0.1)
            logger.debug('WATCHING : {}'.format(self.disp_data(data)))
            self.msg = 1
            self.check_init(data)

    def check_init(self, data):
        if 'code' in data['content'].keys():
            if 'reset' in data['content']['code']:
                init_kernel(self.kc)
                logger.debug('RESET RECEIVED : {}'.format('Init Kernel'))

    def execute(self, code):
        """ Execute **code** """

        value = None
        MSG_RECEIVED = False

        msg_id = self.kc.execute(code, store_history=False)
        logger.debug("EXEC : '{}' sent with id {}".format(code, msg_id.split('-')[0]))

        while not MSG_RECEIVED:
            self.wait_msg()

            while self.kc.iopub_channel.msg_ready():
                data = self.kc.get_iopub_msg()
                if data['parent_header']['msg_id'] != msg_id:
                    logger.debug('EXEC : PASS MSG : {}'.format(self.disp_data(data)))
                    self.check_init(data)
                    continue
                else:
                    MSG_RECEIVED = True
                    logger.debug('EXEC : PROCEED MSG : {}'.format(self.disp_data(data)))
                    if data['header']['msg_type'] == 'stream':
                        value = data['content']['text']

        logger.debug('EXEC : RESULT :\n {}'.format(value))
        self.msg = 0

        return value

    def wait_msg(self):
        """ Waiting for message from iopub channel """

        while not self.kc.iopub_channel.msg_ready():  # To fix.Have to wait
            sleep(self.delay)

    def listen_main_sock(self):
        """ Look for client connection to main socket. """

        try:
            self.client_main, address = self.MainSock.accept()
            logger.info("{} connected to main socket".format(address))
        except BlockingIOError:
            pass
        else:
            send_msg(self.client_main, self.variables)

    def listen_request_sock(self):
        """ Look for client connection to request socket. """

        try:
            self.client_request, address = self.RequestSock.accept()
            logger.info("{} connected to request socket".format(address))
        except BlockingIOError:
            pass

    def check_variables(self):
        """ If variables is None, ask again to kernel """
        if not self.variables:
            logger.debug("EXEC : 'variables' is None : RUN AGAIN 'whos'")
        while not self.variables:
            self.variables = self.execute('whos')

    def kernel_change(self, cf):
        """ Watch kernel changes """

        old_id = set_kid(self.kc.connection_file)
        _, self.kc = connect_kernel(cf)
        new_id = set_kid(self.kc.connection_file)

        # Update kd5.lock files
        self.update_lockfile(new_id)
        logger.info('Kernel change from {} to {}'.format(old_id, new_id))

        # Force kernel update
        self.send_variables()

    def update_lockfile(self, new_id):
        """ Update lock files """

        LogDir = os.path.expanduser("~") + "/.cpyvke/"

        with open(LogDir + 'kd5.lock', 'w') as f:
            f.write(new_id)

    def send_variables(self):
        """ Send variable to client """

        self.variables = self.execute('whos')
        self.check_variables()
        # Send to client
        if self.client_main:
            try:
                send_msg(self.client_main, self.variables)
            except BlockingIOError:
                logger.info("Client is disconnected from main socket!")
                self.client_main = None
            else:
                logger.info('Variable list sent to client')

    @staticmethod
    def disp_id(data):
        """ Display first seq of message id only """
        return data['parent_header']['msg_id'].split('-')[0]

    @classmethod
    def disp_data(cls, data):
        if data['msg_type'] == 'status':
            dbg = '{} | status : {}'.format(cls.disp_id(data), data['content']['execution_state'])
        elif data['msg_type'] == 'execute_input':
            dbg = '{} | code : {}'.format(cls.disp_id(data), data['content']['code'])
        elif data['msg_type'] == 'stream':
            dbg = '{} | stream'.format(cls.disp_id(data))
        elif data['msg_type'] == 'error':
            dbg = '{} | error : {}'.format(cls.disp_id(data), data['content']['ename'])
        else:
            dbg = '{} {}'.format(cls.disp_id(data), data['msg_type'])
        return dbg

    def fetch_request(self):
        """ Listen to sock request :
            handle kernel changes | exec code | stop signal. """

        try:
            tmp = recv_msg(self.client_request).decode('utf8')
        except AttributeError:
            tmp = None
            self.client_request = None
            logger.info("Client is disconnected from request socket!")

        if tmp:
            self._pause.set()
            sleep(self.delay)
            logger.info('Request from client')
            logger.debug('RECEIVED :\n {}'.format(tmp))

            if '<cf>' in tmp:
                cf = tmp.split('<cf>')[1]
                self.kernel_queue.put(cf)           # Send new k to streamer

            elif '<_stop>' in tmp:
                self.stop()

            elif '<code>' in tmp:
                self.execute(tmp.split('<code>')[1])

            self._pause.clear()

    def stop(self):
        """ Stop thread. """

        logger.info("Client sent SIGTERM")
        self._stop.set()


class Daemonize(Daemon):
    """ Daemonize a class """

    def __init__(self,
                 pidfile,
                 WatcherArgs,
                 stdin='/dev/null',
                 stdout='/dev/null',
                 stderr='/dev/null'):
        """ Override __init__ Daemon method with this method. """

        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.cf = WatcherArgs['cf']
        self.sport = WatcherArgs['sport']
        self.rport = WatcherArgs['rport']
        self.delay = WatcherArgs['delay']

    def run(self):
        """ Override Daemon run method with this method. """

        km, kc = connect_kernel(self.cf)
        WK = Watcher(kc,
                     sport=self.sport,
                     rport=self.rport,
                     delay=self.delay)
        WK.start()
        WK.join()


def parse_args(lockfile, pidfile, Config):
    """ Parse arguments. """

    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('start', 'stop', 'restart',
                                           'last', 'status', 'list'))
    parser.add_argument("integer",
                        help="Start up with existing kernel. \
                        INTEGER is the id of the connection file.",
                        nargs='?')
    args = parser.parse_args()

    # start|last actions
    if args.action in ['start', 'last']:
        current_pid = status_pid(pidfile)
        if current_pid:
            sys.stderr.write("Cannot start new instance of kd5.\n")
            sys.exit(1)
        else:
            kid = start_action(args, lockfile, Config)

    # restart action
    elif args.action == 'restart':
        kid = restart_action(pidfile, lockfile)

    # Stop action
    elif args.action == 'stop':
        kid = stop_action(pidfile, lockfile)

    # List action
    elif args.action == 'list':
        print_kernel_list()
        sys.exit(0)

    # Status action
    elif args.action == 'status':
        status_action(pidfile, lockfile)
        sys.exit(0)

    return args, kid


def create_new(Config):
    """ Create new kernel """

    sys.stdout.write('Creating new kernel...\n')
    kid = start_new_kernel(version=Config['kernel version']['version'])
    message = 'Kernel id {} created (Python {})\n'
    sys.stdout.write(message.format(kid, Config['kernel version']['version']))

    return kid


def start_action(args, lockfile, Config):
    """ Start Parser action. """

    if args.integer:

        try:
            kid = str(args.integer)
            find_connection_file(kid)
        except OSError:
            message = '{}Error :\t{}Cannot find kernel id. {} !\n\tExiting\n'
            sys.stderr.write(message.format(RED, RESET, args.integer))
            sys.exit(1)
        else:
            message = 'Connecting to kernel id. {}\n'
            sys.stdout.write(message.format(kid))

    elif args.action == 'last':
        kid = kdread(lockfile)
        if kid:
            message = 'Connecting to kernel id. {}\n'
            sys.stdout.write(message.format(kid))
        else:
            sys.exit(1)

    else:
        kid = create_new(Config)

    kdwrite(lockfile, kid)

    return kid


def restart_action(pidfile, lockfile):
    """ Prepare restart action """

    current_pid = status_pid(pidfile)
    kid = status_lock(lockfile)
    if current_pid and kid:
        return kid
    else:
        sys.stdout.write('Cannot restart kd5.\n')
        sys.exit(1)


def stop_action(pidfile, lockfile):
    """ Prepare stop action """

    current_pid = status_pid(pidfile)
    kid = status_lock(lockfile)
    if current_pid:
        if kid:
            message = 'Disconnecting from kernel id. {}\n'
            sys.stdout.write(message.format(kid))
            return kid
        else:
            message = 'SIGTERM sent to kd5\n'
            p = psutil.Process(int(current_pid))
            p.terminate()
            os.remove(pidfile)
            sys.stdout.write(message.format(kid))
            sys.exit(1)
    else:
        sys.exit(1)


def status_action(pidfile, lockfile):

    status_pid(pidfile)
    status_lock(lockfile)


def status_pid(pidfile):
    """ Status of the daemon """

    if os.path.exists(pidfile):
        if is_kd_running(pidfile):
            message = "{}Current state : {}running{} with pid {}!\n"
            sys.stderr.write(message.format(CYAN, BLUE, RESET, kdread(pidfile)))
            return kdread(pidfile)
        else:
            message = "{}Current state : {}stopped{}, but pidfile still exists !\nFix : {} deleted !\n"
            sys.stderr.write(message.format(CYAN, RED, RESET, pidfile))
            os.remove(pidfile)
            return None
    else:
        pids = find_lost_pid()
        if len(pids) == 1:
            message = "{}Current state : {}running{} with pid {}, but pidfile has been removed !\nFix : {} created\n"
            sys.stderr.write(message.format(CYAN, BLUE, RESET, pids[0], pidfile))
            with open(pidfile, 'w') as f:
                f.write(str(pids[0]))
            return pids[0]
        elif len(pids) == 0:
            message = "{}Current state : {}stopped{} \n"
            sys.stderr.write(message.format(CYAN, RED, RESET))
            return None
        elif len(pids) > 1:
            message = "{}Current state : {}multiple instances of kd5 are running !\nExiting ..."
            sys.stderr.write(message.format(CYAN, RESET))
            sys.exit(1)


def status_lock(lockfile):
    """ Information about the kernel to which the daemon is connected """

    if os.path.exists(lockfile):
        return kdread(lockfile)
    else:
        sys.stderr.write('Kernel id. not found !\n')
        return None


def main(args=None):
    """ Main """

    cfg = cfg_setup()
    Config = cfg.run()

    logdir = os.path.expanduser('~') + '/.cpyvke/'
    logfile = logdir + 'kd5.log'
    lockfile = logdir + 'kd5.lock'
    pidfile = logdir + 'kd5.pid'

    # Logger
    logger.setLevel(logging.DEBUG)

    # create the logging file handler
    handler = RotatingFileHandler(logfile, maxBytes=10*1024*1024,
                                  backupCount=5)
    logmsg = '%(asctime)s :: %(name)s :: %(threadName)s :: %(levelname)s :: %(message)s'
    formatter = logging.Formatter(logmsg, datefmt='%Y-%m-%d - %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Parse Arguments
    args, kid = parse_args(lockfile, pidfile, Config)

    sport = int(Config['comm']['s-port'])
    rport = int(Config['comm']['r-port'])
    delay = float(Config['daemon']['refresh'])

    try:
        cfile = find_connection_file(kid)
    except OSError:
        sys.stderr.write('Lockfile points to an unknown connection file !\n')
        kid = create_new(Config)
        cfile = find_connection_file(kid)
        kdwrite(lockfile, kid)

    WatchConf = {'cf': cfile,
                 'delay': delay,
                 'sport': sport,
                 'rport': rport}

    daemon = Daemonize(pidfile, WatchConf, stdout=logfile, stderr=logfile)

    if args.action == 'stop':
        daemon.stop()
        sys.stdout.write('kd5 stopped !\n')
    elif args.action == 'start' or args.action == 'last':
        sys.stdout.write('kd5 starting...\n')
        daemon.start()
    elif args.action == 'restart':
        sys.stdout.write('kd5 restarting...\n')
        daemon.restart()


if __name__ == "__main__":
    main()
