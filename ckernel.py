#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : CUIMenuKernel.py
# Creation Date : Mon Nov 14 09:08:25 2016
# Last Modified : lun. 28 nov. 2016 16:06:13 CET
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
from __future__ import division  # You don't need this in Python3
import os
import curses
from curses import panel
from math import ceil
from time import sleep
###############################################################################
# Personal Libs
###############################################################################
from ktools import kernel_list, start_new_kernel, shutdown_kernel, connect_kernel
from cwidgets import WarningMsg


###############################################################################
###############################################################################
###############################################################################
class MenuKernelCUI(object):
    def __init__(self, CUI_self):
        ''' Init Kernel menu Class '''

        # Queue for kernel changes
        self.qkc = CUI_self.qkc
        self.kc = CUI_self.kc

        # Define Styles
        curses.init_pair(10, curses.COLOR_BLACK, curses.COLOR_RED)
        self.highlightText = curses.color_pair(10)
        self.normalText = CUI_self.normalText
        self.cyan_text = CUI_self.cyan_text
        self.red_text = CUI_self.red_text
        self.green_text = CUI_self.green_text

        self.stdscreen = CUI_self.stdscreen
        self.screen_width = CUI_self.screen_width
        self.screen_height = CUI_self.screen_height
        self.kernel_info = CUI_self.kernel_info
        self.cf = CUI_self.cf
        # Init Menu
        self.menu_title = '| Kernel Manager |'

        # Init constants
        self.new_kernel_connection = False
        self.position = 1
        self.page = 1

        # Init Variable Box
        self.row_max = self.screen_height-self.kernel_info  # max number of rows

        self.KernelLst = self.stdscreen.subwin(self.row_max+2, self.screen_width-2, 1, 1)
        self.KernelLst.keypad(1)
        self.KernelLst.attrset(self.red_text)  # Change border color
        self.panel_kernel = panel.new_panel(self.KernelLst)
        self.panel_kernel.hide()
        panel.update_panels()

    ############################################################################
    def Display(self):
        ''' Run '''

        self.panel_kernel.top()     # Push the panel to the bottom of the stack.
        self.panel_kernel.show()    # Display the panel
        self.KernelLst.clear()

        self.pkey = -1
        while self.pkey != 113:

            # Get variables from daemon
            self.cf = self.kc.connection_file
            self.lst = kernel_list(self.cf)
            self.row_num = len(self.lst)

            # Navigate in the variable list window
            self.NavigateKernelLst()

            if self.pkey == ord("\n") and self.row_num != 0:
                self.SubMenuKernel()

            # Erase all windows
            self.KernelLst.erase()

            # Create border before updating fields
            self.KernelLst.border(0)

            # Update all windows (virtually)
            self.UpdateKernelLst()     # Update variables list

            # Update display
            self.KernelLst.refresh()
            curses.doupdate()

            # Get pressed key
            self.pkey = self.stdscreen.getch()

            # Sleep a while
            sleep(0.1)

            if self.new_kernel_connection:  # Close menu if new connect
                break

        self.KernelLst.clear()
        self.panel_kernel.hide()
        panel.update_panels()
        curses.doupdate()
        return self.cf, self.kc

###############################################################################
    def UpdateKernelLst(self):
        ''' Update the kernel list '''

        self.KernelLst.addstr(0, int((self.screen_width-len(self.menu_title))/2), self.menu_title, curses.A_BOLD | self.red_text)

        for i in range(1+(self.row_max*(self.page-1)), self.row_max+1+(self.row_max*(self.page-1))):

            if self.row_num == 0:
                self.KernelLst.addstr(1, 1, "No kernel available", self.highlightText)

            else:
                if (i+(self.row_max*(self.page-1)) == self.position+(self.row_max*(self.page-1))):
                    self.KernelLst.addstr(i, 2, self.lst[i-1][0], curses.A_BOLD)
                    if str(self.lst[i-1][1]) == "[Died]":
                        self.KernelLst.addstr(i, self.screen_width-15, str(self.lst[i-1][1]), curses.A_BOLD | self.red_text)
                    elif str(self.lst[i-1][1]) == "[Alive]":
                        self.KernelLst.addstr(i, self.screen_width-15, str(self.lst[i-1][1]), curses.A_BOLD | self.cyan_text)
                    elif str(self.lst[i-1][1]) == "[Connected]":
                        self.KernelLst.addstr(i, self.screen_width-15, str(self.lst[i-1][1]), curses.A_BOLD | self.green_text)
                else:
                    self.KernelLst.addstr(i, 2,  self.lst[i-1][0], curses.A_DIM)
                    if str(self.lst[i-1][1]) == "[Died]":
                        self.KernelLst.addstr(i, self.screen_width-15, str(self.lst[i-1][1]), curses.A_BOLD | self.red_text)
                    elif str(self.lst[i-1][1]) == "[Alive]":
                        self.KernelLst.addstr(i, self.screen_width-15, str(self.lst[i-1][1]), curses.A_BOLD | self.cyan_text)
                    elif str(self.lst[i-1][1]) == "[Connected]":
                        self.KernelLst.addstr(i, self.screen_width-15, str(self.lst[i-1][1]), curses.A_BOLD | self.green_text)
                if i == self.row_num:
                    break

        self.stdscreen.refresh()
        self.KernelLst.refresh()

###############################################################################
    def NavigateKernelLst(self):
        ''' Navigation though the kernel list'''

        pages = int(ceil(self.row_num/self.row_max))
        if self.pkey == curses.KEY_DOWN:
            if self.page == 1:
                if (self.position < self.row_max) and (self.position < self.row_num):
                    self.position = self.position + 1
                else:
                    if pages > 1:
                        self.page = self.page + 1
                        self.position = 1+(self.row_max*(self.page-1))
            elif self.page == pages:
                if self.position < self.row_num:
                    self.position = self.position + 1
            else:
                if self.position < self.row_max+(self.row_max*(self.page-1)):
                    self.position = self.position + 1
                else:
                    self.page = self.page + 1
                    self.position = 1+(self.row_max*(self.page-1))
        if self.pkey == curses.KEY_UP:
            if self.page == 1:
                if self.position > 1:
                    self.position = self.position - 1
            else:
                if self.position > (1+(self.row_max*(self.page-1))):
                    self.position = self.position - 1
                else:
                    self.page = self.page - 1
                    self.position = self.row_max+(self.row_max*(self.page-1))
        if self.pkey in (curses.KEY_LEFT, 339) and self.page > 1:
                self.page = self.page - 1
                self.position = 1+(self.row_max*(self.page-1))

        if self.pkey in (curses.KEY_RIGHT, 338) and self.page < pages:
                self.page = self.page + 1
                self.position = (1+(self.row_max*(self.page-1)))

###############################################################################
# Submenus
###############################################################################
    def SubMenuKernel(self):
        ''' Init kernel list submenu '''

        self.selected = self.lst[self.position-1]
        self.kernel_submenu_lst = self.CreateSubMenuKernel()

        # Various variables
        self.menuposition = 0
        self.kernel_submenu_title = '| ' + self.selected[0].split('-')[1].split('.')[0] + ' |'

        # Menu dimensions
        self.kernel_submenu_width = len(max([self.kernel_submenu_lst[i][0] for i in range(len(self.kernel_submenu_lst))], key=len))
        self.kernel_submenu_width = max(self.kernel_submenu_width, len(self.kernel_submenu_title)) + 5
        self.kernel_submenu_height = len(self.kernel_submenu_lst) + 2

        # Init Menu
        self.kernel_submenu = self.stdscreen.subwin(self.kernel_submenu_height, self.kernel_submenu_width, 2, self.screen_width-self.kernel_submenu_width-2)
        self.kernel_submenu.attrset(self.cyan_text)    # change border color
        self.kernel_submenu.border(0)
        self.kernel_submenu.attrset(self.red_text)  # Change border color
        self.kernel_submenu.keypad(1)

        # Send menu to a panel
        self.panel_kernel_submenu = panel.new_panel(self.kernel_submenu)
        self.panel_kernel_submenu.hide()       # Hide the panel. This does not delete the object, it just makes it invisible.
        panel.update_panels()

        # Submenu
        self.DisplaySubMenuKernel()

    ############################################################################
    def CreateSubMenuKernel(self):
        ''' Create the item list for the kernel submenu  '''

        if self.selected[1] == '[Connected]':
            return [('Create New Kernel', 'self.StartNewKernel()'),
                    ('Remove all died', 'self.RemoveAllDiedKernelJson()')]

        elif self.selected[1] == '[Alive]':
            return [('Connect', 'self.ConnectKernel()'),
                    ('Shutdown', 'self.ShutdownKernel()'),
                    ('Create New Kernel', 'self.StartNewKernel()'),
                    ('Remove all died', 'self.RemoveAllDiedKernelJson()')]

        elif self.selected[1] == '[Died]':
            return [('Restart', 'self.RestartKernel()'),
                    ('Remove connection file', 'self.RemoveKernelJson()'),
                    ('Remove all died', 'self.RemoveAllDiedKernelJson()'),
                    ('Create New Kernel', 'self.StartNewKernel()')]
        else:
            return []

    ############################################################################
    def DisplaySubMenuKernel(self):
        ''' Display the kernel submenu '''

        self.panel_kernel_submenu.top()        # Push the panel to the bottom of the stack.
        self.panel_kernel_submenu.show()       # Display the panel (which might have been hidden)
        self.kernel_submenu.clear()

        menukey = -1
        while menukey not in (27, 113):
            self.kernel_submenu.border(0)
            self.kernel_submenu.addstr(0, int((self.kernel_submenu_width-len(self.kernel_submenu_title))/2), self.kernel_submenu_title, curses.A_BOLD | self.red_text)
            self.kernel_submenu.refresh()
            curses.doupdate()

            # Create entries
            for index, item in enumerate(self.kernel_submenu_lst):
                if index == self.menuposition:
                    mode = curses.A_REVERSE
                else:
                    mode = curses.A_NORMAL

                self.kernel_submenu.addstr(1+index, 1, item[0], mode)

            menukey = self.kernel_submenu.getch()

            if menukey in [curses.KEY_ENTER, ord('\n')]:
                eval(self.kernel_submenu_lst[self.menuposition][1])
                break

            elif menukey == curses.KEY_UP:
                self.NavigateSubMenuKernel(-1)

            elif menukey == curses.KEY_DOWN:
                self.NavigateSubMenuKernel(1)

        self.kernel_submenu.clear()
        self.panel_kernel_submenu.hide()
        panel.update_panels()
        curses.doupdate()

###############################################################################
    def NavigateSubMenuKernel(self, n):
        ''' Navigate through the kernel submenu '''

        self.menuposition += n
        if self.menuposition < 0:
            self.menuposition = 0
        elif self.menuposition >= len(self.kernel_submenu_lst):
            self.menuposition = len(self.kernel_submenu_lst)-1

###############################################################################
# Proceed operations on kernels
###############################################################################
    def StartNewKernel(self):
        kid = start_new_kernel()
        msg = WarningMsg(self.stdscreen)
        msg.Display('Kernel id ' + kid + ' created')

###############################################################################
    def ShutdownKernel(self):
        shutdown_kernel(self.selected[0])

###############################################################################
    def RemoveKernelJson(self):
        os.remove(self.selected[0])
        self.position = 1  # Reinit cursor location

###############################################################################
    def RemoveAllDiedKernelJson(self):
        for json_path, status in self.lst:
            if status == '[Died]':
                os.remove(json_path)
        self.position = 1  # Reinit cursor location

###############################################################################
    def ConnectKernel(self):
        km, self.kc = connect_kernel(self.selected[0])
        self.qkc.put(self.kc)

        # Update kernels
        self.cf = self.kc.connection_file
        self.lst = kernel_list(self.cf)

        # New connection FLAG
        self.new_kernel_connection = True

###############################################################################
    def RestartKernel(self):
        msg = WarningMsg(self.stdscreen)
        msg.Display('Not Implement yet!')
