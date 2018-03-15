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
# Last Modified : jeu. 15 mars 2018 00:55:27 CET
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import os
import logging
import json
import numpy
import curses
from curses import panel
from time import sleep, time

from .classwin import ClassWin
from .widgets import Viewer, WarningMsg
from ..utils.inspector import Inspect
from ..utils.comm import send_msg


logger = logging.getLogger('cpyvke.cvar')


class MenuVar:
    """ Class to handle variable menus. """

    def __init__(self, parent):
        """ Class constructor. """

        # Init parent
        self.parent = parent
        self.stdscreen = parent.stdscreen
        self.Config = parent.Config
        self.c_exp_txt = curses.color_pair(21)
        self.c_exp_bdr = curses.color_pair(22)
        self.c_exp_ttl = curses.color_pair(23)
        self.c_exp_hh = curses.color_pair(24)
        self.c_exp_pwf = curses.color_pair(25)
        self.SaveDir = parent.Config['path']['save-dir']
        self.RequestSock = parent.RequestSock
        self.position = parent.position
        self.row_max = parent.row_max
        self.page = parent.page
        self.debug_info = parent.debug_info

        # Bindings :
        self.kdown = [curses.KEY_DOWN, 106]
        self.kup = [curses.KEY_UP, 107]
        self.kleft = [curses.KEY_LEFT, 104, 339]
        self.kright = [curses.KEY_RIGHT, 108, 338]
        self.kenter = [curses.KEY_ENTER, ord("\n"), 10, 32]
        self.kquit = [27, 113]

        # get heigh and width of stdscreen
        self.screen_height, self.screen_width = self.stdscreen.getmaxyx()

        # Variables properties
        self.varname = parent.strings[parent.position-1]
        self.vartype = parent.variables[parent.strings[parent.position-1]]['type']
        self.varval = parent.variables[parent.strings[parent.position-1]]['value']

        # Get Variable characteristics
        self.get_variable()

        # Init Inspector
        self.inspect = Inspect(self.varval, self.varname, self.vartype)

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
        self.quit_menu = False

    def get_variable(self):
        """ Get Variable characteristics. """
        if self.vartype == 'module':
            self.get_module()

        elif self.vartype in ('dict', 'list', 'tuple', 'str', 'unicode'):
            self.get_structure()

        elif self.vartype == 'ndarray':
            self.get_ndarray()

        # Class
        elif '.' + self.vartype in self.varval:
            self.get_class()
        else:
            self.varval = '[Not Impl.]'
            self._ismenu = True

    def get_class(self):
        """ Get Class characteristics. """

        self.vartype = 'class'
        self.filename = '/tmp/tmp_' + self.varname
        self.code = "with open('{}' , 'w') as fcpyvke0:\n\t_json.dump(_inspect.inspect_class_instance({}), fcpyvke0)".format(self.filename, self.varname)
        self.send_code()
        self.class_win = ClassWin(self)

    def get_module(self):
        """ Get modules characteristics """

        self.filename = '/tmp/tmp_' + self.varname
        self.code = "with open('{}' , 'w') as fcpyvke0:\n\t_json.dump({}.__name__, fcpyvke0)".format(self.filename, self.varname)
        self.send_code()

    def get_structure(self):
        """ Get Dict/List/Tuple characteristics """

        self.filename = '/tmp/tmp_' + self.varname
        self.code = "with open('{}' , 'w') as fcpyvke0:\n\t_json.dump({}, fcpyvke0)".format(self.filename, self.varname)
        self.send_code()

    def get_ndarray(self):
        """ Get ndarray characteristics. """

        self.filename = '/tmp/tmp_' + self.varname + '.npy'
        code = "_np.save('" + self.filename + "', " + self.varname + ')'
        try:
            send_msg(self.RequestSock, '<code>' + code)
            logger.debug("Name of module '{}' asked to kd5".format(self.varname))
            self.wait()
            self.varval = numpy.load(self.filename)
        except Exception:
            logger.error('Get traceback : ', exc_info=True)
            self.kernel_busy()
        else:
            logger.debug('kd5 answered')
            os.remove(self.filename)
            self._ismenu = True

    def get_help(self):
        """ Help item in menu """

        if self.vartype == 'function':
            self.filename = '/tmp/tmp_' + self.varname
            self.code = "with open('{}' , 'w') as fcpyvke0:\n\t_json.dump({}.__doc__, fcpyvke0)".format(self.filename, self.varname)
            self.send_code()

        self.inspect = Inspect(self.varval, self.varname, self.vartype)
        self.inspect.Display('less', 'Help')

    def send_code(self):
        """ Send code to kernel and except answer ! """

        try:
            send_msg(self.RequestSock, '<code>' + self.code)
            logger.debug("Inspecting '{}'".format(self.varname))
            self.wait()
            with open(self.filename, 'r') as f:
                self.varval = json.load(f)
        except Exception:
            logger.error('Get traceback', exc_info=True)
            self.kernel_busy()
        else:
            logger.debug('kd5 answered')
            self.view = Viewer(self)
            os.remove(self.filename)
            self._ismenu = True

    def kernel_busy(self):
        """ Handle silent kernel. """

        Wng = WarningMsg(self.stdscreen)
        Wng.Display('Kernel Busy ! Try again...')
        self.varval = '[Busy]'
        self._ismenu = False

    def is_menu(self):
        """ Used in cmain to check if menu is open! """
        return self._ismenu

    def display(self):
        """ Display general menu in a panel. """

        self.panel_menu.top()        # Push the panel to the bottom of the stack
        self.panel_menu.show()       # Display the panel
        self.menu.clear()
        self.menu.border(0)
        if self.Config['font']['pw-font'] == 'True':
            self.menu.addstr(0, int((self.menu_width-len(self.menu_title) - 4)/2),
                             '', self.c_exp_pwf | curses.A_BOLD)
            self.menu.addstr(' ' + self.menu_title + ' ', self.c_exp_ttl | curses.A_BOLD)
            self.menu.addstr('', self.c_exp_pwf | curses.A_BOLD)
        else:
            self.menu.addstr(0, int((self.menu_width-len(self.menu_title) - 4)/2),
                             '| ' + self.menu_title + ' |', self.c_exp_ttl | curses.A_BOLD)

        menukey = -1
        while menukey not in self.kquit:

            self.menu.refresh()
            for index, item in enumerate(self.menu_lst):
                if index == self.menuposition:
                    mode = self.c_exp_hh
                else:
                    mode = self.c_exp_txt

                msg = item[0]
                self.menu.addstr(1+index, 1, msg, mode)

            menukey = self.menu.getch()

            if menukey in self.kenter:
                self.enter_menu()
                if self.quit_menu:
                    break

            elif menukey in self.kup:
                self.navigate(-1, len(self.menu_lst))

            elif menukey in self.kdown:
                self.navigate(1, len(self.menu_lst))

            if menukey == curses.KEY_RESIZE:
                break

        self.menu.clear()
        self.panel_menu.hide()

    def enter_menu(self):
        """ Variable menu. """

        Wng = WarningMsg(self.stdscreen)
        try:
            eval(self.menu_lst[self.menuposition][1])
            if self.menu_lst[self.menuposition][0] == 'Save':
                Wng.Display('Saved !')
        except Exception:
            logger.error('Menu', exc_info=True)
            if self.menu_lst[self.menuposition][0] == 'Save':
                Wng.Display('Not saved !')
        else:
            self.quit_menu = True

    def wait(self):
        """ Wait for variable value. """

        i = 0
        spinner = [['.', 'o', 'O', 'o'],
                   ['.', 'o', 'O', '@', '*'],
                   ['v', '<', '^', '>'],
                   ['(o)(o)', '(-)(-)', '(_)(_)'],
                   ['◴', '◷', '◶', '◵'],
                   ['←', '↖', '↑', '↗', '→', '↘', '↓', '↙'],
                   ['▁', '▃', '▄', '▅', '▆', '▇', '█', '▇', '▆', '▅', '▄', '▃'],
                   ['▉', '▊', '▋', '▌', '▍', '▎', '▏', '▎', '▍', '▌', '▋', '▊', '▉'],
                   ['▖', '▘', '▝', '▗'],
                   ['▌', '▀', '▐', '▄'],
                   ['┤', '┘', '┴', '└', '├', '┌', '┬', '┐'],
                   ['◢', '◣', '◤', '◥'],
                   ['◰', '◳', '◲', '◱'],
                   ['◐', '◓', '◑', '◒'],
                   ['|', '/', '-', '\\'],
                   ['.', 'o', 'O', '@', '*'],
                   ['◡◡', '⊙⊙', '◠◠'],
                   ['◜ ', ' ◝', ' ◞', '◟ '],
                   ['◇', '◈', '◆'],
                   ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷'],
                   ['⠁', '⠂', '⠄', '⡀', '⢀', '⠠', '⠐', '⠈'],
                   ['Searching.', 'Searching..', 'Searching...']
                   ]

        spinner = spinner[19]
        ti = time()
        while os.path.exists(self.filename) is False:
            sleep(0.05)
            self.stdscreen.addstr(self.position - (self.page-1)*self.row_max + 1,
                                  2, spinner[i], self.c_exp_txt | curses.A_BOLD)

            self.stdscreen.refresh()
            if i < len(spinner) - 1:
                i += 1
            else:
                i = 0

            if time() - ti > 3:
                break

        self.stdscreen.refresh()

    def navigate(self, n, size):
        """ Navigate through the general menu. """

        self.menuposition += n
        if self.menuposition < 0:
            self.menuposition = 0
        elif self.menuposition >= size:
            self.menuposition = size-1

    def del_var(self):
        """ Delete a variable from kernel. """

        code = 'del {}'.format(self.varname)
        try:
            send_msg(self.RequestSock, '<code>' + code)
            logger.debug("Send delete signal for variable {}".format(self.varname))
        except Exception:
            logger.error('Delete variable :', exc_info=True)
            Wng = WarningMsg(self.stdscreen)
            Wng.Display('Kernel Busy ! Try again...')
        else:
            Wng = WarningMsg(self.stdscreen)
            Wng.Display('Variable {} deleted'.format(self.varname))

    def create_menu_lst(self):
        """ Create the item list for the general menu. """

        if self.varval == '[Busy]':
            return [('Busy', ' ')]

        elif self.vartype in ('int', 'float', 'complex'):
            return [('Del', "self.del_var()")]

        elif self.vartype in ['module', 'function']:
            return [('View', 'self.view.display()'),
                    ('Help', "self.get_help()")]

        elif self.vartype in ('dict', 'tuple', 'str', 'list', 'unicode'):
            return [('View', 'self.view.display()'),
                    ('Less', "self.inspect.Display('less')"),
                    ('Edit', "self.inspect.Display('vim')"),
                    ('Save', "self.inspect.Save(self.SaveDir)"),
                    ('Del', "self.del_var()")]

        elif (self.vartype == 'ndarray') and (len(self.varval.shape) == 1):
            return [('Plot', 'self.inspect.Plot1D()'),
                    ('Save', 'self.menu_save()'),
                    ('Del', "self.del_var()")]

        elif (self.vartype == 'ndarray') and (len(self.varval.shape) == 2):
            return [('Plot 2D', 'self.inspect.Plot2D()'),
                    ('Plot (cols)', 'self.inspect.Plot1Dcols()'),
                    ('Plot (lines)', 'self.inspect.Plot1Dlines()'),
                    ('Save', 'self.menu_save()'),
                    ('Del', "self.del_var()")]

        elif self.vartype == 'class':
            return [('View', 'self.view.display()'),
                    ('Inspect', 'self.class_win.display()')]

        else:
            return []

    def menu_save(self):
        """ Create the save menu. """

        # Init Menu
        save_menu = self.stdscreen.subwin(5, 6, self.menu_height, self.screen_width-9)
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
        while menukey not in self.kquit:
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

            if menukey in self.kenter:
                Wng = WarningMsg(self.stdscreen)
                try:
                    eval(save_lst[self.menuposition][1])
                    Wng.Display('Saved !')
                except Exception:
                    Wng.Display('Not saved !')
                    logger.error('Menu save', exc_info=True)
                else:
                    self.menuposition = 0
                    break

            elif menukey in self.kup:
                self.navigate(-1, len(save_lst))

            elif menukey == self.kdown:
                self.navigate(1, len(save_lst))

            if menukey == curses.KEY_RESIZE:
                self.menuposition = 0
                break

        save_menu.clear()
        panel_save.hide()
