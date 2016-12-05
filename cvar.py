#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : CUIMenuVar.py
# Creation Date : Wed Nov  9 16:29:28 2016
# Last Modified : mar. 06 déc. 2016 00:28:50 CET
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
from numpy import array
import time
# Personal
from inspector import Inspect
from cwidgets import Viewer, WarningMsg


###############################################################################
# Class and Methods
###############################################################################

class MenuVarCUI(object):
    ''' Class to handle variable menus. '''

    def __init__(self, parent):

        self.stdscreen = parent.stdscreen
        self.c_exp_txt = curses.color_pair(21)
        self.c_exp_bdr = curses.color_pair(22)
        self.c_exp_ttl = curses.color_pair(23)
        self.c_exp_hh = curses.color_pair(24)
        self.SaveDir = parent.Config['path']['save-dir']
        self.LogDir = parent.LogDir

        # Variables properties
        self.varname = parent.strings[parent.position-1]
        self.vartype = parent.variables[parent.strings[parent.position-1]]['type']
        self.screen_width = parent.screen_width

        # Get variable value
        if parent.variables[parent.strings[parent.position-1]]['type'] == 'module':
            self.varval = parent.variables[parent.strings[parent.position-1]]['value']
            self.varval = self.varval.split("'")[1]

        elif parent.variables[parent.strings[parent.position-1]]['type'] in ('dict', 'list', 'tuple'):
            parent.qreq.put('print ' + self.varname)
            self.varval = parent.qans.get()
            self.varval = eval(self.varval)
            self.view = Viewer(self.stdscreen, self.varval, self.varname)

        elif parent.variables[parent.strings[parent.position-1]]['type'] == 'str':
            parent.qreq.put(self.varname)
            self.varval = parent.qans.get()
            self.varval = eval(self.varval)
            self.view = Viewer(self.stdscreen, self.varval, self.varname)

        elif parent.variables[parent.strings[parent.position-1]]['type'] == 'ndarray':
            parent.qreq.put(self.varname)
            self.varval = parent.qans.get()
            self.varval = eval(self.varval)

        else:
            self.varval = '[Not Impl.]'

        # Init Inspector
        self.inspect = Inspect(self.varval, self.varname, self.vartype)

        # Create Menu List
        self.menu_title = '| ' + self.varname + ' |'
        self.menu_lst = self.CreateMenuLst()
        if len(self.menu_lst) == 0:
            self.menu_lst.append(('No Options', 'exit'))

        # Menu dimensions
        self.menu_width = len(max([self.menu_lst[i][0] for i in range(len(self.menu_lst))], key=len))
        self.menu_width = max(self.menu_width, len(self.menu_title)) + 5
        self.menu_height = len(self.menu_lst) + 2

        # Init Menu
        self.menu = self.stdscreen.subwin(self.menu_height, self.menu_width, 2, self.screen_width-self.menu_width-2)
        self.menu.bkgd(self.c_exp_txt)
        self.menu.attrset(self.c_exp_bdr | curses.A_BOLD)  # Change border color
        self.menu.border(0)
        self.menu.keypad(1)

        # Send menu to a panel
        self.panel_menu = panel.new_panel(self.menu)
        self.panel_menu.hide()       # Hide the panel. Doesnt delete the object

        # Various variables
        self.menuposition = 0

    def Display(self):
        ''' Display general menu in a panel. '''

        self.panel_menu.top()        # Push the panel to the bottom of the stack
        self.panel_menu.show()       # Display the panel
        self.menu.clear()

        menukey = -1
        while menukey not in (27, 113):
            self.menu.border(0)
            self.menu.addstr(0, int((self.menu_width-len(self.menu_title))/2), self.menu_title, self.c_exp_ttl | curses.A_BOLD)
            self.menu.refresh()
            for index, item in enumerate(self.menu_lst):
                if index == self.menuposition:
                    mode = self.c_exp_hh | curses.A_BOLD
                else:
                    mode = self.c_exp_txt | curses.A_DIM

                msg = item[0]
                self.menu.addstr(1+index, 1, msg, mode)

            menukey = self.menu.getch()

            if menukey in [curses.KEY_ENTER, ord('\n')]:
                Wng = WarningMsg(self.stdscreen)
                try:
                    eval(self.menu_lst[self.menuposition][1])
                    if self.menu_lst[self.menuposition][0] == 'Save':
                        Wng.Display('Saved !')
                except Exception, err:
                    if self.menu_lst[self.menuposition][0] == 'Save':
                        Wng.Display('Not saved !')
                    with open(self.LogDir + 'cpyvke.log', 'a') as f:
                        f.write(time.strftime("[%D :: %H:%M:%S] ::  Error ::") + str(err) + '\n')
                else:
                    break

            elif menukey == curses.KEY_UP:
                self.Navigate(-1, len(self.menu_lst))

            elif menukey == curses.KEY_DOWN:
                self.Navigate(1, len(self.menu_lst))

            if menukey == curses.KEY_RESIZE:
                break

        self.menu.clear()
        self.panel_menu.hide()

    def Navigate(self, n, size):
        ''' Navigate through the general menu. '''

        self.menuposition += n
        if self.menuposition < 0:
            self.menuposition = 0
        elif self.menuposition >= size:
            self.menuposition = size-1

    def CreateMenuLst(self):
        ''' Create the item list for the general menu. '''

        if self.vartype == 'module':
            return [('Description', "self.inspect.Display('less', 'Description')"),
                    ('Help', "self.inspect.Display('less', 'Help')")]

        elif self.vartype in ('dict', 'tuple', 'str', 'list'):
            return [('View', 'self.view.Display()'),
                    ('Less', "self.inspect.Display('less')"),
                    ('Edit', "self.inspect.Display('vim')"),
                    ('Save', "self.inspect.Save(self.SaveDir)")]

        elif (self.vartype == 'ndarray') and (len(self.varval.shape) == 1):
            return [('Plot', 'self.inspect.Plot1D()'),
                    ('Save', 'self.MenuSave()')]

        elif (self.vartype == 'ndarray') and (len(self.varval.shape) == 2):
            return [('Plot 2D', 'self.inspect.Plot2D()'),
                    ('Plot (cols)', 'self.inspect.Plot1Dcols()'),
                    ('Plot (lines)', 'self.inspect.Plot1Dlines()'),
                    ('Save', 'self.MenuSave()')]
        else:
            return []

    def MenuSave(self):
        ''' Create the save menu. '''

        # Init Menu
        save_menu = self.stdscreen.subwin(5, 6, self.menu_height-2, self.screen_width-9)
        save_menu.bkgd(self.c_exp_txt)
        save_menu.attrset(self.c_exp_bdr | curses.A_BOLD)  # Change border color
        save_menu.border(0)
        save_menu.keypad(1)

        # Send menu to a panel
        panel_save = panel.new_panel(save_menu)
        panel_save.hide()

        # Various variables
        self.menuposition = 0

        save_lst = [('txt', "self.inspect.SaveNP(self.varname, self.SaveDir, 'txt')"),
                    ('npy', "self.inspect.SaveNP(self.varname, self.SaveDir, 'npy')"),
                    ('npz', "self.inspect.SaveNP(self.varname, self.SaveDir, 'npz')")]
        panel_save.top()        # Push the panel to the bottom of the stack.
        panel_save.show()       # Display the panel (which might have been hidden)
        save_menu.clear()

        menukey = -1
        while menukey not in (27, 113):
            save_menu.border(0)
            save_menu.refresh()
            for index, item in enumerate(save_lst):
                if index == self.menuposition:
                    mode = self.c_exp_hh | curses.A_BOLD
                else:
                    mode = self.c_exp_txt | curses.A_DIM

                msg = item[0]
                save_menu.addstr(1+index, 1, msg, mode)

            menukey = save_menu.getch()

            if menukey in [curses.KEY_ENTER, ord('\n')]:
                Wng = WarningMsg(self.stdscreen)
                try:
                    eval(save_lst[self.menuposition][1])
                    Wng.Display('Saved !')
                except Exception, err:
                    Wng.Display('Not saved !')
                    with open(self.LogDir + 'cpyvke.log', 'a') as f:
                        f.write(time.strftime("[%D :: %H:%M:%S] ::  Error ::") + str(err) + '\n')
                else:
                    break

            elif menukey == curses.KEY_UP:
                self.Navigate(-1, len(save_lst))

            elif menukey == curses.KEY_DOWN:
                self.Navigate(1, len(save_lst))

            if menukey == curses.KEY_RESIZE:
                break

        save_menu.clear()
        panel_save.hide()
