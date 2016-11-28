#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : KernelTools.py
# Creation Date : Fri Nov  4 21:49:15 2016
# Last Modified : lun. 28 nov. 2016 16:26:02 CET
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
from jupyter_client import BlockingKernelClient, manager
from Queue import Empty
from time import sleep
import os
import subprocess


# ------------------------------------------------------------------------------
################################################################################
# Definitions
################################################################################
# ------------------------------------------------------------------------------
def start_new_kernel():
    ''' Start a new kernel and return the kernel_id '''

    with open("kcreate.log", "w") as f:
        subprocess.Popen(["ipython", "kernel"], stdout=f)

    sleep(1)
    with open("kcreate.log", "r") as f:
        stdout = f.read()

    return stdout.split('kernel-')[1].split('.json')[0]


###############################################################################
def is_runing(cf):
    ''' Check if kernel is alive '''
    kc = BlockingKernelClient()
    kc.load_connection_file(cf)
    kc.execute('whos', store_history=False)
    try:
        kc.get_iopub_msg(timeout=0.1)
    except Empty:
        return False
    else:
        return True


###############################################################################
def kernel_list(cf=None):
    ''' List of connection files '''
    path = '/run/user/1000/jupyter/'
    lst = [(path + item, '[Alive]' if is_runing(path + item) else '[Died]') for item in os.listdir(path)]
    return [(cf, '[Connected]') if cf in item else item for item in lst]


###############################################################################
def print_kernel_list():
    ''' '''
    klst = kernel_list()
    print('---------------| List of available kernels |---------------')

    if not klst:
        print('                    No kernel available')
        print('               Use -n to create a new kernel')
    else:
        for item in klst:
            if item == klst[-1]:
                print(str(item[0]) + ' : ' + str(item[1]))
            else:
                print(str(item[0]) + ' : ' + str(item[1]) + '\n')
    print('-----------------------------------------------------------')


###############################################################################
def connect_kernel(cf):
    ''' Connect a kernel '''

    if is_runing(cf) is True:
        kc = BlockingKernelClient(connection_file=cf)
        kc.load_connection_file(cf)
        km = None

    else:
        # Kernel manager
        km = manager.KernelManager(connection_file=cf)
        km.start_kernel()
        # Kernel Client
        kc = km.blocking_client()

    # init communication
    kc.execute("import numpy as np", store_history=False)
    kc.execute("np.set_printoptions(threshold='nan')", store_history=False)

    return km, kc


###############################################################################
def shutdown_kernel(cf):
    ''' Shutdown a kernel based on its connection file '''
    km, kc = connect_kernel(cf)
    kc.shutdown()
