#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : KernelDaemon.py
# Creation Date : Fri Nov  4 21:49:15 2016
# Last Modified : mar. 22 nov. 2016 17:36:13 CET
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
from IPython.lib.kernel import find_connection_file
from IPython.kernel import BlockingKernelClient
from Queue import Empty, Full
from time import sleep
from threading import Thread
###############################################################################
###############################################################################
###############################################################################


###############################################################################
###############################################################################
###############################################################################
###############################################################################
def connect_kernel(kernel_id):
    ''' '''

    cf = find_connection_file(kernel_id)
    # Kernel manager
    km = BlockingKernelClient(connection_file=cf)
    # load connection info and init communication
    km.load_connection_file()
    km.start_channels()
    km.shell_channel.execute("import numpy as np", store_history=None)
    km.shell_channel.execute("np.set_printoptions(threshold='nan')", store_history=None)
    return km


###############################################################################
# Transform whos output to dictionnary
###############################################################################
def WhoToDict(string):
    ''' '''

    variables = {}
    for item in string.split('\n')[2:-1]:
        var_name = filter(None, item.split(' '))[0]
        var_typ = filter(None, item.split(' '))[1]
        var_val = filter(None, item.split(' '))[2:]
        var_val = ' '.join(var_val)
        variables[var_name] = {'value': var_val, 'type': var_typ}
    return variables


###############################################################################
###############################################################################
###############################################################################
class Watcher(Thread):
    def __init__(self, km, delay, qstop, qvar, qreq, qans, ONLY_DAEMON=False):
        Thread.__init__(self)
        self.km = km
        self.delay = delay
        self.qstop = qstop
        self.qvar = qvar
        self.qreq = qreq
        self.qans = qans
        self.ONLY_DAEMON = ONLY_DAEMON
        try:
            self.msg, self.variables = self.Exec('whos', True)
        except:
            self.msg = 0
            self.variables = str()
            pass


###############################################################################
    def run(self):
        ''' Variable manager daemon '''

        self.qvar.put(WhoToDict(self.variables))

        while True:

            # Listen to new variables in the kernel
            try:
                data = self.km.get_iopub_msg(timeout=0.1)
                self.msg = 1
            except Empty:
                pass
            else:
                try:
                    if data['content']['execution_state'] == 'idle' and self.msg == 1:
                        self.msg, self.variables = self.Exec('whos')
                        if self.ONLY_DAEMON is True:
                            print(WhoToDict(self.variables))
                except KeyError:
                    pass
                else:
                    # Send variables to CUI
                    try:
                        if self.qvar.qsize() > 0:
                            self.qvar.queue.clear()
                        self.qvar.put(WhoToDict(self.variables))
                    except Full:
                        pass

            # Listen if CUI request a value
            if self.qreq.qsize() > 0:
                self.msg, value = self.Exec(self.qreq.get(), True)
                with open("debug.txt", "w") as text_file:
                    text_file.write(value)
                self.qans.put(value)

            # Terminate daemon
            if self.qstop.qsize() > 0:
                stop = self.qstop.get(timeout=0)
                if stop:
                    self.km.stop_channels()
                    break

            sleep(self.delay)

###############################################################################
    def Exec(self, code, FORCE_EXEC=False):
        ''' Execute whos in the kernel and get output '''

        if FORCE_EXEC is True:
            self.msg = 1

        try:
            self.km.shell_channel.execute(code, store_history=None)
        except:
            pass

        while self.msg == 1:
            try:
                data = self.km.get_iopub_msg(timeout=0.1)
                if code == 'whos':
                    tmp = data['content']['data']
                else:
                    tmp = data['content']['data']['text/plain']
                if self.ONLY_DAEMON is True:
                    print(tmp)
            except KeyError:
                pass
            else:
                data = self.km.get_iopub_msg(timeout=0.1)
                self.msg = 0

        return self.msg, tmp
