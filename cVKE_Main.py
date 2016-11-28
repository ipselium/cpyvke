#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : cVKE_Main.py
# Creation Date : Fri Nov  4 21:49:15 2016
# Last Modified : lun. 28 nov. 2016 16:02:00 CET
# Created By : Cyril Desjouy
#
# Copyright © 2016-2017 Cyril Desjouy <cyril.desjouy@free.fr>
# Distributed under terms of the BSD license.
"""

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
###############################################################################
# Personal Libs
###############################################################################
from kd5 import Watcher
from CUIMainWin import CUI
from ktools import connect_kernel, print_kernel_list
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

if args.only_daemon:
    ONLY_DAEMON = True
else:
    ONLY_DAEMON = False

if args.only_cui:
    ONLY_CUI = True
else:
    ONLY_CUI = False

if args.debug:
    DEBUG = True
else:
    DEBUG = False
###############################################################################
###############################################################################
###############################################################################
###############################################################################

if __name__ == "__main__":

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
            from KernelTools import start_new_kernel
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
            if ONLY_CUI is not True:
                thread1 = Watcher(kc, args.refresh_delay, qstop, qvar, qreq, qans, qkc, ONLY_DAEMON)
            if ONLY_DAEMON is not True:
                thread2 = CUI(kc, cf, qstop, qvar, qreq, qans, qkc, DEBUG)

            # Start them
            if ONLY_CUI is not True:
                thread1.start()
            if ONLY_DAEMON is not True:
                thread2.start()

            # Waiting the thread terminate
            if ONLY_CUI is not True:
                thread1.join()
            if ONLY_DAEMON is not True:
                thread2.join()
