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
# Last Modified : sam. 17 mars 2018 12:20:05 CET
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import curses
from curses import panel

from cpyvke.curseswin.classwin import ClassWin
from cpyvke.curseswin.widgets import Viewer, WarningMsg
from cpyvke.utils.inspector import ProceedInspection, Inspect


class ExplorerMenu:
    """ Class to handle variable menus. """

    def __init__(self, app, sock, logger, parent):
        """ Class constructor. """

        self.app = app
        self.sock = sock
        self.logger = logger
        self.parent = parent

        # Init parent
        self.save_dir = self.app.config['path']['save-dir']
        self.position = parent.position
        self.row_max = parent.row_max
        self.page = parent.page

        # Warning messages
        self.wng = WarningMsg(self.app.stdscr)

        # get heigh and width of stdscreen
        self.screen_height, self.screen_width = self.app.stdscr.getmaxyx()

        # Variables properties
        self.varname = parent.strings[parent.position-1]
        self.vartype = parent.lst[parent.strings[parent.position-1]]['type']
        self.varval = parent.lst[parent.strings[parent.position-1]]['value']

        # Get Variable characteristics
        proc = ProceedInspection(self.app, self.sock, self.logger,
                                 self.varname, self.varval, self.vartype,
                                 self.position, self.page, self.row_max, self.wng)
        self._ismenu, self.varname, self.varval, self.vartype = proc.get_variable()

        # Init all Inspectors
        self.inspect = Inspect(self.varval, self.varname, self.vartype)
        self.view = Viewer(self.app, self.varval, self.varname)
        self.class_win = ClassWin(self.app, self.varval, self.varname)

        # Create Menu List
        self.menu_title = self.varname
        self.menu_lst = self.create_menu_lst()
        if len(self.menu_lst) == 0:
            self.menu_lst.append(('No Options', 'exit'))

        # Menu dimensions
        self.menu_width = len(max([self.menu_lst[i][0] for i in range(len(self.menu_lst))], key=len))
        self.menu_width = max(self.menu_width, len(self.menu_title)) + 9
        self.menu_height = len(self.menu_lst) + 2

        # Init Menu
        self.menu = self.app.stdscr.subwin(self.menu_height, self.menu_width, 2, self.screen_width-self.menu_width-2)
        self.menu.bkgd(self.app.c_exp_txt)
        self.menu.attrset(self.app.c_exp_bdr | curses.A_BOLD)  # Change border color
        self.menu.border(0)
        self.menu.keypad(1)

        # Send menu to a panel
        self.panel_menu = panel.new_panel(self.menu)
        self.panel_menu.hide()       # Hide the panel. Doesnt delete the object

        # Various variables
        self.menuposition = 0
        self.quit_menu = False

    def is_menu(self):
        """ Used in cmain to check if menu is open! """
        return self._ismenu

    def display(self):
        """ Display general menu in a panel. """

        self.panel_menu.top()        # Push the panel to the bottom of the stack
        self.panel_menu.show()       # Display the panel
        self.menu.clear()
        self.menu.border(0)
        if self.app.config['font']['pw-font'] == 'True':
            self.menu.addstr(0, int((self.menu_width-len(self.menu_title) - 4)/2),
                             '', self.app.c_exp_pwf | curses.A_BOLD)
            self.menu.addstr(' ' + self.menu_title + ' ', self.app.c_exp_ttl | curses.A_BOLD)
            self.menu.addstr('', self.app.c_exp_pwf | curses.A_BOLD)
        else:
            self.menu.addstr(0, int((self.menu_width-len(self.menu_title) - 4)/2),
                             '| ' + self.menu_title + ' |', self.app.c_exp_ttl | curses.A_BOLD)

        menukey = -1
        while menukey not in self.app.kquit:

            self.menu.refresh()
            for index, item in enumerate(self.menu_lst):
                if index == self.menuposition:
                    mode = self.app.c_exp_hh
                else:
                    mode = self.app.c_exp_txt

                msg = item[0]
                self.menu.addstr(1+index, 1, msg, mode)

            menukey = self.menu.getch()

            if menukey in self.app.kenter:
                self.enter_menu()
                if self.quit_menu:
                    break

            elif menukey in self.app.kup:
                self.navigate(-1, len(self.menu_lst))

            elif menukey in self.app.kdown:
                self.navigate(1, len(self.menu_lst))

            if menukey == curses.KEY_RESIZE:
                break

        self.menu.clear()
        self.panel_menu.hide()

    def enter_menu(self):
        """ Variable menu. """

        try:
            eval(self.menu_lst[self.menuposition][1])
            if self.menu_lst[self.menuposition][0] == 'Save':
                self.wng.Display('Saved !')
        except Exception:
            self.logger.error('Menu', exc_info=True)
            if self.menu_lst[self.menuposition][0] == 'Save':
                self.wng.Display('Not saved !')
        else:
            self.quit_menu = True

    def navigate(self, n, size):
        """ Navigate through the general menu. """

        self.menuposition += n
        if self.menuposition < 0:
            self.menuposition = 0
        elif self.menuposition >= size:
            self.menuposition = size-1

    def create_menu_lst(self):
        """ Create the item list for the general menu. """

        if self.varval == '[Busy]':
            return [('Busy', ' ')]

        elif self.vartype in ('int', 'float', 'complex'):
            return [('Del', "self.sock.del_var(self.varname, self.wng)")]

        elif self.vartype in ['module', 'function']:
            return [('View', 'self.view.display()'),
                    ('Help', "self.get_help()")]

        elif self.vartype in ('dict', 'tuple', 'str', 'list', 'unicode'):
            return [('View', 'self.view.display()'),
                    ('Less', "self.inspect.Display('less')"),
                    ('Edit', "self.inspect.Display('vim')"),
                    ('Save', "self.inspect.Save(self.save_dir)"),
                    ('Del', "self.sock.del_var(self.varname, self.wng)")]

        elif (self.vartype == 'ndarray') and (len(self.varval.shape) == 1):
            return [('Plot', 'self.inspect.Plot1D()'),
                    ('Save', 'self.menu_save()'),
                    ('Del', "self.sock.del_var(self.varname, self.wng)")]

        elif (self.vartype == 'ndarray') and (len(self.varval.shape) == 2):
            return [('Plot 2D', 'self.inspect.Plot2D()'),
                    ('Plot (cols)', 'self.inspect.Plot1Dcols()'),
                    ('Plot (lines)', 'self.inspect.Plot1Dlines()'),
                    ('Save', 'self.menu_save()'),
                    ('Del', "self.sock.del_var(self.varname, self.wng)")]

        elif self.vartype == 'class':
            return [('View', 'self.view.display()'),
                    ('Inspect', 'self.class_win.display()')]

        else:
            return []

    def menu_save(self):
        """ Create the save menu. """

        # Init Menu
        save_menu = self.app.stdscr.subwin(5, 6, self.menu_height, self.screen_width-9)
        save_menu.bkgd(self.app.c_exp_txt)
        save_menu.attrset(self.app.c_exp_bdr | curses.A_BOLD)  # Change border color
        save_menu.border(0)
        save_menu.keypad(1)

        # Send menu to a panel
        panel_save = panel.new_panel(save_menu)
        panel_save.hide()

        # Various variables
        self.menuposition = 0

        save_lst = [('txt', "self.inspect.SaveNP(self.varname, self.save_dir, 'txt')"),
                    ('npy', "self.inspect.SaveNP(self.varname, self.save_dir, 'npy')"),
                    ('npz', "self.inspect.SaveNP(self.varname, self.save_dir, 'npz')")]
        panel_save.top()        # Push the panel to the bottom of the stack.
        panel_save.show()       # Display the panel (which might have been hidden)
        save_menu.clear()

        menukey = -1
        while menukey not in self.app.kquit:
            save_menu.border(0)
            save_menu.refresh()
            for index, item in enumerate(save_lst):
                if index == self.menuposition:
                    mode = self.app.c_exp_hh | curses.A_BOLD
                else:
                    mode = self.app.c_exp_txt | curses.A_DIM

                msg = item[0]
                save_menu.addstr(1+index, 1, msg, mode)

            menukey = save_menu.getch()

            if menukey in self.app.kenter:
                try:
                    eval(save_lst[self.menuposition][1])
                    self.wng.Display('Saved !')
                except Exception:
                    self.wng.Display('Not saved !')
                    self.logger.error('Menu save', exc_info=True)
                else:
                    self.menuposition = 0
                    break

            elif menukey in self.app.kup:
                self.navigate(-1, len(save_lst))

            elif menukey == self.app.kdown:
                self.navigate(1, len(save_lst))

            if menukey == curses.KEY_RESIZE:
                self.menuposition = 0
                break

        save_menu.clear()
        panel_save.hide()
