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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with cpyvke.  If not, see <http://www.gnu.org/licenses/>.
#
#
# Creation Date : Wed Nov  9 10:03:04 2016
# Last Modified : sam. 10 mars 2018 20:05:18 CET
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import argparse
from time import sleep
from jupyter_client import find_connection_file
import sys
import os
import logging
from logging.handlers import RotatingFileHandler
import locale

from .cmain import MainWin
from .ktools import connect_kernel, print_kernel_list
from .config import cfg_setup

locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()
logger = logging.getLogger("cpyvke")


def InitCf(lockfile, pidfile):
    """ Init connection file. """

    with open(lockfile, 'r') as f:
        kernel_id = f.readline()

    return find_connection_file(kernel_id)


def WithDaemon(lockfile, pidfile, cmd):
    """ Launch daemon. """

    os.system(cmd)

    while os.path.exists(pidfile) is False:
        sleep(0.1)

    return InitCf(lockfile, pidfile)


def ParseArgs(lockfile, pidfile):
    """ Parse Arguments. """

    parser = argparse.ArgumentParser()
    parser.add_argument("-D", "--debug", help="Debug mode", action="store_true")
    parser.add_argument("-L", "--list", help="List all kernels",
                        action="store_true")
    parser.add_argument("integer", help="Start up with existing kernel. \
                        INTEGER is the id of the connection file.",
                        nargs='?')

    args = parser.parse_args()

    if args.list:
        print_kernel_list()
        sys.exit(2)

    elif os.path.exists(lockfile) and os.path.exists(pidfile):

        try:
            cf = InitCf(lockfile, pidfile)
        except FileNotFoundError:
            missing(lockfile, pidfile)
            sys.exit(2)

    elif args.integer:

        try:
            find_connection_file(str(args.integer))
        except FileNotFoundError:
            message = 'Error :\tCannot find kernel id. {} !\n\tExiting\n'
            sys.stderr.write(message.format(args.integer))
            sys.exit(2)

        cmd = 'kd5 start ' + str(args.integer)
        cf = WithDaemon(lockfile, pidfile, cmd)

    else:

        cmd = 'kd5 start'
        cf = WithDaemon(lockfile, pidfile, cmd)

    return args, cf


def missing(lockfile, pidfile):
    """ Fix missing connection file. """

    print('An old lock file already exists, but the kernel connection file is missing.')
    print('As this issue is not fixed, cpyvke cannot run.')
    rm_lock = input('Remove the old lock file ? [y|n] : ')

    if rm_lock == 'y':
        os.remove(lockfile)
        os.remove(pidfile)
        print('You can now restart cpyvke.')
    elif rm_lock == 'n':
        print('Exiting...')
    else:
        print('Wrong choice. exiting... ')


def main(args=None):
    """ Launch cpyvke. """

    # Parse Config
    cfg = cfg_setup()
    Config = cfg.RunCfg()

    # Define Paths
    logdir = os.path.expanduser('~') + '/.cpyvke/'
    lockfile = logdir + 'kd5.lock'
    pidfile = logdir + 'kd5.pid'
    logfile = logdir + 'cpyvke.log'

    # Logger
    logger.setLevel(logging.DEBUG)

    # create the logging file handler
    handler = RotatingFileHandler(logfile, maxBytes=10*1024*1024,
                                  backupCount=5)
    logmsg = '%(asctime)s :: %(name)s :: %(threadName)s :: %(levelname)s :: %(message)s'
    formatter = logging.Formatter(logmsg, datefmt='%Y-%m-%d - %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Parse arguments
    args, cf = ParseArgs(lockfile, pidfile)

    # Init kernel
    km, kc = connect_kernel(cf)

    # Run App
    logger.info('cpyvke started')
    App = MainWin(kc, cf, Config, args.debug)
    App.run()


if __name__ == "__main__":
    main()
