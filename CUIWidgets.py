# -*- coding: utf-8 -*-
"""
Created on Wed Nov  9 16:29:28 2016

@author: cdesjouy
"""
###############################################################################
# Imports
###############################################################################
import curses
from curses import panel
from time import sleep
import subprocess
import json
###############################################################################
# Personal Libs
###############################################################################
from ModuleInspector import describe, manual  # Used in the menu_list
from CUISuspend import suspend_curses


###############################################################################
###############################################################################
###############################################################################
class Inspector(object):
    def __init__(self, CUI_self):
        ''' Init Inspector Class '''
        self.varval = CUI_self.varval
        self.stdscreen = CUI_self.CUI_self.stdscreen

###############################################################################
    def Display(self, Arg):
        ''' '''
        if Arg == 'Help':
            manual(self.varval)
        elif Arg == 'Description':
            describe(__import__(self.varval))

        with suspend_curses():
            subprocess.call(['less', 'tmp'])
            subprocess.call(['rm', 'tmp'])

        self.stdscreen.refresh()


###############################################################################
###############################################################################
###############################################################################
class Viewer(object):
    def __init__(self, CUI_self):
        ''' Init Viewer Class '''
        self.CUI_self = CUI_self
        self.varval = CUI_self.varval
        self.stdscreen = CUI_self.CUI_self.stdscreen
        self.screen_width = CUI_self.CUI_self.screen_width

        self.menu_title = '| Viewer |'

###############################################################################
    def Display(self):
        # Init Menu
        self.menu_help = self.stdscreen.subwin(0, 0)
        self.menu_help.keypad(1)
        self.panel_help = panel.new_panel(self.menu_help)
        panel.update_panels()
        self.panel_help.top()        # Push the panel to the bottom of the stack.
        self.panel_help.show()       # Display the panel (which might have been hidden)
        self.menu_help.clear()

        menukey = -1
        while menukey not in (27, 113):
            self.menu_help.border(0)
            self.menu_help.addstr(0, int((self.screen_width - len(self.menu_title))/2), self.menu_title, curses.A_BOLD)
            self.menu_help.addstr(5, 5, json.dumps(self.varval, indent=4), curses.A_BOLD)
            curses.doupdate()
            menukey = self.menu_help.getch()

        self.menu_help.clear()
        self.panel_help.hide()
        panel.update_panels()
        curses.doupdate()


###############################################################################
###############################################################################
###############################################################################
class WarningMsg(object):
    def __init__(self, CUI_self):
        ''' Init WarningMsg Class '''
        self.cyan_text = CUI_self.cyan_text
        self.red_text = CUI_self.red_text
        self.stdscreen = CUI_self.stdscreen
        self.screen_width = CUI_self.screen_width

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
