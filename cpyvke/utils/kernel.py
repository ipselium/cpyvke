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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with cpyvke. If not, see <http://www.gnu.org/licenses/>.
#
#
# Creation Date : Fri Nov 4 21:49:15 2016
# Last Modified : mar. 13 mars 2018 14:02:48 CET
"""
-----------
DOCSTRING

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


def start_new_kernel(LogDir=os.path.expanduser("~") + "/.cpyvke/", version=3):
    """ Start a new kernel and return the kernel_id """

    with open(LogDir + 'LastKernel', "w") as f:
        if version == '2':
            subprocess.Popen(["ipython", "kernel"], stdout=f)
        else:
            subprocess.Popen(["ipython3", "kernel"], stdout=f)

    sleep(1)
    with open(LogDir + 'LastKernel', "r") as f:
        stdout = f.read()

    logger.info('Create :: %s', stdout.split('\n')[-2])

    return stdout.split('kernel-')[1].split('.json')[0]


def is_runing(cf):
    """ Check if kernel is alive. """

    kc = BlockingKernelClient()
    kc.load_connection_file(cf)
    port = kc.get_connection_info()['iopub_port']

    if check_server(port):
        return True
    else:
        return False


def check_server(port):
    """ Check if a service is listening on port. """

    addr = [item.laddr for item in psutil.net_connections('inet') if str(port) in str(item.laddr[1])]
    if addr:
        return True
    else:
        return False


def kernel_list(cf=None):
    """ List of connection files. """

    path = '/run/user/1000/jupyter/'
    lstk = [path + item for item in os.listdir(path) if 'kernel' in item]

    try:
        lst = [(item, '[Alive]' if is_runing(item) else '[Died]') for item in lstk]
    except Exception:
        logger.error('No kernel available', exc_info=True)
        return []
    else:
        return [(cf, '[Connected]') if cf in item else item for item in lst]


def print_kernel_list():
    """ Display kernel list. """
    klst = kernel_list()
    print('{:-^79}'.format('| List of available kernels |'))

    if not klst:
        print('{:^79}'.format('No kernel available'))
        print('{:^79}'.format('Last run of the daemon may have quit prematurely.'))
    else:
        for item in klst:
            if item == klst[-1]:
                print('{0[0]:71}{0[1]:>8}'.format(item))
            else:
                print('{0[0]:71}{0[1]:>8}\n'.format(item))
    print(79*'-')


def connect_kernel(cf):
    """ Connect a kernel. """

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


def connect_kernel_as_manager(cf):
    # Kernel manager
    km = manager.KernelManager(connection_file=cf)
    km.start_kernel()
    # Kernel Client
    kc = km.blocking_client()
    init_kernel(kc)

    return km, kc


def init_kernel(kc, backend='tk'):
    """ init communication. """

    backend = 'tk'

    kc.execute("import numpy as _np", store_history=False)
    kc.execute("_np.set_printoptions(threshold='nan')", store_history=False)
    kc.execute("import json as _json", store_history=False)
    kc.execute("%matplotlib {}".format(backend), store_history=False)
    kc.execute("import cpyvke.utils.inspector as _inspect", store_history=False)


def restart_daemon():
    with open(os.devnull, 'w') as f:
        subprocess.Popen(["kd5", "restart"], stdout=f)


def shutdown_kernel(cf):
    """ Shutdown a kernel based on its connection file. """

    km, kc = connect_kernel_as_manager(cf)
    km.shutdown_kernel(now=True)
