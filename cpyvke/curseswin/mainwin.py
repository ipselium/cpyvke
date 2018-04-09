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
# Last Modified : lun. 09 avril 2018 22:43:21 CEST
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import curses
import locale

from cpyvke.curseswin.kernelwin import KernelWin
from cpyvke.curseswin.explorerwin import ExplorerWin
from cpyvke.curseswin.widgets import WarningMsg
from cpyvke.objects.panel import BasePanel
from cpyvke.utils.ascii import ascii_cpyvke

locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()


class MainWin(BasePanel):
    """ Main window. """

    def __init__(self, app, sock, logger):
        """ Main window constructor """

        super(MainWin, self).__init__(app, sock, logger)

        # Add explorer, kernel panels and wng pad to self.app !
        self.app.explorer_win = ExplorerWin(self.app, self.sock, self.logger)
        self.app.kernel_win = KernelWin(self.app, self.sock, self.logger)
        self.app.wng = WarningMsg(self.app)

    @property
    def title(self):
        return ''

    @property
    def panel_name(self):
        return 'main'

    def color(self, item):
        if item == 'txt':
            return self.app.c_main_txt
        elif item == 'bdr':
            return self.app.c_main_bdr
        elif item == 'ttl':
            return self.app.c_main_ttl
        elif item == 'hh':
            return self.app.c_main_hh
        elif item == 'pwf':
            return self.app.c_main_pwf
        elif item == 'asc':
            return self.app.c_main_asc

    def fill_main_box(self):
        """ Welcome message """

        msg = ascii_cpyvke(self.app.config['font']['ascii-font'])
        msg_size = max([len(i) for i in msg])

        for i in range(len(msg)):
            self.gwin.addstr(i+1,
                             int((self.app.screen_width - msg_size)/2),
                             msg[i], self.color('asc') | curses.A_BOLD)

        tmp = "Type   {:25} {:30}"
        self.gwin.addstr(i+3, 1, tmp.format(':help<Enter> or ?',
                                            'for help').center(self.app.screen_width-4))
        self.gwin.addstr(i+4, 1, tmp.format(':q<Enter>',
                                            'to exit').center(self.app.screen_width-4))
        self.gwin.addstr(i+5, 1, tmp.format(':Q<Enter>',
                                            'to exit and shutdown daemon').center(self.app.screen_width-4))

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
