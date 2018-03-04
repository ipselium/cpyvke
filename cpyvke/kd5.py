#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : KernelDaemon5.py
# Creation Date : Fri Nov  4 21:49:15 2016
# Last Modified : dim. 04 mars 2018 16:33:50 CET
# Created By : Cyril Desjouy
#
# Copyright © 2016-2017 Cyril Desjouy <ipselium@free.fr>
# Distributed under terms of the BSD license.
"""

DESCRIPTION

@author: Cyril Desjouy
"""

import threading
import socket
import os
import sys
import argparse
import logging
from logging.handlers import RotatingFileHandler
from jupyter_client import find_connection_file
from time import sleep
try:
    from Queue import Queue
except ImportError:
    from queue import Queue

from .ktools import init_kernel, connect_kernel, print_kernel_list, start_new_kernel
from .stools import send_msg, recv_msg
from .config import cfg_setup
from .daemon3x import Daemon


logger = logging.getLogger('kd5')


class Watcher(threading.Thread):
    '''
    Daemon : watch the kernel input and update variable list.
    The client may also request for the content of a variable.
    '''

    def __init__(self, kc, delay=0.1, sport=15555, rport=15556):

        # Init Thread
        threading.Thread.__init__(self)
        threading.Thread.daemon = True

        # Events
        self._stop = threading.Event()
        self._pause = threading.Event()

        # Inputs
        self.kc = kc
        self.delay = delay

        # Queue
        self.kernel_queue = Queue()

        # Init Main Socket
        self.MainSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.MainSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.MainSock.bind(('', sport))
        self.MainSock.listen(5)
        self.MainSock.setblocking(0)
        self.client_main = None

        # Init Request Socket
        self.RequestSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.RequestSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.RequestSock.bind(('', rport))
        self.RequestSock.listen(5)
        self.RequestSock.setblocking(0)
        self.client_request = None

        logger.info('++++++++++++++++++++++++++++')
        logger.info('Daemon started !')
        logger.info('Delay set to {} s.'.format(self.delay))
        logger.info('Kernel : {}'.format(self.kc.connection_file))
        logger.info('Streaming on {}'.format(sport))
        logger.info('Listening on {}'.format(rport))
        logger.info('++++++++++++++++++++++++++++')

        # Init variables
        self.msg = 0
        self.CheckInput()
        self.variables = self.Exec('whos')

    def run(self):
        ''' Run the variable explorer daemon '''

        # Launch streamer
        streamer = threading.Thread(target=self.StreamData)
        streamer.start()

        while True:

            # Look for connection to request socket
            self.ListenRequestSockConnection()

            # Watch RequestSock for code request OR kernel changes
            if self.client_request:
                self.ClientRequestSocket()

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

    def StreamData(self):
        ''' Stream 'whos' output to client. '''

        while True:

            # Pause if client has a request
            self.Pause()

            # Look for connection to main socket
            self.ListenMainSockConnection()

            # Listen to kernel changes
            if self.kernel_queue.qsize() > 0:
                self.KernelChange(self.kernel_queue.get())

            # Check in new entries in kernel
            self.CheckInput()

            # If new entries, update variables
            self.UpdateStream()

            # Terminate daemon
            if self._stop.isSet():
                logger.info('Stream Socket closed !')
                break

            sleep(self.delay)

    def UpdateStream(self):
        ''' If new entry in kernel, update variable list. '''

        if self.msg == 1:
            self.variables = self.Exec('whos')
            # Send to CUI
            if self.client_main:
                try:
                    send_msg(self.client_main, self.variables)
                except:
                    logger.info("Client is disconnected from main socket!")
                    self.client_main = None
                else:
                    logger.info('Variable list sent to client')

    def Pause(self):
        ''' Pause streamer when client has a request. '''

        if self._pause.isSet():

            logger.debug('Streamer paused...')

            while self._pause.isSet():
                sleep(self.delay)

            logger.debug('Streamer active')

    def CheckInput(self):
        ''' Check the iopub msgs available '''

        self.msg = 0
        while self.kc.iopub_channel.msg_ready():
            data = self.kc.get_iopub_msg(timeout=0.1)

            logger.debug('{} {}'.format(data['msg_type'], data['content']))

            # Wait for answer when execute reset
            if data['msg_type'] == 'execute_input':
                if data['content']['code'] == 'reset':
                    init_kernel(self.kc)
                    data = self.kc.get_iopub_msg()

            # Wait for end execution (script)
            if data['msg_type'] == 'execute_input':
                if 'run' in data['content']['code']:
                    data = self.kc.get_iopub_msg()

            # For long script with output to sdtout
            while data['msg_type'] == 'stream':
                data = self.kc.get_iopub_msg()

            self.msg = 1

    def Exec(self, code):
        ''' Execute **code** '''

        value = 'No Value !'

        self.kc.execute(code, store_history=False)

        while self.kc.iopub_channel.msg_ready() == False:  # To fix.Have to wait
            sleep(self.delay)

        while self.kc.iopub_channel.msg_ready():
            data = self.kc.get_iopub_msg()
            if data['msg_type'] == 'stream' and code == 'whos':
                value = data['content']['text']
                logger.debug('Execute result :\n {}'.format(data['content']['text']))

            elif data['msg_type'] == 'execute_result' and code != 'whos':
                value = data['content']['data']['text/plain']

            elif data['msg_type'] == 'stream' and code != 'whos':
                value = data['content']['text']

        self.msg = 0

        return value

    def ListenMainSockConnection(self):
        ''' Look for client connection to main socket. '''

        try:
            self.client_main, address = self.MainSock.accept()
            logger.info("{} connected to main socket".format(address))
        except BlockingIOError:
            pass
        else:
            send_msg(self.client_main, self.variables)

    def ListenRequestSockConnection(self):
        ''' Look for client connection to request socket. '''

        try:
            self.client_request, address = self.RequestSock.accept()
            logger.info("{} connected to request socket".format(address))
        except BlockingIOError:
            pass

    def KernelChange(self, cf):
        ''' Watch kernel changes '''

        km, self.kc = connect_kernel(cf)
        # Force update
        self.variables = self.Exec('whos')
        # Send to CUI
        try:
            send_msg(self.client_main, self.variables)
        except:
            logger.info("Client is disconnected from main socket!")
            self.client_main = None

    def ClientRequestSocket(self):
        ''' Listen to sock request :
            handle kernel changes | exec code | stop signal. '''

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
            logger.debug('Execute :\n {}'.format(tmp))

            if '<cf>' in tmp:
                cf = tmp.split('<cf>')[1]
                km, self.kc = connect_kernel(cf)    # Connect request to new k
                self.kernel_queue.put(cf)           # Send new k to streamer

            elif '<_stop>' in tmp:
                self.stop()

            elif '<code>' in tmp:
                self.Exec(tmp.split('<code>')[1])

            self._pause.clear()

    def stop(self):
        ''' Stop thread. '''

        logger.info("Client sent SIGTERM")
        self._stop.set()


class Daemonize(Daemon):

    def __init__(self,
                 pidfile,
                 WatcherArgs,
                 stdin='/dev/null',
                 stdout='/dev/null',
                 stderr='/dev/null'):
        ''' Override __init__ Daemon method with this method. '''

        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.cf = WatcherArgs['cf']
        self.sport = WatcherArgs['sport']
        self.rport = WatcherArgs['rport']
        self.delay = WatcherArgs['delay']

    def run(self):
        ''' Override Daemon run method with this method. '''

        km, kc = connect_kernel(self.cf)
        WK = Watcher(kc,
                     sport=self.sport,
                     rport=self.rport,
                     delay=self.delay)
        WK.start()
        WK.join()


def ParseArgs(lockfile, pidfile, Config):
    ''' Parse arguments. '''

    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('start', 'stop', 'restart', 'list'))
    parser.add_argument("integer",
                        help="Start up with existing kernel. \
                        INTEGER is the id of the connection file.",
                        nargs='?')
    args = parser.parse_args()

    # Start action
    if args.action == 'start':
        if os.path.exists(pidfile):
            message = "pidfile {} already exist. Daemon already running?\n"
            sys.stderr.write(message.format(pidfile))
            sys.exit(1)
        else:
            kernel_id = StartAction(args, lockfile, Config)

    # Stop action
    elif args.action == 'stop':
        kernel_id = StopAction(lockfile)

    # Restart action
    elif args.action == 'restart':
        kernel_id = RestartAction(lockfile)

    # List action
    elif args.action == 'list':
        print_kernel_list()
        sys.exit(2)

    return args, kernel_id


def StartAction(args, lockfile, Config):
    ''' Start Parser action. '''

    if args.integer:
        try:
            kernel_id = str(args.integer)
            message = 'Connecting to kernel id. {}\n'
            sys.stdout.write(message.format(kernel_id))
            find_connection_file(kernel_id)
            with open(lockfile, "w") as f:
                f.write(kernel_id)
        except:
            message = 'Error :\tCannot find kernel id. {} !\n\tExiting\n'
            sys.stderr.write(message.format(args.integer))
            sys.exit(2)
    else:
        sys.stdout.write('Creating kernel...\n')
        kernel_id = start_new_kernel(version=Config['kernel version']['version'])
        message = 'Kernel id {} created (Python {})\n'
        sys.stdout.write(message.format(kernel_id, Config['kernel version']['version']))
        with open(lockfile, "w") as f:
            f.write(kernel_id)

    return kernel_id


def StopAction(lockfile):
    ''' Parser Stop Action. '''

    try:
        with open(lockfile, "r") as f:
            kernel_id = f.readline()
    except:
        message = '{} not found. Daemon is not running. Try start action !\n'
        sys.stderr.write(message.format(lockfile))
        sys.exit(2)
    else:
        message = 'Disconnecting from kernel id. {}\n'
        sys.stdout.write(message.format(kernel_id))

    if os.path.exists(lockfile):
        os.remove(lockfile)

    return kernel_id


def RestartAction(lockfile):
    ''' Parser Restart action. '''

    try:
        with open(lockfile, "r") as f:
            return f.readline()
    except:
        message = '{} not found. Daemon is not running. Try start action !\n'
        sys.stderr.write(message.format(lockfile))
        sys.exit(2)


def main(args=None):
    ''' Main '''

    cfg = cfg_setup()
    Config = cfg.RunCfg()

    logdir = os.path.expanduser('~') + '/.cpyvke/'
    logfile = logdir + 'kd5.log'
    lockfile = logdir + 'kd5.lock'
    pidfile = logdir + 'kd5.pid'

    # Logger
    logger.setLevel(logging.DEBUG)

    # create the logging file handler
    handler = RotatingFileHandler(logfile, maxBytes=10*1024*1024,
                                  backupCount=5)
    formatter = logging.Formatter('%(asctime)s :: %(name)s :: %(threadName)s :: %(levelname)s :: %(message)s', datefmt='%Y-%m-%d - %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Parse Arguments
    args, kernel_id = ParseArgs(lockfile, pidfile, Config)

    sport = int(Config['comm']['s-port'])
    rport = int(Config['comm']['r-port'])
    delay = float(Config['daemon']['refresh'])

    WatchConf = {'cf': find_connection_file(kernel_id),
                 'delay': delay,
                 'sport': sport,
                 'rport': rport}

    daemon = Daemonize(pidfile, WatchConf, stdout=logfile, stderr=logfile)

    if args.action == 'stop':
        daemon.stop()
        sys.stdout.write('kd5 stopped !\n')
    elif args.action == 'start':
        sys.stdout.write('kd5 starting...\n')
        daemon.start()
    elif args.action == 'restart':
        sys.stdout.write('kd5 restarting...\n')
        daemon.restart()


if __name__ == "__main__":

    main()


