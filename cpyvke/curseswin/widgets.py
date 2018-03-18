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
# Creation Date : Wed Nov 9 16:29:28 2016
# Last Modified : sam. 17 mars 2018 11:47:43 CET
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""


import curses
from curses import panel
from time import sleep
import locale

from cpyvke.utils.display import dump, str_reduce
from cpyvke.objects.pad import PadWin

locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()


class Viewer(PadWin):
    """ Display variable content in a pad. """

    def __init__(self, app, varval, varname):
        """ Class constructor """

        self.varval = varval
        self.varname = varname

        super(Viewer, self).__init__(app)

        # Init Values
        self.c_txt = self.app.c_exp_txt
        self.c_bdr = self.app.c_exp_bdr
        self.c_ttl = self.app.c_exp_ttl
        self.c_hh = self.app.c_exp_hh
        self.c_pwf = self.app.c_exp_pwf

        # Init Menu
        self.title = ' ' + self.varname + ' '
        self.content = self.create_content()

    def create_content(self):
        """ Create content of the pad """

        # Format variable
        if type(self.varval) is str:
            dumped = self.varval.split('\n')
        else:
            dumped = dump(self.varval)

        return dumped


class WarningMsg:
    """ Display a message. """

    def __init__(self, stdscreen):

        self.stdscreen = stdscreen
        self.screen_height, self.screen_width = self.stdscreen.getmaxyx()

        # Define Styles
        self.c_warn_txt = curses.color_pair(1)
        self.c_warn_bdr = curses.color_pair(2)

    def Display(self, wng_msg):
        """ Display **wng_msg** in a panel. """

        # Init Menu
        wng_msg = str_reduce(wng_msg, self.screen_width - 2)
        wng_width = len(wng_msg) + 2
        menu_wng = self.stdscreen.subwin(3, wng_width, 3, int((self.screen_width-wng_width)/2))
        menu_wng.bkgd(self.c_warn_txt | curses.A_BOLD)
        menu_wng.attrset(self.c_warn_bdr | curses.A_BOLD)    # change border color
        menu_wng.border(0)
        menu_wng.keypad(1)

        # Send menu to a panel
        panel_wng = panel.new_panel(menu_wng)
        panel_wng.top()        # Push the panel to the bottom of the stack.

        menu_wng.addstr(1, 1, wng_msg, self.c_warn_txt)
        panel_wng.show()       # Display the panel (which might have been hidden)
        menu_wng.refresh()
        sleep(1)

        # Erase the panel
        menu_wng.clear()
        panel_wng.hide()


class Help(PadWin):
    """ Display help in a pad. """

    def __init__(self, app):

        super(Help, self).__init__(app)

        # Init Values
        self.c_txt = self.app.c_main_txt
        self.c_bdr = self.app.c_main_bdr
        self.c_ttl = self.app.c_main_ttl
        self.c_pwf = self.app.c_main_pwf

        # Init Menu
        self.title = 'Help'
        self.content = self.create_content()

    def create_content(self):
        """ Create content """

        return ['',
                '(?) This Help !',
                '(ENTER) Selected item menu',
                '(q|ESC) Previous menu/quit',
                '(/) Search in variable explorer',
                '(s) Sort by name/type',
                '(L) Limit display to keyword',
                '(u) Undo limit',
                '(r) Refresh explorer',
                '(K) Kernel Menu',
                '(c-r) Restart Daemon',
                '(R) Restart connection to daemon',
                '(D) Disconnect from daemon',
                '(C) Connect to daemon',
                '(↓|j) Next line',
                '(↑|k) Previous line',
                '(→|↡|l) Next page',
                '(←|↟|h) Previous page',
                '']


class suspend_curses:
    """Context Manager to temporarily leave curses mode"""

    def __enter__(self):
        curses.endwin()

    def __exit__(self, exc_type, exc_val, tb):
        stdscreen = curses.initscr()
        stdscreen.refresh()
        curses.doupdate()
