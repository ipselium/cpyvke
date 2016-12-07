#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : cwidgets.py
# Creation Date : Wed Nov  9 16:29:28 2016
# Last Modified : mer. 07 déc. 2016 16:40:55 CET
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
        self.padpos = 0
        self.menu_viewer.keypad(1)
        for i in range(len(dumped)):
            self.menu_viewer.addstr(1+i, 1, dumped[i], self.c_exp_txt)

        self.menu_viewer.bkgd(self.c_exp_txt)
        self.menu_viewer.attrset(self.c_exp_bdr | curses.A_BOLD)  # Change border color
        self.menu_viewer.border(0)
        if self.Config['font']['pw-font'] == 'True':
            self.menu_viewer.addstr(0, int((self.pad_width - len(self.menu_title) - 2)/2), '', self.c_exp_pwf | curses.A_BOLD)
            self.menu_viewer.addstr(self.menu_title, self.c_exp_ttl | curses.A_BOLD)
            self.menu_viewer.addstr('', self.c_exp_pwf | curses.A_BOLD)
        else:
            self.menu_viewer.addstr(0, int((self.pad_width - len(self.menu_title) - 2)/2), '|' + self.menu_title + '|', self.c_exp_ttl | curses.A_BOLD)

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
        self.c_warn_txt = curses.color_pair(1)
        self.c_warn_bdr = curses.color_pair(2)

    def Display(self, wng_msg):
        ''' Display **wng_msg** in a panel. '''

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


class Help(object):
    ''' Display help in a pad. '''

    def __init__(self, parent):

        # Init Values
        self.stdscreen = parent.stdscreen
        self.screen_height, self.screen_width = self.stdscreen.getmaxyx()
        self.Config = parent.Config

        # Init Menu
        self.c_main_txt = curses.color_pair(11)
        self.c_main_bdr = curses.color_pair(12)
        self.c_main_ttl = curses.color_pair(13)
        self.c_main_pwf = curses.color_pair(15)

        self.padpos = 0

        self.nb_items = 14
        self.pad_width = 38
        self.pad_height = self.nb_items+2

        self.menu_help = curses.newpad(self.pad_height, self.pad_width)
        self.menu_help.keypad(1)
        self.menu_help.bkgd(self.c_main_txt)
        self.menu_help.attrset(self.c_main_bdr | curses.A_BOLD)  # Change border color

        self.menu_title = ' Help '
        self.menu_help.addstr(2, 2, 'Bindings :', curses.A_BOLD)
        self.menu_help.addstr(4, 3, '(h) This Help !', self.c_main_txt | curses.A_DIM)
        self.menu_help.addstr(5, 3, '(ENTER) Selected item menu', self.c_main_txt | curses.A_DIM)
        self.menu_help.addstr(6, 3, '(q|ESC) Previous menu/quit', self.c_main_txt | curses.A_DIM)
        self.menu_help.addstr(7, 3, '(s) Sort by name/type', self.c_main_txt | curses.A_DIM)
        self.menu_help.addstr(8, 3, '(l) Limit display to keyword', self.c_main_txt | curses.A_DIM)
        self.menu_help.addstr(9, 3, '(u) Undo limit', self.c_main_txt | curses.A_DIM)
        self.menu_help.addstr(10, 3, '(c) Kernel Menu', self.c_main_txt | curses.A_DIM)
        self.menu_help.addstr(11, 3, '(/) Search in variable explorer', self.c_main_txt | curses.A_DIM)
        self.menu_help.addstr(12, 3, '(↓) Next line', self.c_main_txt | curses.A_DIM)
        self.menu_help.addstr(13, 3, '(↑) Previous line', self.c_main_txt | curses.A_DIM)
        self.menu_help.addstr(14, 3, '(→|↡) Next page', self.c_main_txt | curses.A_DIM)
        self.menu_help.addstr(15, 3, '(←|↟) Previous page', self.c_main_txt | curses.A_DIM)
        self.menu_help.border(0)

        if self.Config['font']['pw-font'] == 'True':
            self.menu_help.addstr(0, int((self.pad_width - len(self.menu_title) - 2)/2), '', self.c_main_pwf | curses.A_BOLD)
            self.menu_help.addstr(self.menu_title, self.c_main_ttl | curses.A_BOLD)
            self.menu_help.addstr('', self.c_main_pwf | curses.A_BOLD)
        else:
            self.menu_help.addstr(0, int((self.pad_width - len(self.menu_title) - 2)/2), '|' + self.menu_title + '|', self.c_main_ttl | curses.A_BOLD)

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
