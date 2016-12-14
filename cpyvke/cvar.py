#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : cvar.py
# Creation Date : Wed Nov  9 16:29:28 2016
# Last Modified : mer. 14 déc. 2016 11:54:55 CET
# Created By : Cyril Desjouy
#
# Copyright © 2016-2017 Cyril Desjouy <ipselium@free.fr>
# Distributed under terms of the BSD license.
"""

DESCRIPTION

@author: Cyril Desjouy
"""


###############################################################################
# IMPORTS
###############################################################################
import curses
import json
from curses import panel
from numpy import load
from time import sleep, strftime, time
import os
# Personal
from inspector import Inspect
from cwidgets import Viewer, WarningMsg
from kd5 import send_msg

###############################################################################
# Class and Methods
###############################################################################


class MenuVar(object):
    ''' Class to handle variable menus. '''

    def __init__(self, parent):

        # Init parent
        self.stdscreen = parent.stdscreen
        self.screen_height, self.screen_width = self.stdscreen.getmaxyx()  # get heigh and width of stdscreen
        self.Config = parent.Config
        self.c_exp_txt = curses.color_pair(21)
        self.c_exp_bdr = curses.color_pair(22)
        self.c_exp_ttl = curses.color_pair(23)
        self.c_exp_hh = curses.color_pair(24)
        self.c_exp_pwf = curses.color_pair(25)
        self.SaveDir = parent.Config['path']['save-dir']
        self.LogFile = parent.LogFile
        self.RequestSock = parent.RequestSock

        # Variables properties
        self.varname = parent.strings[parent.position-1]
        self.vartype = parent.variables[parent.strings[parent.position-1]]['type']

        # Get variable value
        if parent.variables[parent.strings[parent.position-1]]['type'] == 'module':
            self.varval = parent.variables[parent.strings[parent.position-1]]['value']
            self.varval = self.varval.split("'")[1]

        elif parent.variables[parent.strings[parent.position-1]]['type'] in ('dict', 'list', 'tuple', 'str'):
            self.filename = '/tmp/tmp_' + self.varname
            code = "with open('" + self.filename + "' , 'w') as f:\n\tjson.dump(" + self.varname + ", f)"
            send_msg(self.RequestSock, '<code>' + code)
            self.Wait(parent)
            try:
                with open(self.filename, 'r') as f:
                    self.varval = json.load(f)
            except Exception as err:
                Wng = WarningMsg(self.stdscreen)
                Wng.Display('Kernel Busy ! Try again...')
                self.varval = '[Busy]'
                with open(self.LogFile, 'a') as f:
                    f.write(strftime("[%D :: %H:%M:%S] ::  Error :: Busy ::") + str(err) + '\n')
            else:
                self.view = Viewer(self)
                os.remove(self.filename)

        elif parent.variables[parent.strings[parent.position-1]]['type'] == 'ndarray':
            self.filename = '/tmp/tmp_' + self.varname + '.npy'
            code = "np.save('" + self.filename + "', " + self.varname + ')'
            send_msg(self.RequestSock, '<code>' + code)
            self.Wait(parent)
            try:
                self.varval = load(self.filename)
                os.remove(self.filename)
            except Exception as err:
                Wng = WarningMsg(self.stdscreen)
                Wng.Display('Kernel Busy ! Try again...')
                self.varval = '[Busy]'
                with open(self.LogFile, 'a') as f:
                    f.write(strftime("[%D :: %H:%M:%S] ::  Error :: Busy ::") + str(err) + '\n')

        else:
            self.varval = '[Not Impl.]'

        # Init Inspector
        self.inspect = Inspect(self.varval, self.varname, self.vartype)

        # Create Menu List
        self.menu_title = self.varname
        self.menu_lst = self.CreateMenuLst()
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

    def Display(self):
        ''' Display general menu in a panel. '''

        self.panel_menu.top()        # Push the panel to the bottom of the stack
        self.panel_menu.show()       # Display the panel
        self.menu.clear()
        self.menu.border(0)
        if self.Config['font']['pw-font'] == 'True':
            self.menu.addstr(0, int((self.menu_width-len(self.menu_title) - 4)/2), '', self.c_exp_pwf | curses.A_BOLD)
            self.menu.addstr(' ' + self.menu_title + ' ', self.c_exp_ttl | curses.A_BOLD)
            self.menu.addstr('', self.c_exp_pwf | curses.A_BOLD)
        else:
            self.menu.addstr(0, int((self.menu_width-len(self.menu_title) - 4)/2), '| ' + self.menu_title + ' |', self.c_exp_ttl | curses.A_BOLD)

        menukey = -1
        while menukey not in (27, 113):

            self.menu.refresh()
            for index, item in enumerate(self.menu_lst):
                if index == self.menuposition:
                    mode = self.c_exp_hh
                else:
                    mode = self.c_exp_txt

                msg = item[0]
                self.menu.addstr(1+index, 1, msg, mode)

            menukey = self.menu.getch()

            if menukey in [curses.KEY_ENTER, ord('\n')]:
                Wng = WarningMsg(self.stdscreen)
                try:
                    eval(self.menu_lst[self.menuposition][1])
                    if self.menu_lst[self.menuposition][0] == 'Save':
                        Wng.Display('Saved !')
                except Exception as err:
                    if self.menu_lst[self.menuposition][0] == 'Save':
                        Wng.Display('Not saved !')
                    with open(self.LogFile, 'a') as f:
                        f.write(strftime("[%D :: %H:%M:%S] ::  Error ::") + str(err) + '\n')
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

    def Wait(self, parent):
        ''' Wait for variable value. '''

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
            self.stdscreen.addstr(parent.position - (parent.page-1)*parent.row_max + 1, 2, spinner[i], self.c_exp_txt | curses.A_BOLD)

            self.stdscreen.refresh()
            if i < len(spinner) - 1:
                i += 1
            else:
                i = 0

            if time() - ti > 3:
                break

        self.stdscreen.refresh()

    def Navigate(self, n, size):
        ''' Navigate through the general menu. '''

        self.menuposition += n
        if self.menuposition < 0:
            self.menuposition = 0
        elif self.menuposition >= size:
            self.menuposition = size-1

    def CreateMenuLst(self):
        ''' Create the item list for the general menu. '''

        if self.varval == '[Busy]':
            return [('Busy', ' ')]

        elif self.vartype == 'module':
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
                except Exception as err:
                    Wng.Display('Not saved !')
                    with open(self.LogFile, 'a') as f:
                        f.write(strftime("[%D :: %H:%M:%S] ::  Error ::") + str(err) + '\n')
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