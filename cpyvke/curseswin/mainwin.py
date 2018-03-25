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
# Last Modified : dim. 25 mars 2018 23:52:40 CEST
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import curses
from time import sleep
import locale

from cpyvke.curseswin.kernelwin import KernelWin
from cpyvke.curseswin.explorerwin import ExplorerWin
from cpyvke.objects.panel import PanelWin
from cpyvke.utils.ascii import ascii_cpyvke

locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()


class MainWin(PanelWin):
    """ Main window. """

    def __init__(self, app, sock, logger):
        """ Main window constructor """

        super(MainWin, self).__init__(app, sock, logger)

        # Various Variables :
        self.search = None
        self.filter = None
        self.search_index = 0
        self.mk_sort = 'name'
        self.variables = {}
        self.panel_name = 'main'

        # Init Variable Box
        self.gwin = curses.newwin(self.app.panel_height, self.app.screen_width, 0, 0)
        self.gwin.bkgd(self.app.c_exp_txt)

        # Add explorer and kernel panels to self.app !
        self.app.explorer_win = ExplorerWin(self.app, self.sock, self.logger)
        self.app.kernel_win = KernelWin(self.app, self.sock, self.logger)
        self.app.test_win = PanelWin(self.app, self.sock, self.logger)

    def display(self):
        """ Run app ! """

        try:
            self.pkey = -1
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

            # Check switch panel
            if self.app.explorer_switch:
                self.app.explorer_switch = False
                self.app.kernel_win.display()
                self.resize_curses(True)

            elif self.app.kernel_switch:
                self.app.kernel_switch = False
                self.app.explorer_win.display()
                self.resize_curses(True)

            else:
                self.tasks()

    def fill_main_box(self):
        """ Welcome message """

        msg = ascii_cpyvke()
        msg_size = max([len(i) for i in msg])

        for i in range(len(msg)):
            self.gwin.addstr(i+1,
                             int((self.app.screen_width - msg_size)/2),
                             msg[i], self.app.c_warn_txt | curses.A_BOLD)

        tmp = "Type   {:25} {:30}"
        self.gwin.addstr(i+3, 1, tmp.format(':help<Enter> or ?',
                                            'for help').center(self.app.screen_width-4))
        self.gwin.addstr(i+4, 1, tmp.format(':q<Enter> or q',
                                            'to exit').center(self.app.screen_width-4))
        self.gwin.addstr(i+5, 1, tmp.format(':Q<Enter> or q',
                                            'to exit and shutdown daemon').center(self.app.screen_width-4))

    def tasks(self):
        """ Tasks to update curses """

        # Check Connection to daemon
        self.sock.check_main_socket()

        # Keys
        self.common_key_bindings()

        # Close menu
        if self.pkey in self.app.kquit:
            self.app.close_menu()

        # Skip end of tasks if switching panel !
        if not self.app.explorer_switch and not self.app.kernel_switch and self.app.close_signal == "continue":

            # Update screen size if another menu break because of resizing
            self.resize_curses()

            # Update all static panels
            self.refresh()

        # Get pressed key (even in case of switch)
        self.pkey = self.app.stdscr.getch()

    def list_key_bindings(self):
        """ Overload this method with nothing ! """

        pass

    def custom_key_bindings(self):
        """ Custom Key Actions ! """

        # Kernel Panel
        if self.pkey == 75:    # -> K
            self.app.kernel_win.display()
            self.resize_curses(True)  # Fix brutal resize crash
            if self.app.kernel_change:
                self.app.cf, self.app.kc = self.app.kernel_win.update_connection()

        # Explorer panel
        elif self.pkey in [9, 69]:    # -> TAB/E
            self.app.explorer_win.display()
            self.resize_curses(True)  # Fix brutal resize crash

        # Test panel
        elif self.pkey == 84:    # -> T
            self.app.test_win.display()
            self.resize_curses(True)  # Fix brutal resize crash
