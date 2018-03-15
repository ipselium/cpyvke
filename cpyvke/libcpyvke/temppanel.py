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
# Creation Date : Mon Nov 14 09:08:25 2016
# Last Modified : jeu. 15 mars 2018 00:54:14 CET
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import curses
from curses import panel
from math import ceil
from time import sleep

from .widgets import Help


class PanelWin:
    """ Generic Panel.
    Overload :
        * key_bindings
        * get_items
        * create_menu
    """

    def __init__(self, parent):
        """ Class Constructor """

        self.parent = parent
        self.Config = parent.Config

        # Define Styles
        self.c_txt = parent.c_exp_txt
        self.c_bdr = parent.c_exp_bdr
        self.c_ttl = parent.c_exp_ttl
        self.c_hh = parent.c_exp_hh
        self.c_pwf = parent.c_exp_pwf

        # Bindings
        self.kup = parent.kup
        self.kdown = parent.kdown
        self.kleft = parent.kleft
        self.kright = parent.kright
        self.kenter = parent.kenter
        self.kquit = parent.kquit

        self.stdscreen = parent.stdscreen
        self.screen_height, self.screen_width = self.stdscreen.getmaxyx()
        self.debug_info = parent.debug_info

        # Init Menu
        self.win_title = ' Kernel Manager '

        # Init constants
        self.position = 1
        self.page = 1
        self.quit = False

        # Init Variable Box
        self.row_max = self.screen_height-self.debug_info  # max number of rows
        self.gwin = self.stdscreen.subwin(self.row_max+2, self.screen_width-2, 1, 1)
        self.gwin.keypad(1)
        self.gwin.bkgd(self.c_txt)
        self.gwin.attrset(self.c_bdr | curses.A_BOLD)  # Change border color
        self.gpan = panel.new_panel(self.gwin)
        self.gpan.hide()

    def display(self):
        """ Display the panel. """

        self.gpan.top()     # Push the panel to the bottom of the stack.
        self.gpan.show()    # Display the panel
        self.gwin.clear()

        self.pkey = -1
        while self.pkey not in self.kquit:    # -> q

            # Get items
            self.lst = self.get_items()
            self.row_num = len(self.lst)

            # Menu Help
            if self.pkey == 63:    # -> ?
                help_menu = Help(self.parent)
                help_menu.Display()

            # Key bindings
            self.key_bindings()

            # Navigate in the variable list window
            self.navigate_lst()

            if self.pkey in self.kenter and self.row_num != 0:
                self.init_menu()

            # Erase all windows
            self.gwin.erase()

            # Create border before updating fields
            self.gwin.border(0)

            # Update all windows (virtually)
            self.update_lst()     # Update variables list

            # Update display
            self.gwin.refresh()

            # Get pressed key
            self.pkey = self.stdscreen.getch()

            # Sleep a while
            sleep(0.1)

            if self.quit:
                break

            if self.pkey == curses.KEY_RESIZE:
                break

        self.gwin.clear()
        self.gpan.hide()

    def key_bindings(self):
        """ Key bindings : To overload """

        pass

    def get_items(self):
        """ Return the list of item : To overload """

        return [['This is...'], ['... an example']]

    def update_lst(self):
        """ Update the item list """

        # Title
        if self.Config['font']['pw-font'] == 'True':
            self.gwin.addstr(0, int((self.screen_width-len(self.win_title))/2),
                             '', curses.A_BOLD | self.c_pwf)
            self.gwin.addstr(self.win_title, curses.A_BOLD | self.c_ttl)
            self.gwin.addstr('', curses.A_BOLD | self.c_pwf)
        else:
            self.gwin.addstr(0, int((self.screen_width-len(self.win_title))/2),
                             '|' + self.win_title + '|',
                             curses.A_BOLD | self.c_ttl)

        # Items
        for i in range(1+(self.row_max*(self.page-1)),
                       self.row_max+1+(self.row_max*(self.page-1))):

            if self.row_num == 0:
                self.gwin.addstr(1, 1, "No kernel available",
                                 self.c_hh | curses.A_BOLD)

            else:
                if (i+(self.row_max*(self.page-1)) == self.position+(self.row_max*(self.page-1))):
                    self.gwin.addstr(i, 2, self.lst[i-1][0].ljust(self.screen_width-5),
                                     self.c_hh | curses.A_BOLD)
                else:
                    self.gwin.addstr(i, 2,
                                     self.lst[i-1][0].ljust(self.screen_width-5),
                                     self.c_txt | curses.A_DIM)
                if i == self.row_num:
                    break

        self.stdscreen.refresh()
        self.gwin.refresh()

    def navigate_lst(self):
        """ Navigation though the item list"""

        self.pages = int(ceil(self.row_num/self.row_max))
        if self.pkey in self.kdown:
            self.navigate_down()
        if self.pkey in self.kup:
            self.navigate_up()
        if self.pkey in self.kleft and self.page > 1:
            self.navigate_left()
        if self.pkey in self.kright and self.page < self.pages:
            self.navigate_right()

    def navigate_right(self):
        """ Navigate Right. """

        self.page = self.page + 1
        self.position = (1+(self.row_max*(self.page-1)))

    def navigate_left(self):
        """ Navigate Left. """

        self.page = self.page - 1
        self.position = 1+(self.row_max*(self.page-1))

    def navigate_up(self):
        """ Navigate Up. """

        if self.page == 1:
            if self.position > 1:
                self.position = self.position - 1
        else:
            if self.position > (1+(self.row_max*(self.page-1))):
                self.position = self.position - 1
            else:
                self.page = self.page - 1
                self.position = self.row_max+(self.row_max*(self.page-1))

    def navigate_down(self):
        """ Navigate Down. """

        if self.page == 1:
            if (self.position < self.row_max) and (self.position < self.row_num):
                self.position = self.position + 1
            else:
                if self.pages > 1:
                    self.page = self.page + 1
                    self.position = 1+(self.row_max*(self.page-1))
        elif self.page == self.pages:
            if self.position < self.row_num:
                self.position = self.position + 1
        else:
            if self.position < self.row_max+(self.row_max*(self.page-1)):
                self.position = self.position + 1
            else:
                self.page = self.page + 1
                self.position = 1+(self.row_max*(self.page-1))

    def init_menu(self):
        """ Init the menu """

        self.selected = self.lst[self.position-1]
        self.menu_lst = self.create_menu()

        # Various variables
        self.menu_cursor = 0
        self.menu_title = ' ' + self.selected[0].split('/')[-1] + ' '

        # Menu dimensions
        self.menu_width = len(max(
            [self.menu_lst[i][0] for i in range(len(self.menu_lst))], key=len))
        self.menu_width = max(self.menu_width, len(self.menu_title)) + 4
        self.menu_height = len(self.menu_lst) + 2
        self.title_pos = int((self.menu_width - len(self.menu_title) - 2)/2)

        # Init Menu
        self.gwin_menu = self.stdscreen.subwin(self.menu_height,
                                               self.menu_width, 2,
                                               self.screen_width-self.menu_width-2)
        self.gwin_menu.border(0)
        self.gwin_menu.bkgd(self.c_txt)
        self.gwin_menu.attrset(self.c_bdr | curses.A_BOLD)  # Change border color
        self.gwin_menu.keypad(1)

        # Send menu to a panel
        self.gpan_menu = panel.new_panel(self.gwin_menu)
        # Hide the panel. This does not delete the object, it just makes it invisible.
        self.gpan_menu.hide()
        panel.update_panels()

        # Submenu
        self.display_menu()

    def create_menu(self):
        """ Create the item list for the kernel menu : To overload """

        return [('No Option', 'None')]

    def display_menu(self):
        """ Display the menu """

        self.gpan_menu.top()        # Push the panel to the bottom of the stack.
        self.gpan_menu.show()       # Display the panel (which might have been hidden)
        self.gwin_menu.clear()

        menukey = -1
        while menukey not in self.kquit:
            self.gwin_menu.border(0)

            # Title
            if self.Config['font']['pw-font'] == 'True':
                self.gwin_menu.addstr(0, self.title_pos,
                                      '', curses.A_BOLD | self.c_pwf)
                self.gwin_menu.addstr(self.menu_title,
                                      curses.A_BOLD | self.c_ttl)
                self.gwin_menu.addstr('', curses.A_BOLD | self.c_pwf)
            else:
                self.gwin_menu.addstr(0, self.title_pos,
                                      '|' + self.menu_title + '|',
                                      curses.A_BOLD | self.c_ttl)

            self.gwin_menu.refresh()

            # Create entries
            for index, item in enumerate(self.menu_lst):
                if index == self.menu_cursor:
                    mode = self.c_hh | curses.A_BOLD
                else:
                    mode = self.c_txt | curses.A_DIM

                self.gwin_menu.addstr(1+index, 1, item[0], mode)

            # Wait for keyboard event
            menukey = self.gwin_menu.getch()

            if menukey in self.kenter:
                eval(self.menu_lst[self.menu_cursor][1])
                break

            elif menukey in self.kup:
                self.navigate_menu(-1)

            elif menukey in self.kdown:
                self.navigate_menu(1)

        self.gwin_menu.clear()
        self.gpan_menu.hide()

    def navigate_menu(self, n):
        """ Navigate through the menu """

        self.menu_cursor += n

        if self.menu_cursor < 0:
            self.menu_cursor = 0
        elif self.menu_cursor >= len(self.menu_lst):
            self.menu_cursor = len(self.menu_lst)-1
