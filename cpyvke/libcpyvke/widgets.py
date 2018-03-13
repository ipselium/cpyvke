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
# Last Modified : mar. 13 mars 2018 12:51:51 CET
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""


import curses
from curses import panel
from time import sleep
import locale

from ..utils.display import dump


locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()


class Viewer:
    """ Display variable content in a pad. """

    def __init__(self, parent):

        # Init Values
        self.stdscreen = parent.stdscreen
        self.varval = parent.varval
        self.varname = parent.varname
        self.screen_height, self.screen_width = self.stdscreen.getmaxyx()
        self.menu_title = ' ' + self.varname + ' '
        self.Config = parent.Config
        self.c_exp_txt = parent.c_exp_txt
        self.c_exp_bdr = parent.c_exp_bdr
        self.c_exp_ttl = parent.c_exp_ttl
        self.c_exp_hh = parent.c_exp_hh
        self.c_exp_pwf = parent.c_exp_pwf

        # Format variable
        if type(self.varval) is str:
            dumped = self.varval.split('\n')
        else:
            dumped = dump(self.varval)

        # Init Menu
        self.pad_width = max(len(self.menu_title), max([len(elem) for elem in dumped])) + 8
        self.pad_height = len(dumped) + 2
        self.menu_viewer = curses.newpad(self.pad_height, self.pad_width)
        self.menu_viewer.keypad(1)
        self.menu_viewer.bkgd(self.c_exp_txt)
        self.menu_viewer.attrset(self.c_exp_bdr | curses.A_BOLD)
        self.menu_viewer.border(0)

        # Viewer content
        for i in range(len(dumped)):
            self.menu_viewer.addstr(1+i, 1, dumped[i].encode(code), self.c_exp_txt)

        # Viewer title
        if self.Config['font']['pw-font'] == 'True':
            self.menu_viewer.addstr(0, int((self.pad_width - len(self.menu_title) - 2)/2),
                                    '', self.c_exp_pwf | curses.A_BOLD)
            self.menu_viewer.addstr(self.menu_title, self.c_exp_ttl | curses.A_BOLD)
            self.menu_viewer.addstr('', self.c_exp_pwf | curses.A_BOLD)
        else:
            self.menu_viewer.addstr(0, int((self.pad_width - len(self.menu_title) - 2)/2),
                                    '|' + self.menu_title + '|', self.c_exp_ttl | curses.A_BOLD)

    def Display(self):
        """ Create pad to display variable content. """

        menukey = -1
        padpos = 0
        pady = max(self.pad_height, self.screen_height - 2) - (self.screen_height - 2)

        while menukey not in (27, 113):
            if menukey == curses.KEY_DOWN:
                padpos = min(pady, padpos+1)
            elif menukey == curses.KEY_UP:
                padpos = max(0, padpos-1)
            elif menukey == curses.KEY_RIGHT:
                padpos = min(pady, padpos+5)
            elif menukey == curses.KEY_LEFT:
                padpos = max(0, padpos-5)
            elif menukey == curses.KEY_NPAGE:
                padpos = min(pady, padpos+10)
            elif menukey == curses.KEY_PPAGE:
                padpos = max(0,  padpos-10)
            elif menukey == 262:
                padpos = 0
            elif menukey == 360:
                padpos = pady

            self.menu_viewer.refresh(padpos, 0, 1, 1, self.screen_height-2, self.screen_width-2)

            menukey = self.menu_viewer.getch()

            if menukey == curses.KEY_RESIZE:
                break

        self.menu_viewer.erase()


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


class Help:
    """ Display help in a pad. """

    def __init__(self, parent):

        # Init Values
        self.stdscreen = parent.stdscreen
        self.screen_height, self.screen_width = self.stdscreen.getmaxyx()
        self.Config = parent.Config
        self.c_main_txt = parent.c_main_txt
        self.c_main_bdr = parent.c_main_bdr
        self.c_main_ttl = parent.c_main_ttl
        self.c_main_pwf = parent.c_main_pwf

        # Init Menu
        item_lst = ['(h) This Help !',
                    '(ENTER) Selected item menu',
                    '(q|ESC) Previous menu/quit',
                    '(/) Search in variable explorer',
                    '(s) Sort by name/type',
                    '(l) Limit display to keyword',
                    '(u) Undo limit',
                    '(k) Kernel Menu',
                    '(r) Refresh explorer',
                    '(c-r) Restart Daemon',
                    '(R) Restart connection to daemon',
                    '(D) Disconnect from daemon',
                    '(C) Connect to daemon',
                    '(↓) Next line',
                    '(↑) Previous line',
                    '(→|↡) Next page',
                    '(←|↟) Previous page']

        self.nb_items = len(item_lst)
        self.pad_width = 38
        self.pad_height = self.nb_items + 6

        # Create pad
        self.menu_help = curses.newpad(self.pad_height, self.pad_width)
        self.menu_help.keypad(1)
        self.menu_help.bkgd(self.c_main_txt)
        self.menu_help.attrset(self.c_main_bdr | curses.A_BOLD)

        # Create help content
        self.menu_title = ' Help '
        self.menu_help.addstr(2, 2, 'Bindings :', curses.A_BOLD)
        for i in range(self.nb_items):
            self.menu_help.addstr(i+4, 3, item_lst[i], self.c_main_txt | curses.A_DIM)
        self.menu_help.border(0)

        # Create pad title
        if self.Config['font']['pw-font'] == 'True':
            self.menu_help.addstr(0, int((self.pad_width - len(self.menu_title) - 2)/2),
                                  '', self.c_main_pwf | curses.A_BOLD)
            self.menu_help.addstr(self.menu_title, self.c_main_ttl | curses.A_BOLD)
            self.menu_help.addstr('', self.c_main_pwf | curses.A_BOLD)
        else:
            self.menu_help.addstr(0, int((self.pad_width - len(self.menu_title) - 2)/2),
                                  '|' + self.menu_title + '|', self.c_main_ttl | curses.A_BOLD)

    def Display(self):
        """ Display pad. """

        menukey = -1
        padpos = 0
        pady = max(self.nb_items, self.screen_height - 8) - (self.screen_height - 8)

        while menukey not in (27, 113):
            if menukey == curses.KEY_DOWN:
                padpos = min(pady, padpos+1)
            elif menukey == curses.KEY_UP:
                padpos = max(0, padpos-1)
            elif menukey == curses.KEY_RIGHT:
                padpos = min(pady, padpos+5)
            elif menukey == curses.KEY_LEFT:
                padpos = max(0, padpos-5)
            elif menukey == curses.KEY_NPAGE:
                padpos = min(pady, padpos+10)
            elif menukey == curses.KEY_PPAGE:
                padpos = max(0,  padpos-10)
            elif menukey == 262:
                padpos = 0
            elif menukey == 360:
                padpos = pady

            self.menu_help.refresh(padpos, 0, 1, 1, self.screen_height-2, self.pad_width)

            menukey = self.menu_help.getch()

            if menukey == curses.KEY_RESIZE:
                break

        self.menu_help.erase()


class suspend_curses:
    """Context Manager to temporarily leave curses mode"""

    def __enter__(self):
        curses.endwin()

    def __exit__(self, exc_type, exc_val, tb):
        stdscreen = curses.initscr()
        stdscreen.refresh()
        curses.doupdate()
