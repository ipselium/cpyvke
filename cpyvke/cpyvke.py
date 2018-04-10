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
# Last Modified : mar. 10 avril 2018 20:54:45 CEST
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

from .curseswin.app import InitApp
from .curseswin.mainwin import MainWin
from .utils.config import cfg_setup
from .utils.kernel import connect_kernel, print_kernel_list
from .utils.kd import kd_status
from .utils.sockets import SocketManager
from .utils.term_colors import RED, RESET

locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()


def init_cf(lockfile):
    """ Init connection file. """

    with open(lockfile, 'r') as f:
        kid = f.readline()

    return find_connection_file(kid)


def with_daemon(lockfile, pidfile, cmd):
    """ Launch daemon. """

    os.system(cmd)

    while os.path.exists(pidfile) is False:
        time.sleep(0.1)

    return init_cf(lockfile)


def no_lock_exit():
    """ If no kd5.lock ! """

    message = '{}Error :{}\tCannot find kd5.lock !\n\tFixing issues shutting down kd5...\n'
    sys.stderr.write(message.format(RED, RESET))
    os.system('kd5 stop')
    sys.stderr.write("You can now restart cpyvke!\n")
    sys.exit(1)


def parse_args(lockfile, pidfile):
    """ Parse Arguments. """

    parser = argparse.ArgumentParser()
    parser.add_argument("-L", "--list", help="List all kernels",
                        action="store_true")
    parser.add_argument("integer", help="Start up with existing kernel. \
                        INTEGER is the id of the connection file. \
                        INTEGER can also be the keyword 'last' for 'last kernel'",
                        nargs='?')

    args = parser.parse_args()

    pid = kd_status(pidfile)

    if args.list:
        print_kernel_list()
        sys.exit(0)

    elif os.path.exists(lockfile) and pid:
        try:
            cf = init_cf(lockfile)
        except OSError:
            sys.stderr.write('lockfile points to an unknown connection file.\n')
            sys.stderr.write("Try 'kd5 stop'\n")
            sys.exit(1)
        if args.integer:
            message = 'Daemon is already running. Dropping argument {}\n'
            sys.stderr.write(message.format(args.integer))
            time.sleep(1.5)

    elif not os.path.exists(lockfile) and pid:
        no_lock_exit()

    elif args.integer == 'last' and not os.path.exists(lockfile):
        no_lock_exit()

    elif args.integer == 'last' and os.path.exists(lockfile):
        cmd = 'kd5 last'
        cf = with_daemon(lockfile, pidfile, cmd)

    elif args.integer:
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
    args, cf = parse_args(lockfile, pidfile)

    # Init kernel
    km, kc = connect_kernel(cf)

    # Init Curses App
    sock = SocketManager(config, logger)
    app = InitApp(kc, cf, config, sock)
    # Run App
    logger.info('cpyvke started')
    main_curse = MainWin(app, sock, logger)
    main_curse.display()


if __name__ == "__main__":
    main()
