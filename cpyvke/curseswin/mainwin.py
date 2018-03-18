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
# Creation Date : Wed Nov 9 10:03:04 2016
# Last Modified : dim. 18 mars 2018 00:55:04 CET
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import curses
from math import ceil
from time import sleep
import locale

from cpyvke.curseswin.kernelwin import KernelWin
from cpyvke.curseswin.explorerwin import ExplorerWin
from cpyvke.curseswin.widgets import WarningMsg, Help
from cpyvke.utils.kernel import restart_daemon
from cpyvke.utils.ascii import ascii_cpyvke

locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()


class MainWin:
    """ Main window. """

    def __init__(self, app, sock, logger):
        """ Main window constructor """

        self.app = app
        self.sock = sock
        self.logger = logger

        # Various Variables :
        self.search = None
        self.filter = None
        self.search_index = 0

        self.mk_sort = 'name'
        self.variables = {}

        # Init Variable Box
        self.row_max = self.app.screen_height-self.app.debug_info
        self.mwin = curses.newwin(self.row_max+2, self.app.screen_width-2, 1, 1)
        self.mwin.bkgd(self.app.c_exp_txt)
        self.mwin.attrset(self.app.c_exp_bdr | curses.A_BOLD)  # border color

        # Add explorer and kernel panels to self.app !
        self.app.explorer_win = ExplorerWin(self.app, self.sock, self.logger)
        self.app.kernel_win = KernelWin(self.app, self.sock.RequestSock)

    def run(self):
        """ Run daemon """

        try:
            self.pkey = -1    # Init pressed Key
            while self.app.close_signal == 'continue':
                self.update_curses()
            self.app.shutdown()
        except Exception:
            self.app.exit_with_error()

    def update_curses(self):
        """ Update Curses """

        # Listen to resize and adapt Curses
        self.resize_curses()

        # Check if size is enough
        if self.app.screen_height < self.app.term_min_height or self.app.screen_width < self.app.term_min_width:
            self.app.check_size()
            sleep(0.5)
        else:
            self.tasks()

    def resize_curses(self):
        """ Check if terminal is resized and adapt screen """

        resize = curses.is_term_resized(self.app.screen_height, self.app.screen_width)
        if resize is True and self.app.screen_height >= self.app.term_min_height and self.app.screen_width >= self.app.term_min_width:
            self.app.screen_height, self.app.screen_width = self.app.stdscr.getmaxyx()  # new heigh and width of object stdscreen
            self.row_max = self.app.screen_height-self.app.debug_info
            self.app.stdscr.clear()
            self.mwin.clear()
            self.mwin.resize(self.row_max+2, self.app.screen_width-2)
            curses.resizeterm(self.app.screen_height, self.app.screen_width)
            self.app.stdscr.refresh()
            self.mwin.refresh()

    def update_static(self):
        """ Update all static windows. """

        # Erase all windows
        self.mwin.erase()
        self.app.stdscr.erase()

        # Create border before updating fields
        self.app.stdscr.border(0)
        self.mwin.border(0)

        # Update all windows (virtually)
        if self.app.DEBUG:
            self.app.dbg_socket()         # Display infos about the process
            self.app.dbg_term()         # Display infos about the process
            self.app.dbg_general(self.pkey, self.search, self.filter, self.mk_sort)        # Display debug infos

        # Welcome screen
        self.welcome()

        # Update display  -- Bottom : Display infos about kernel at bottom
        self.app.bottom_bar_info(len(self.variables))
        self.app.stdscr.refresh()
        self.mwin.refresh()

    def welcome(self):
        """ """

        msg = ascii_cpyvke()
        msg_size = max([len(i) for i in msg])

        for i in range(len(ascii_cpyvke())):
            self.mwin.addstr(i+1,
                             int((self.app.screen_width - msg_size)/2),
                             msg[i], self.app.c_main_txt | curses.A_BOLD)

        self.mwin.addstr(i+3, 1,
                         'E : Variable Inspector'.center(self.app.screen_width-4))
        self.mwin.addstr(i+4, 1,
                         'K : Kernel Manager'.center(self.app.screen_width-4))

    def tasks(self):
        """ Tasks to update curses """

        # Check switch panel
        if self.app.explorer_win.switch:
            self.app.explorer_win.switch = False
            self.app.kernel_win.display()
            self.app.cf, self.app.kc = self.app.kernel_win.update_connection()

        if self.app.kernel_win.switch:
            self.app.kernel_win.switch = False
            self.app.explorer_win.display()

        # Check Connection to daemon
        self.sock.check_main_socket()

        # Keys
        self.key_bindings()

        # Update screen size if another menu break because of resizing
        self.resize_curses()

        # Update all static panels
        self.update_static()

        # Get pressed key
        self.pkey = self.app.stdscr.getch()

        # Close menu
        if self.pkey in self.app.kquit:
            self.app.close_menu()

    def key_bindings(self):
        """ Key Actions ! """

        # Init Warning Msg
        WngMsg = WarningMsg(self.app.stdscr)

        # Menu Variable
        # Menu Help
        if self.pkey == 63:    # -> ?
            help_menu = Help(self.app)
            help_menu.display()

        # Kernel Panel
        elif self.pkey == 75:    # -> K
            self.app.kernel_win.display()
            self.app.cf, self.app.kc = self.app.kernel_win.update_connection()
            # Reset cursor location
            self.position = 1
            self.page = int(ceil(self.position/self.row_max))

        # Explorer panel
        elif self.pkey == 69:    # -> E
            self.app.explorer_win.display()
            # Reset cursor location
            self.position = 1
            self.page = int(ceil(self.position/self.row_max))

        # Reconnection to socket
        elif self.pkey == 82:    # -> R
            WngMsg.Display(' Restarting connection ')
            self.sock.restart_sockets()
            self.sock.warning_socket(WngMsg)

        # Disconnect from daemon
        elif self.pkey == 68:    # -> D
            self.sock.close_sockets()
            self.sock.warning_socket(WngMsg)

        # Connect to daemon
        elif self.pkey == 67:     # -> C
            self.sock.init_sockets()
            self.sock.warning_socket(WngMsg)

        # Restart daemon
        elif self.pkey == 18:    # -> c-r
            restart_daemon()
            WngMsg.Display(' Restarting Daemon ')
            self.sock.init_sockets()
            self.sock.warning_socket(WngMsg)

        # Force Update Variable List sending fake code to daemon
        elif self.pkey == 114:   # -> r
            self.sock.force_update(WngMsg)
