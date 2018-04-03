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
# Last Modified : mar. 03 avril 2018 21:15:01 CEST
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""


import curses
from curses import panel
from time import sleep
import locale

from cpyvke.utils.display import dump, str_reduce, str_format
from cpyvke.objects.pad import PadWin

locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()


class Viewer(PadWin):
    """ Display variable content in a pad. """

    def __init__(self, app, varval, varname):
        super(Viewer, self).__init__(app)
        self.varval = varval
        self.varname = varname

    def color(self, item):
        if item == 'txt':
            return self.app.c_exp_txt
        elif item == 'bdr':
            return self.app.c_exp_bdr | curses.A_BOLD
        elif item == 'ttl':
            return self.app.c_exp_ttl | curses.A_BOLD
        elif item == 'pwf':
            return self.app.c_exp_pwf | curses.A_BOLD

    @property
    def title(self):
        return ' ' + self.varname + ' '

    @property
    def content(self):
        if type(self.varval) is str:
            dumped = str_format(self.varval, self.app.screen_width-6)
        else:
            dumped = dump(self.varval)

        return dumped


class WarningMsg:
    """ Display a message. """

    def __init__(self, app):

        self.app = app

    def display(self, wng_msg):
        """ Display **wng_msg** in a panel. """

        # Init Menu
        wng_msg = str_reduce(wng_msg, self.app.screen_width - 2)
        wng_width = len(wng_msg) + 2
        menu_wng = self.app.stdscr.subwin(3, wng_width, 3, int((self.app.screen_width-wng_width)/2))
        menu_wng.bkgd(self.app.c_warn_txt | curses.A_BOLD)
        menu_wng.attrset(self.app.c_warn_bdr | curses.A_BOLD)    # change border color
        menu_wng.border(0)
        menu_wng.keypad(1)

        # Send menu to a panel
        panel_wng = panel.new_panel(menu_wng)
        panel_wng.top()        # Push the panel to the bottom of the stack.

        menu_wng.addstr(1, 1, wng_msg, self.app.c_warn_txt)
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

    def color(self, item):
        if item == 'txt':
            return self.app.c_main_txt
        elif item == 'bdr':
            return self.app.c_main_bdr | curses.A_BOLD
        elif item == 'ttl':
            return self.app.c_main_ttl | curses.A_BOLD
        elif item == 'pwf':
            return self.app.c_main_pwf | curses.A_BOLD

    @property
    def title(self):
        return ' Help '

    @property
    def content(self):
        return ['',
                '(?) This Help !',
                '(ENTER) Selected item menu',
                '(q|ESC) Previous menu',
                '(:) Prompt access',
                '(/) Search a pattern',
                '(n) Next occurence of pattern',
                '(s) Sort by name/type',
                '(f) filter',
                '(x) Execute code in current IPython kernel',
                '(u) Undo limit',
                '(r) Refresh explorer',
                '(E) Variable Explorer',
                '(K) Kernel Manager',
                '(TAB) Kernel <-> Variable',
                '(c-r) Restart daemon',
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
