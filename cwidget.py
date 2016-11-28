#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : CUIWidgets.py
# Creation Date : Wed Nov  9 16:29:28 2016
# Last Modified : lun. 28 nov. 2016 16:08:12 CET
# Created By : Cyril Desjouy
#
# Copyright © 2016-2017 Cyril Desjouy <cyril.desjouy@free.fr>
# Distributed under terms of the BSD license.
"""

DESCRIPTION

@author: Cyril Desjouy
"""


###############################################################################
# IMPORTS
###############################################################################
import curses
from curses import panel
from time import sleep
###############################################################################
# Personal Libs
###############################################################################
from ctools import dump


###############################################################################
###############################################################################
###############################################################################
class Viewer(object):
    def __init__(self, stdscreen, varval, varname):

        # Init Values
        self.stdscreen = stdscreen
        self.varval = varval
        self.varname = varname
        self.screen_height, self.screen_width = self.stdscreen.getmaxyx()
        self.menu_title = '| ' + self.varname + ' |'

        # Format variable
        if type(self.varval) is str:
            dumped = self.varval.split('\n')
        else:
            dumped = dump(self.varval)

        # Init Menu
        self.pad_width = max(len(self.menu_title), max([len(elem) for elem in dumped])) + 4
        self.pad_height = len(dumped) + 2
        self.menu_viewer = curses.newpad(self.pad_height, self.pad_width)
        self.padpos = 0
        self.menu_viewer.keypad(1)
        for i in range(len(dumped)):
            self.menu_viewer.addstr(1+i, 1, dumped[i], curses.A_BOLD)

        self.menu_viewer.border(0)
        self.menu_viewer.addstr(0, int((self.pad_width - len(self.menu_title))/2), self.menu_title, curses.A_BOLD)

###############################################################################
    def Display(self):
        ''' '''

        menukey = -1
        pady = max(self.pad_height, self.screen_height - 2)
        max_y = pady - (self.screen_height - 2)

        while menukey not in (27, 113):
            if menukey == curses.KEY_DOWN:
                self.padpos = min(max_y, self.padpos+1)
            elif menukey == curses.KEY_UP:
                self.padpos = max(0, self.padpos-1)
            elif menukey == curses.KEY_RIGHT:
                self.padpos = min(max_y, self.padpos+5)
            elif menukey == curses.KEY_LEFT:
                self.padpos = max(0, self.padpos-5)
            elif menukey == curses.KEY_NPAGE:
                self.padpos = min(max_y, self.padpos+10)
            elif menukey == curses.KEY_PPAGE:
                self.padpos = max(0, self.padpos-10)
            elif menukey == 262:
                self.padpos = 0
            elif menukey == 360:
                self.padpos = max_y

            self.menu_viewer.refresh(self.padpos, 0, 1, 1, self.screen_height-2, self.screen_width-2)

            menukey = self.menu_viewer.getch()

        self.menu_viewer.erase()


###############################################################################
###############################################################################
###############################################################################
class WarningMsg(object):
    def __init__(self, stdscreen):
        ''' Init WarningMsg Class '''

        self.stdscreen = stdscreen
        self.screen_height, self.screen_width = self.stdscreen.getmaxyx()

        # Define Styles
        curses.init_pair(2, curses.COLOR_CYAN, -1)
        curses.init_pair(3, curses.COLOR_RED, -1)
        self.cyan_text = curses.color_pair(2)
        self.red_text = curses.color_pair(3)

    def Display(self, wng_msg):
        ''' Display ** wng_msg ** '''

        # Init Menu
        wng_width = len(wng_msg) + 2
        menu_wng = self.stdscreen.subwin(3, wng_width, 3, int((self.screen_width-wng_width)/2))
        menu_wng.attrset(self.cyan_text)    # change border color
        menu_wng.border(0)
        menu_wng.keypad(1)

        # Send menu to a panel
        panel_wng = panel.new_panel(menu_wng)
        panel_wng.top()        # Push the panel to the bottom of the stack.

        menu_wng.addstr(1, 1, wng_msg, curses.A_BOLD | self.red_text)
        panel_wng.show()       # Display the panel (which might have been hidden)
        menu_wng.refresh()
        curses.doupdate()
        sleep(1)

        # Erase the panel
        menu_wng.clear()
        panel_wng.hide()
        panel.update_panels()
        curses.doupdate()
