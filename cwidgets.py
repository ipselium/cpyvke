#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : CUIWidgets.py
# Creation Date : Wed Nov  9 16:29:28 2016
# Last Modified : mar. 29 nov. 2016 11:56:53 CET
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
# Personal Libs
from ctools import dump


###############################################################################
# Class and Methods
###############################################################################
class Viewer(object):
    ''' Display variable content in a pad. '''

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

    def Display(self):
        ''' Create pad to display variable content. '''

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

            if menukey == curses.KEY_RESIZE:
                break

        self.menu_viewer.erase()


class WarningMsg(object):
    ''' Display a message. '''

    def __init__(self, stdscreen):

        self.stdscreen = stdscreen
        self.screen_height, self.screen_width = self.stdscreen.getmaxyx()

        # Define Styles
        curses.init_pair(2, curses.COLOR_CYAN, -1)
        curses.init_pair(3, curses.COLOR_RED, -1)
        self.cyan_text = curses.color_pair(2)
        self.red_text = curses.color_pair(3)

    def Display(self, wng_msg):
        ''' Display **wng_msg** in a panel. '''

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


class MenuHelpCUI(object):
    ''' Display help in a pad. '''

    def __init__(self, stdscreen):

        # Init Values
        self.stdscreen = stdscreen
        self.screen_height, self.screen_width = self.stdscreen.getmaxyx()

        # Init Menu
        self.padpos = 0

        self.nb_items = 14
        self.pad_width = 38
        self.pad_height = self.nb_items+2

        self.menu_help = curses.newpad(self.pad_height, self.pad_width)
        self.menu_help.keypad(1)

        self.menu_title = '| Help |'
        self.menu_help.addstr(2, 2, 'Bindings :', curses.A_BOLD)
        self.menu_help.addstr(4, 3, '(h) This Help !')
        self.menu_help.addstr(5, 3, '(ENTER) Selected item menu')
        self.menu_help.addstr(6, 3, '(q|ESC) Previous menu/quit')
        self.menu_help.addstr(7, 3, '(c) Kernel Menu')
        self.menu_help.addstr(8, 3, '(/) Search in variable explorer')
        self.menu_help.addstr(9, 3, '(↓) Next line')
        self.menu_help.addstr(10, 3, '(↑) Previous line')
        self.menu_help.addstr(11, 3, '(→|↡) Next page')
        self.menu_help.addstr(12, 3, '(←|↟) Previous page')

        self.menu_help.border(0)
        self.menu_help.addstr(0, int((self.pad_width - len(self.menu_title))/2), self.menu_title, curses.A_BOLD)

    def Display(self):
        ''' Display pad. '''

        menukey = -1
        pady = max(self.nb_items, self.screen_height - 4)
        max_y = pady - (self.screen_height - 4)

        while menukey not in (27, 113):
            if menukey == curses.KEY_DOWN:
                self.padpos = min(max_y, self.padpos+1)
            elif menukey == curses.KEY_UP:
                self.padpos = max(0, self.padpos-1)
            elif menukey in (curses.KEY_NPAGE, curses.KEY_RIGHT):
                self.padpos = min(max_y, self.padpos+5)
            elif menukey in (curses.KEY_PPAGE, curses.KEY_LEFT):
                self.padpos = max(0, self.padpos-5)

            self.menu_help.refresh(self.padpos, 0, 1, 1, self.screen_height-2, self.pad_width)

            menukey = self.menu_help.getch()

            if menukey == curses.KEY_RESIZE:
                break

        self.menu_help.erase()


def SizeWng(self):
    ''' Blank screen and display a warning if size of the terminal is too small. '''

    self.stdscreen.erase()
    self.screen_height, self.screen_width = self.stdscreen.getmaxyx()
    msg_actual = str(self.screen_width) + 'x' + str(self.screen_height)
    msg_limit = 'Win must be > ' + str(self.term_min_width) + 'x' + str(self.term_min_height)
    try:
        self.stdscreen.addstr(int(self.screen_height/2), int((self.screen_width-len(msg_limit))/2), msg_limit, curses.A_BOLD | self.red_text)
        self.stdscreen.addstr(int(self.screen_height/2)+1, int((self.screen_width-len(msg_actual))/2), msg_actual, curses.A_BOLD | self.red_text)
    except:
        pass
    self.stdscreen.border(0)
    self.stdscreen.refresh()
    return self.screen_width, self.screen_height
