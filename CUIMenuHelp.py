# -*- coding: utf-8 -*-
"""
Created on Mon Nov 14 09:08:25 2016

@author: cdesjouy
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
