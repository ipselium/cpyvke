#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : KernelDaemon5.py
# Creation Date : Fri Nov  4 21:49:15 2016
# Last Modified : mer. 14 déc. 2016 17:53:04 CET
# Created By : Cyril Desjouy
#
# Copyright © 2016-2017 Cyril Desjouy <ipselium@free.fr>
# Distributed under terms of the BSD license.
"""

DESCRIPTION

@author: Cyril Desjouy
"""

import argparse
import threading
import socket
import struct
import os
import sys
from time import sleep
from Queue import Queue
from daemon import Daemon
from jupyter_client import find_connection_file
from ktools import init_kernel, connect_kernel, print_kernel_list
from config import cfg_setup


def WhoToDict(string):
    ''' Format output of daemon to a dictionnary '''

    variables = {}
    for item in string.split('\n')[2:-1]:
        var_name = filter(None, item.split(' '))[0]
        var_typ = filter(None, item.split(' '))[1]
        var_val = filter(None, item.split(' '))[2:]
        var_val = ' '.join(var_val)
        if var_typ != 'function':
            variables[var_name] = {'value': var_val, 'type': var_typ}
    return variables


def send_msg(sock, msg):
    ''' Prefix each message with a 4-byte length (network byte order) '''
    msg = struct.pack('>I', len(msg)) + msg
    sock.sendall(msg)


def recv_msg(sock):
    ''' Read message length and unpack it into an integer '''
    raw_msglen = recv_all(sock, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    return recv_all(sock, msglen)


def recv_all(sock, n):
    ''' Helper function to recv n bytes or return None if EOF is hit '''
    data = ''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data


class Watcher(threading.Thread):
    '''
    Daemon : watch the kernel input and update variable list.
    The client may also request for the content of a variable.
    '''

    def __init__(self, kc, delay=0.1, sport=15555, rport=15556, verbose=False):

        # Init Thread
        threading.Thread.__init__(self)
        threading.Thread.daemon = True

        # Events
        self._stop = threading.Event()
        self._pause = threading.Event()

        # Inputs
        self.kc = kc
        self.delay = delay
        self.verbose = verbose
        if self.verbose:
            print('++++++++++++++++++++++++++++')
            print('Daemon started !')
            print('Delay set to ' + str(self.delay) + ' s.')
            print('Kernel : ' + str(self.kc.connection_file))

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

        print('____________________________')
        print('Streaming on ' + str(sport))
        print('Listening on ' + str(rport))
        print('____________________________')

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
                print('Request Socket closed !')
                break

            sleep(self.delay)

        streamer.join()
        self.MainSock.close()
        self.RequestSock.close()
        print('Exited')

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
                print('Stream Socket closed !')
                break

            sleep(self.delay)

    def UpdateStream(self):
        ''' If new entry in kernel, update variable list. '''

        if self.msg == 1:
            self.variables = self.Exec('whos')
            # Send to CUI
            if self.client_main:
                send_msg(self.client_main, self.variables)
                if self.verbose:
                    print('--> Variable list sent to client')

    def Pause(self):
        ''' Pause streamer when client has a request. '''

        if self._pause.isSet():

            if self.verbose:
                print('Streamer paused...')

            while self._pause.isSet():
                sleep(self.delay)

            if self.verbose:
                print('Streamer active')

    def CheckInput(self):
        ''' Check the iopub msgs available '''

        self.msg = 0
        while self.kc.iopub_channel.msg_ready():
            data = self.kc.get_iopub_msg(timeout=0.1)

            if self.verbose is True:
                print(data['msg_type'], data['content'])

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
                if self.verbose is True:
                    print('Execute result :')
                    print(data['content']['text'])

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
            if self.verbose:
                print("{} connected to main socket".format(address))
        except:
            pass
        else:
            send_msg(self.client_main, self.variables)
            if self.verbose:
                print('Client Initiated')

    def ListenRequestSockConnection(self):
        ''' Look for client connection to request socket. '''

        try:
            self.client_request, address = self.RequestSock.accept()
            if self.verbose:
                print("{} connected to request socket".format(address))
        except:
            pass

    def KernelChange(self, cf):
        ''' Watch kernel changes '''

        km, self.kc = connect_kernel(cf)
        # Force update
        self.variables = self.Exec('whos')
        # Send to CUI
        send_msg(self.client_main, self.variables)

    def ClientRequestSocket(self):
        ''' Listen to sock request :
            handle kernel changes | exec code | stop signal. '''

        tmp = recv_msg(self.client_request)

        if tmp:

            self._pause.set()
            sleep(self.delay)
            if self.verbose:
                print('Request from client :\n' + tmp)

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

        print("Client sent SIGTERM")
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
        self.verbose = WatcherArgs['verbose']

    def run(self):
        ''' Override Daemon run method with this method. '''

        km, kc = connect_kernel(self.cf)
        WK = Watcher(kc,
                     sport=self.sport,
                     rport=self.rport,
                     delay=self.delay,
                     verbose=self.verbose)
        WK.start()
        WK.join()


def ParseArgs(lockfile, pidfile):
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
            message = "pidfile %s already exist. Daemon already running?\n"
            sys.stderr.write(message % pidfile)
            sys.exit(1)
        else:
            kernel_id = StartAction(args, lockfile)

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


def StartAction(args, lockfile):
    ''' Start Parser action. '''

    if args.integer:
        try:
            kernel_id = str(args.integer)
            message = 'Connecting to kernel id. %s\n'
            sys.stdout.write(message % kernel_id)
            find_connection_file(kernel_id)
            with open(lockfile, "w") as f:
                f.write(kernel_id)
        except:
            message = 'Error :\tCannot find kernel id. %s !\n\tExiting\n'
            sys.stderr.write(message % args.integer)
            sys.exit(2)
    else:
        sys.stdout.write('Creating kernel...\n')
        from ktools import start_new_kernel
        kernel_id = start_new_kernel()
        message = 'Kernel id %s created\n'
        sys.stdout.write(message % kernel_id)
        with open(lockfile, "w") as f:
            f.write(kernel_id)

    return kernel_id


def StopAction(lockfile):
    ''' Parser Stop Action. '''

    try:
        with open(lockfile, "r") as f:
            kernel_id = f.readline()
    except:
        message = '%s not found. Daemon is not running. Try start action !\n'
        sys.stderr.write(message % lockfile)
        sys.exit(2)
    else:
        message = 'Disconnecting from kernel id. %s\n'
        sys.stdout.write(message % kernel_id)

    if os.path.exists(lockfile):
        os.remove(lockfile)

    return kernel_id


def RestartAction(lockfile):
    ''' Parser Restart action. '''

    try:
        with open(lockfile, "r") as f:
            return f.readline()
    except:
        message = '%s not found. Daemon is not running. Try start action !\n'
        sys.stderr.write(message % lockfile)
        sys.exit(2)


def main(args=None):
    ''' Main '''

    cfg = cfg_setup()
    Config = cfg.RunCfg()

    logdir = os.path.expanduser('~') + '/.cpyvke/'
    logfile = logdir + 'kd5.log'
    lockfile = logdir + 'kd5.lock'
    pidfile = logdir + 'kd5.pid'

    args, kernel_id = ParseArgs(lockfile, pidfile)

    sport = int(Config['comm']['s-port'])
    rport = int(Config['comm']['r-port'])
    delay = float(Config['daemon']['refresh'])
    verbose = True

    WatchConf = {'cf': find_connection_file(kernel_id),
                 'verbose': verbose,
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


