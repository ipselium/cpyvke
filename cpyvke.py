#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : cVKE_Main.py
# Creation Date : Fri Nov  4 21:49:15 2016
# Last Modified : lun. 05 déc. 2016 12:48:30 CET
# Created By : Cyril Desjouy
#
# Copyright © 2016-2017 Cyril Desjouy <cyril.desjouy@free.fr>
# Distributed under terms of the BSD license.
"""
Tested with ipython 5

To upgrade :
    pip install ipython --update
To downgrade:
    pip install ipython==2.4.1

@author: Cyril Desjouy
"""


###############################################################################
# IMPORTS
###############################################################################
import argparse
from jupyter_client import find_connection_file
from Queue import Queue
# Personal Libs
from kd5 import Watcher
from cmain import CUI
from ktools import connect_kernel, print_kernel_list
from config import cfg_setup


###############################################################################
# PARSE CONFIG
###############################################################################

cfg = cfg_setup()
Config = cfg.RunCfg()

###############################################################################
# PARSE ARGUMENTS
###############################################################################
kernel_id = None

parser = argparse.ArgumentParser()
parser.add_argument("-n", "--new", help="Start up with a new kernel", action="store_true")
parser.add_argument("-e", "--existing", help="Start up with existing kernel. EXISTING is the id of the connection file")
parser.add_argument("-d", "--only_daemon", help="Only start up daemon", action="store_true")
parser.add_argument("-D", "--debug", help="Debug mode", action="store_true")
parser.add_argument("-c", "--only_cui", help="Only start up curse user interface", action="store_true")
parser.add_argument("-l", "--list_kernels", help="Only list kernels", action="store_true")
parser.add_argument("-r", "--refresh_delay", help="Refresh delay of the daemon [in s]", nargs='?', const=1., type=float, default=1.)
args = parser.parse_args()

if args.only_cui and args.only_daemon:
    print('Error :\tCannot run only daemon AND only CUI !\n\tExiting...')

elif args.list_kernels:
        print_kernel_list()

elif args.new and args.existing:
    print('Error :\tIncompatible options -n and -e ! \
                    \n\tCreate or use an existing kernel !\n')
    print_kernel_list()
    print('\nExiting...')

elif args.new is False and args.existing is None:
    print('Error :\tNo kernel provided !\n\tNeed argument -n or -e\n')
    print_kernel_list()
    print('\nExiting...')

else:
    # Kernel provided by user ?
    if args.existing:
        kernel_id = args.existing

    elif args.new:
        print('Creating new kernel...')
        from ktools import start_new_kernel
        kernel_id = start_new_kernel()

    # Kernel's connection file
    try:
        cf = find_connection_file(kernel_id)

    except:
        print('Error :\tCannot find kernel !\n\tExiting')
        pass

    else:
        # Init kernel
        km, kc = connect_kernel(cf)

        # Init Queues
        qstop = Queue()  # Stop event
        qvar = Queue()  # Queue of all Kernel variables
        qreq = Queue()  # Request value of a single variable
        qans = Queue()  # Send Valule of a single variable
        qkc = Queue()  # Kernel changes

        # Create threads
        thread1 = Watcher(kc, args.refresh_delay, qstop, qvar, qreq, qans, qkc, args.only_daemon)
        if args.only_daemon is False:
            thread2 = CUI(kc, cf, qstop, qvar, qreq, qans, qkc, Config, args.debug)

        # Start them
        thread1.start()
        if args.only_daemon is False:
            thread2.start()

        # Waiting the thread terminate
        thread1.join()
        if args.only_daemon is False:
            thread2.join()
