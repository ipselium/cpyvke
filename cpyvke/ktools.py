#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : KernelTools.py
# Creation Date : Fri Nov  4 21:49:15 2016
# Last Modified : mar. 27 févr. 2018 12:08:56 CET
# Created By : Cyril Desjouy
#
# Copyright © 2016-2017 Cyril Desjouy <ipselium@free.fr>
# Distributed under terms of the BSD license.
"""

DESCRIPTION

@author: Cyril Desjouy
"""


from jupyter_client import BlockingKernelClient, manager
from time import sleep
import os
import subprocess
import psutil
import logging

logger = logging.getLogger("cpyvke.ktools")


def ProcInfo(init=0):
    pid = os.getpid()
    py = psutil.Process(pid)
    mem = py.memory_percent()  # py.memory_info()[0]/2.**30
    if init != mem:
        print('Memory :', mem)  # memory use in GB...I think
    return mem


def start_new_kernel(LogDir=os.path.expanduser("~") + "/.cpyvke/"):
    ''' Start a new kernel and return the kernel_id '''

    with open(LogDir + 'LastKernel', "w") as f:
        subprocess.Popen(["ipython", "kernel"], stdout=f)

    sleep(1)
    with open(LogDir + 'LastKernel', "r") as f:
        stdout = f.read()

    logger.info('Create :: %s', stdout.split('\n')[-2])

    return stdout.split('kernel-')[1].split('.json')[0]


def is_runing(cf):
    ''' Check if kernel is alive. '''

    kc = BlockingKernelClient()
    kc.load_connection_file(cf)
    port = kc.get_connection_info()['iopub_port']

    if check_server(port):
        return True
    else:
        return False


def check_server(port):
    ''' Check if a service is listening on port. '''

    addr = [item.laddr for item in psutil.net_connections('inet') if str(port) in str(item.laddr[1])]
    if addr:
        return True
    else:
        return False


def kernel_list(cf=None):
    ''' List of connection files. '''

    path = '/run/user/1000/jupyter/'
    lstk = [path + item for item in os.listdir(path) if 'kernel' in item]

    try:
        lst = [(item, '[Alive]' if is_runing(item) else '[Died]') for item in lstk]
    except:
        logger.info('No kernel available')
        return []
    else:
        return [(cf, '[Connected]') if cf in item else item for item in lst]


def print_kernel_list():
    ''' Display kernel list. '''
    klst = kernel_list()
    print('---------------| List of available kernels |---------------')

    if not klst:
        print('                    No kernel available')
        print('Last run of the daemon may have quit prematurely.')
    else:
        for item in klst:
            if item == klst[-1]:
                print(str(item[0]) + ' : ' + str(item[1]))
            else:
                print(str(item[0]) + ' : ' + str(item[1]) + '\n')
    print('-----------------------------------------------------------')


def connect_kernel(cf):
    ''' Connect a kernel. '''

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

    init_kernel(kc)

    return km, kc


def init_kernel(kc):
    ''' init communication. '''

    kc.execute("import numpy as np", store_history=False)
    kc.execute("np.set_printoptions(threshold='nan')", store_history=False)
    kc.execute("import json", store_history=False)


def shutdown_kernel(cf):
    ''' Shutdown a kernel based on its connection file. '''

    km, kc = connect_kernel(cf)
    kc.shutdown()
