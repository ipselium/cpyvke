#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : KernelDaemon5.py
# Creation Date : Fri Nov  4 21:49:15 2016
# Last Modified : mar. 27 févr. 2018 12:46:41 CET
# Created By : Cyril Desjouy
#
# Copyright © 2016-2017 Cyril Desjouy <cyril.desjouy@free.fr>
# Distributed under terms of the BSD license.
"""

DESCRIPTION

@author: Cyril Desjouy
"""


import threading
import socket
import struct
import os
import select
from time import sleep
from queue import Queue
from daemon import Daemon
from jupyter_client import find_connection_file
from ktools import init_kernel, connect_kernel


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
    msg = struct.pack('>I', len(msg)) + msg.encode('utf-8')
    # msg = struct.pack('>I', len(msg)) + msg
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

    def __init__(self, kc, delay=0.1, port=15555, verbose=False):

        # Inputs
        threading.Thread.__init__(self)
        threading.Thread.daemon = True
        self._stop = threading.Event()
        self.kc = kc
        self.delay = delay
        self.verbose = verbose
        if self.verbose:
            print('++++++++++++++++++++++++++++')
            print('Daemon started !')
            print('Delay set to ' + str(self.delay) + ' s.')
            print('Kernel : ' + str(self.kc.connection_file))
        # Iinit Queue
        self.request_queue = Queue()
        self.kernel_queue = Queue()

        # Init Main Socket
        self.MainSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.MainSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.MainSock.bind(('', port))
        self.MainSock.listen(5)
        self.MainSock.setblocking(0)

        # Init Request Socket
        self.RequestSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.RequestSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.RequestSock.bind(('', 15556))
        self.RequestSock.listen(5)
        self.RequestSock.setblocking(0)

        print('++++++++++++++++++++++++++++')
        print('Socket created on port ' + str(port))
        print('++++++++++++++++++++++++++++')
        self.client = None
        self.client_request = None

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

            # Listen to code request (queue method)
            if self.request_queue.qsize() > 0:
                self.Exec(self.request_queue.get())

            # Listen to kernel changes (queue method)
            if self.kernel_queue.qsize() > 0:
                self.KernelChange(self.kernel_queue.get())

            # Terminate daemon
            if self._stop.isSet():
                self.MainSock.close()
                self.RequestSock.close()
                break

            sleep(self.delay)


    def StreamData(self):

        while True:

            # Look for connection to main socket
            self.ListenMainSockConnection()

            # Check in new entries in kernel
            self.CheckInput()

            # If new entries, update variables
            if self.msg == 1:
                self.variables = self.Exec('whos')
                # Send to CUI
                if self.client:
                    send_msg(self.client, self.variables)
                    if self.verbose:
                        print('--> Variables sent to client')

            # Terminate daemon
            if self._stop.isSet():
                self.MainSock.close()
                self.RequestSock.close()
                break

            sleep(self.delay)

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
            self.client, address = self.MainSock.accept()
            if self.verbose:
                print("{} connected to main socket".format(address))
        except:
            pass
        else:
            send_msg(self.client, self.variables)
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

    def RequestKernelChange(self, cf):
        ''' Send a request to daemon to change kernel. '''

        self.kernel_queue.put(cf)

    def KernelChange(self, cf):
        ''' Watch kernel changes '''

        km, self.kc = connect_kernel(cf)
        # Force update
        self.variables = self.Exec('whos')
        # Send to CUI
        send_msg(self.client, self.variables)

    def RequestCode(self, code):
        ''' Send a request to the daemon. '''

        self.request_queue.put(code)

    def ClientRequestSocket(self):
        ''' Listen to sock request :
            handle kernel changes | exec code | stop signal. '''

        tmp = recv_msg(self.client_request)
        if tmp:
            if '<cf>' in tmp:
                self.KernelChange(tmp.split('<cf>')[1])
            elif '<_stop_flag>' in tmp:
                self._stop.set()
            elif '<code>' in tmp:
                self.Exec(tmp.split('<code>')[1])

    def stop(self):
        ''' Stop thread. '''

        self._stop.set()


class Daemonize(Daemon):

    def __init__(self, pidfile, WatcherArgs, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        ''' Override __init__ Daemon method with this method. '''

        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.cf = WatcherArgs['cf']
        self.port = WatcherArgs['port']
        self.delay = WatcherArgs['delay']
        self.verbose = WatcherArgs['verbose']

    def run(self):
        ''' Override Daemon run method with this method. '''

        km, kc = connect_kernel(cf)
        WK = Watcher(kc, port=self.port, delay=self.delay, verbose=self.verbose)
        WK.start()
        WK.join()


if __name__ == "__main__":

    import sys

    cf = find_connection_file('4988')
    port = 15555
    delay = 0.1
    verbose = True

    WatchConf = {'cf': cf, 'verbose': verbose, 'delay': delay, 'port': port}
    logfile = os.path.expanduser('~') + '/.cpyvke/kd5.log'
    daemon = Daemonize('/tmp/kd5.pid', WatchConf, stdout=logfile, stderr=logfile)

    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            print('kd5 started...')
            daemon.start()
        elif 'stop' == sys.argv[1]:
            print('kd5 stopped...')
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            print('kd5 restarted...')
            daemon.restart()
        else:
            print('Unknown command')
            sys.exit(2)
        sys.exit(0)
    else:
        print("usage: %s start|stop|restart" % sys.argv[0])
        sys.exit(2)
