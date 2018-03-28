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
# Last Modified : mer. 28 mars 2018 16:23:48 CEST
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import os
import sys
import locale
import logging
import argparse
import time
from jupyter_client import find_connection_file
from logging.handlers import RotatingFileHandler

from cpyvke.curseswin.app import InitApp
from cpyvke.curseswin.mainwin import MainWin
from cpyvke.utils.config import cfg_setup
from cpyvke.utils.kernel import connect_kernel, print_kernel_list
from cpyvke.utils.sockets import SocketManager
from cpyvke.utils.term_colors import RED, RESET

locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()


def init_cf(lockfile):
    """ Init connection file. """

    with open(lockfile, 'r') as f:
        kernel_id = f.readline()

    return find_connection_file(kernel_id)


def with_daemon(lockfile, pidfile, cmd):
    """ Launch daemon. """

    os.system(cmd)

    while os.path.exists(pidfile) is False:
        time.sleep(0.1)

    return init_cf(lockfile)


def parse_args(lockfile, pidfile, lastfile):
    """ Parse Arguments. """

    parser = argparse.ArgumentParser()
    parser.add_argument("-D", "--debug", help="Debug mode", action="store_true")
    parser.add_argument("-L", "--list", help="List all kernels",
                        action="store_true")
    parser.add_argument("integer", help="Start up with existing kernel. \
                        INTEGER is the id of the connection file. \
                        INTEGER can also be the keyword 'last' for 'last kernel'",
                        nargs='?')

    args = parser.parse_args()

    if args.list:
        print_kernel_list()
        sys.exit(0)

    elif os.path.exists(lockfile) and os.path.exists(pidfile):
        cf = init_cf(lockfile)
        if args.integer:
            message = 'Daemon is already running. Dropping argument {}\n'
            sys.stderr.write(message.format(args.integer))
            time.sleep(2)

    elif args.integer:
        if args.integer == 'last':
            cmd = 'kd5 last'
        else:
            try:
                find_connection_file(str(args.integer))
            except OSError:
                message = '{}Error :{}\tCannot find kernel id. {} !\n\tExiting\n'
                sys.stderr.write(message.format(RED, RESET, args.integer))
                sys.exit(1)
            else:
                cmd = 'kd5 start ' + str(args.integer)
        cf = with_daemon(lockfile, pidfile, cmd)
    else:
        cmd = 'kd5 start'
        cf = with_daemon(lockfile, pidfile, cmd)

    return args, cf


def main(args=None):
    """ Launch cpyvke. """

    # Parse Config
    cfg = cfg_setup()
    config = cfg.run()

    # Define Paths
    logdir = os.path.expanduser('~') + '/.cpyvke/'
    lockfile = logdir + 'kd5.lock'
    pidfile = logdir + 'kd5.pid'
    logfile = logdir + 'cpyvke.log'
    lastfile = logdir + 'kd5.last'

    # Logger
    logger = logging.getLogger("cpyvke")
    logger.setLevel(logging.DEBUG)

    # create the logging file handler
    handler = RotatingFileHandler(logfile, maxBytes=10*1024*1024,
                                  backupCount=5)
    logmsg = '%(asctime)s :: %(name)s :: %(threadName)s :: %(levelname)s :: %(message)s'
    formatter = logging.Formatter(logmsg, datefmt='%Y-%m-%d - %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Parse arguments
    args, cf = parse_args(lockfile, pidfile, lastfile)

    # Init kernel
    km, kc = connect_kernel(cf)

    # Init Curses App
    sock = SocketManager(config, logger)
    app = InitApp(kc, cf, config, sock, args.debug)
    # Run App
    logger.info('cpyvke started')
    main_curse = MainWin(app, sock, logger)
    main_curse.display()


if __name__ == "__main__":
    main()
