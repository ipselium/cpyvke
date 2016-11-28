#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : CUIMenuHelp.py
# Creation Date : Mon Nov 14 09:08:25 2016
# Last Modified : lun. 28 nov. 2016 12:33:46 CET
# Created By : Cyril Desjouy
#
# Copyright © 2016-2017 Cyril Desjouy <cyril.desjouy@free.fr>
# Distributed under terms of the BSD license.
"""

DESCRIPTION

@author: Cyril Desjouy
"""
###############################################################################
# Imports
###############################################################################
import curses
from curses import panel


###############################################################################
###############################################################################
###############################################################################
class MenuHelpCUI(object):
    def __init__(self, stdscreen):
        ''' Init MenuCUI Class '''

        # Init Values
        self.stdscreen = stdscreen
        self.screen_height, self.screen_width = self.stdscreen.getmaxyx()

        # Init Menu
        self.menu_help = self.stdscreen.subwin(0, 0)
        self.menu_help.keypad(1)
        self.panel_help = panel.new_panel(self.menu_help)
        self.panel_help.hide()
        panel.update_panels()

        self.menu_title = '| Help |'

    ############################################################################
    def Display(self):
        ''' '''

        self.panel_help.top()
        self.panel_help.show()
        self.menu_help.clear()

        menukey = -1
        while menukey not in (27, 113):
            self.menu_help.border(0)
            self.menu_help.addstr(0, int((self.screen_width - len(self.menu_title))/2), self.menu_title, curses.A_BOLD)
            self.menu_help.addstr(2, 3, 'Bindings :', curses.A_BOLD)
            self.menu_help.addstr(3, 5, '(h) Help')
            self.menu_help.addstr(4, 5, '(q|ESC) Previous menu/quit')
            self.menu_help.addstr(5, 5, '(c) Kernel Menu')
            self.menu_help.addstr(6, 5, '(/) Search in variable explorer')
            self.menu_help.addstr(7, 5, '(↓) Next line')
            self.menu_help.addstr(8, 5, '(↑) Previous line')
            self.menu_help.addstr(9, 5, '(→) Next page')
            self.menu_help.addstr(10, 5, '(←) Previous page')

            self.menu_help.refresh()
            curses.doupdate()
            menukey = self.menu_help.getch()

        self.menu_help.clear()
        self.panel_help.hide()
        panel.update_panels()
        curses.doupdate()


###############################################################################
###############################################################################
###############################################################################
class MenuHelpPadCUI(object):
    def __init__(self, stdscreen):
        ''' Init MenuCUI Class '''

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
        self.menu_help.addstr(8, 3, '(s) Save Menu')
        self.menu_help.addstr(9, 3, '(/) Search in variable explorer')
        self.menu_help.addstr(10, 3, '(↓) Next line')
        self.menu_help.addstr(11, 3, '(↑) Previous line')
        self.menu_help.addstr(12, 3, '(→|↡) Next page')
        self.menu_help.addstr(13, 3, '(←|↟) Previous page')

        self.menu_help.border(0)
        self.menu_help.addstr(0, int((self.pad_width - len(self.menu_title))/2), self.menu_title, curses.A_BOLD)

    ############################################################################
    def Display(self):
        ''' '''

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

        self.menu_help.erase()
