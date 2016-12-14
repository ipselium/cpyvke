#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : daemon_socket.py
# Creation Date : jeu. 24 nov. 2016 14:48:35 CET
# Last Modified : jeu. 08 déc. 2016 13:41:49 CET
# Created By : Cyril Desjouy
#
# Copyright © 2016-2017 Cyril Desjouy <cyril.desjouy@free.fr>
# Distributed under terms of the BSD license.
"""

DESCRIPTION

@author: Cyril Desjouy
"""

###############################################################################
# IMPORTS
###############################################################################
from time import sleep
import threading
from ktools import init_kernel
import socket
from Queue import Queue


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


class Watcher():
    def __init__(self, kc, delay=0.5):
        ''' Init Watcher Class '''

        # Inputs
        self.kc = kc
        self.delay = delay

        # Init Queue
        self.qreq = Queue()

        # Init variables
        self.stop = False
        self.msg = 0
        self.CheckInput()
        self.variables = self.Exec('whos')

        # Init Socket
        self.LKsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.LKsock.bind(('', 15555))
        self.LKsock.listen(5)
        self.LKsock.setblocking(0)

        self.client = None

###############################################################################
    def run(self):
        ''' Run the variable explorer daemon '''

        while self.stop is False:

            try:
                self.client, address = self.LKsock.accept()
                print("{} connected".format(address))
            except:
                pass
            else:
                print('Init client')
                self.client.send(self.variables)

            # Check in new entries in kernel
            self.CheckInput()

            # If new entries, update variables
            if self.msg == 1:
                self.variables = self.Exec('whos')
                # Send to CUI
                print(self.variables)
                if self.client:
                    print('Send to client')
                    self.client.send(self.variables)

            sleep(self.delay)

###############################################################################
    def CheckInput(self):
        ''' Check the iopub msgs available '''

        self.msg = 0
        while self.kc.iopub_channel.msg_ready():
            data = self.kc.get_iopub_msg(timeout=0.1)

            print(data['msg_type'])
            print(data['content'])
            print('\n')

            self.msg = 1

###############################################################################
    def Exec(self, code):
        ''' Execute **code** '''

        self.kc.execute(code, store_history=False)

        while self.kc.iopub_channel.msg_ready() == False:  # To fix.Have to wait
            sleep(0.5)

        while self.kc.iopub_channel.msg_ready():
            data = self.kc.get_iopub_msg(timeout=0.1)

            if data['msg_type'] == 'stream' and code == 'whos':
                value = data['content']['text']
                print(data['content']['text'])

            elif data['msg_type'] == 'execute_result' and code != 'whos':
                value = data['content']['data']['text/plain']

        self.msg = 0

        return value


if __name__ == "__main__":

    from KernelTools import connect_kernel
    from jupyter_client import find_connection_file

    delay = 0.5
    cf = find_connection_file('27146')
    km, kc = connect_kernel(cf)

    WK = Watcher(kc, delay)
    WK.run()

# print "Close"
# client.close()
# stock.close()


