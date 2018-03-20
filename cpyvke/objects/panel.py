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
# Last Modified : mar. 20 mars 2018 23:16:57 CET
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import curses
from curses import panel
from math import ceil
from time import sleep
import locale

from cpyvke.curseswin.widgets import Help, WarningMsg
from cpyvke.utils.kernel import restart_daemon
from cpyvke.utils.display import format_cell, type_sort, filter_var_lst
from cpyvke.utils.comm import send_msg

code = locale.getpreferredencoding()


class PanelWin:
    """ Generic Panel.
    Overload :
        * key_bindings
        * get_items
        * create_menu
    """

    def __init__(self, app, sock, logger):
        """ Class Constructor """

        # Arguments
        self.app = app
        self.config = app.config
        self.sock = sock
        self.logger = logger

        # Define Style
        self.c_txt = app.c_exp_txt
        self.c_bdr = app.c_exp_bdr
        self.c_ttl = app.c_exp_ttl
        self.c_hh = app.c_exp_hh
        self.c_pwf = app.c_exp_pwf

        self.stdscr = app.stdscr
        self.debug_info = app.debug_info

        # Some strings
        self.win_title = ' template '
        self.empty_dic = "No item available"
        self.wng_msg = ''

        # Init constants
        self.position = 1
        self.page = 1
        self.switch = False
        self.resize = False
        self.pkey = -1
        self.search = None
        self.filter = None
        self.mk_sort = 'name'
        self.search_index = 0

        # Init variables :
        self.lst = {}
        self.strings = []

        # Init Variable Box
        self.app.row_max = self.app.screen_height-self.debug_info  # max number of rows
        self.gwin = self.app.stdscr.subwin(self.app.row_max+2, self.app.screen_width-2, 1, 1)
        self.gwin.keypad(1)
        self.gwin.bkgd(self.c_txt)
        self.gwin.attrset(self.c_bdr | curses.A_BOLD)  # Change border color
        self.screen_height, self.screen_width = self.app.stdscr.getmaxyx()
        self.gpan = panel.new_panel(self.gwin)
        self.gpan.hide()

    def display(self):
        """ Display the panel. """

        self.gpan.top()     # Push the panel to the bottom of the stack.
        self.gpan.show()    # Display the panel
        self.gwin.clear()

        # Update size if it has change when panel was hidden
        self.resize_curses(True)

        self.pkey = -1
        while self.pkey not in self.app.kquit and not self.switch:    # -> q or switch

            # Listen to resize and adapt Curses
            self.resize_curses()

            if self.app.screen_height < self.app.term_min_height or self.app.screen_width < self.app.term_min_width:
                self.app.check_size()
                sleep(0.5)
            else:
                self.tasks()

        self.gwin.clear()
        self.gpan.hide()

    def custom_tasks(self):
        """ Supplementary tasks """

        pass

    def tasks(self):
        """ List of tasks at each iteration """

        # Custom tasks
        self.custom_tasks()

        # Check Connection to daemon
        self.sock.check_main_socket()

        # Get items
        self.lst = self.get_items()
        self.row_num = len(self.lst)

        # Arange item list
        self.arange_lst()

        # Key bindings
        self.common_key_bindings()

        if not self.switch:

            # Navigate in the variable list window
            self.navigate_lst()

            # Update screen size
            self.resize_curses()

            # Update all
            self.refresh()

            # Get key
            self.pkey = self.app.stdscr.getch()

    def refresh(self):
        """ """

        # Erase all windows
        self.gwin.erase()
        self.app.stdscr.erase()

        # Create border before updating fields
        self.app.stdscr.border(0)
        self.gwin.border(0)

        # Update all windows
        if self.app.DEBUG:
            self.app.dbg_socket()         # Display infos about the process
            self.app.dbg_term(self.pkey)         # Display infos about the process
            self.app.dbg_general(self.search, self.filter, self.mk_sort)        # Display debug infos

        self.update_lst()     # Update variables list

        # Update infos -- Bottom
        self.app.bottom_bar_info()
        self.app.stdscr.refresh()
        self.gwin.refresh()

        # Reactive timeout for getch
        curses.halfdelay(self.app.curse_delay)

    def common_key_bindings(self):
        """ Common key bindings """

        # Init Warning Msg
        wng_msg = WarningMsg(self.app.stdscr)

        # Custom key bindings
        self.custom_key_bindings()

        # Menu Help
        if self.pkey == 63:    # -> ?
            help_menu = Help(self.app)
            help_menu.display()

        # Reconnection to socket
        elif self.pkey == 82:    # -> R
            wng_msg.Display(' Restarting connection ')
            self.sock.restart_sockets()
            self.sock.warning_socket(wng_msg)

        # Disconnect from daemon
        elif self.pkey == 68:    # -> D
            self.sock.close_sockets()
            self.sock.warning_socket(wng_msg)

        # Connect to daemon
        elif self.pkey == 67:     # -> C
            self.sock.init_sockets()
            self.sock.warning_socket(wng_msg)

        # Restart daemon
        elif self.pkey == 18:    # -> c-r
            restart_daemon()
            wng_msg.Display(' Restarting Daemon ')
            self.sock.init_sockets()
            self.sock.warning_socket(wng_msg)

        # Menu Search
        elif self.pkey == 47:    # -> /
            self.search_item('Search for :', wng_msg)

        # Sort variable by name/type
        elif self.pkey == 115:       # -> s
            if self.mk_sort == 'name':
                self.mk_sort = 'type'
            elif self.mk_sort == 'type':
                self.mk_sort = 'name'
            self.arange_lst()

        # Filter variables
        elif self.pkey == 76:    # -> L
            self.filter = self.input_panel('Limit to :')
            self.mk_sort = 'filter'
            self.position = 1
            self.page = int(ceil(self.position/self.app.row_max))
            self.arange_lst()

        # Send code
        elif self.pkey == 83:    # -> S
            self.send_code()

        # Reinit
        elif self.pkey == 117:   # -> u
            self.mk_sort = 'name'
            self.wng_msg = ''
            self.position = 1
            self.page = int(ceil(self.position/self.app.row_max))
            self.arange_lst()

        # Panel Menu
        elif self.pkey in self.app.kenter and self.row_num != 0:
            self.init_menu()

    def custom_key_bindings(self):
        """ Key bindings : To overload """

        pass

    def get_items(self):
        """ Return the list of item : To overload """

        return {'name':
                {'type': 'type', 'value': 'value'},
                'This is...':
                {'value': '... a simple...', 'type': '... example'}
                }

    def update_lst(self):
        """ Update the item list """

        # Title
        if self.config['font']['pw-font'] == 'True':
            self.gwin.addstr(0, int((self.app.screen_width-len(self.win_title))/2),
                             '', curses.A_BOLD | self.c_pwf)
            self.gwin.addstr(self.win_title, curses.A_BOLD | self.c_ttl)
            self.gwin.addstr('', curses.A_BOLD | self.c_pwf)
        else:
            self.gwin.addstr(0, int((self.app.screen_width-len(self.win_title))/2),
                             '|' + self.win_title + '|',
                             curses.A_BOLD | self.c_ttl)

        # Reset position if position is greater than the new list of var (reset)
        self.row_num = len(self.strings)
        if self.position > self.row_num:
            self.position = 1
            self.page = 1

        # Items
        for i in range(1+(self.app.row_max*(self.page-1)),
                       self.app.row_max+1+(self.app.row_max*(self.page-1))):

            if self.row_num == 0:
                self.gwin.addstr(1, 1, self.empty_dic,
                                 curses.A_BOLD | self.c_hh)

            else:
                self.cell1, self.cell2 = format_cell(self.lst, self.strings[i-1], self.app.screen_width)
                if (i+(self.app.row_max*(self.page-1)) == self.position+(self.app.row_max*(self.page-1))):
                    self.gwin.addstr(i-(self.app.row_max*(self.page-1)), 2,
                                     self.cell1.encode(code), curses.A_BOLD | self.c_hh)
                    self.setup_type_display_select(i)
                else:
                    self.gwin.addstr(i-(self.app.row_max*(self.page-1)), 2,
                                     self.cell1.encode(code),
                                     curses.A_DIM | self.c_txt)
                    self.setup_type_display_unselect(i)
                if i == self.row_num:
                    break

        # Bottom info
        if self.app.config['font']['pw-font'] == 'True' and len(self.wng_msg) > 0:
            self.gwin.addstr(self.app.row_max+1,
                             int((self.app.screen_width-len(self.wng_msg))/2),
                             '', self.c_pwf)
            self.gwin.addstr(self.wng_msg, self.c_ttl | curses.A_BOLD)
            self.gwin.addstr('',  self.c_pwf | curses.A_BOLD)
        elif len(self.wng_msg) > 0:
            self.gwin.addstr(self.app.row_max+1,
                             int((self.app.screen_width-len(self.wng_msg))/2),
                             '< ' + self.wng_msg + ' >', curses.A_DIM | self.c_ttl)

        self.app.stdscr.refresh()
        self.gwin.refresh()

    def setup_type_display_select(self, i):
        if "[Died]" in self.cell2:
            self.gwin.addstr(i-(self.app.row_max*(self.page-1)), len(self.cell1),
                             self.cell2, curses.A_BOLD | self.c_di)
        elif "[Alive]" in self.cell2:
            self.gwin.addstr(i-(self.app.row_max*(self.page-1)), len(self.cell1),
                             self.cell2, curses.A_BOLD | self.c_al)
        elif "[Connected]" in self.cell2:
            self.gwin.addstr(i-(self.app.row_max*(self.page-1)), len(self.cell1),
                             self.cell2, curses.A_BOLD | self.c_co)
        else:
            self.gwin.addstr(i-(self.app.row_max*(self.page-1)), len(self.cell1),
                             self.cell2, curses.A_BOLD | self.c_hh)

    def setup_type_display_unselect(self, i):
        if "[Died]" in self.cell2:
            self.gwin.addstr(i-(self.app.row_max*(self.page-1)), len(self.cell1),
                             self.cell2, curses.A_BOLD | self.c_di)
        elif "[Alive]" in self.cell2:
            self.gwin.addstr(i-(self.app.row_max*(self.page-1)), len(self.cell1),
                             self.cell2, curses.A_BOLD | self.c_al)
        elif "[Connected]" in self.cell2:
            self.gwin.addstr(i-(self.app.row_max*(self.page-1)), len(self.cell1),
                             self.cell2, curses.A_BOLD | self.c_co)
        else:
            self.gwin.addstr(i-(self.app.row_max*(self.page-1)), len(self.cell1),
                             self.cell2, curses.A_BOLD | self.c_txt)

    def arange_lst(self):
        """ Organize/Arange variable list. """

        if self.mk_sort == 'name':
            self.strings = sorted(list(self.lst))

        elif self.mk_sort == 'type':
            self.strings = type_sort(self.lst)

        elif self.mk_sort == 'filter' and self.filter:
            self.strings = filter_var_lst(self.lst, self.filter)
            self.wng_msg = 'Filter : ' + self.filter + ' (' + str(len(self.strings)) + ' obj.)'

        else:
            self.strings = list(self.lst)

        # Update number of columns
        self.row_num = len(self.strings)

    def send_code(self):
        """ Send code to current kernel """

        code = self.input_panel('>>')
        send_msg(self.sock.RequestSock, '<code>' + code)
        self.logger.info('code sent to kernel : {}'.format(code))

    def search_item(self, txt_msg, wng_msg):
        """ Search an object in the variable list """

        self.search = self.input_panel(txt_msg)

        try:
            self.logger.info('Searching for : {} in :\n{}'.format(self.search, self.strings))
            self.search_index = min([i for i, s in enumerate(self.strings) if self.search in s])
        except ValueError:
            wng_msg.Display(self.search + ' not found !')
            pass
        else:
            self.position = self.search_index + 1
            self.page = int(ceil(self.position/self.app.row_max))

    def resize_curses(self, force=False):
        """ Check if terminal is resized and adapt screen """

        resize = curses.is_term_resized(self.screen_height, self.screen_width)
        cond = resize is True and self.app.screen_height >= self.app.term_min_height and self.app.screen_width >= self.app.term_min_width
        if cond or force:
            self.app.screen_height, self.app.screen_width = self.app.stdscr.getmaxyx()  # new heigh and width of object stdscreen
            self.screen_height, self.screen_width = self.app.stdscr.getmaxyx()  # new heigh and width of object stdscreen
            self.app.row_max = self.app.screen_height-self.app.debug_info
            self.app.stdscr.clear()
            self.gwin.clear()
            self.gwin.resize(self.app.row_max+2, self.app.screen_width-2)
            curses.resizeterm(self.app.screen_height, self.app.screen_width)
            self.app.stdscr.refresh()
            self.gwin.refresh()

    def navigate_lst(self):
        """ Navigation though the item list"""

        self.pages = int(ceil(self.row_num/self.app.row_max))
        if self.pkey in self.app.kdown:
            self.navigate_down()
        if self.pkey in self.app.kup:
            self.navigate_up()
        if self.pkey in self.app.kleft and self.page > 1:
            self.navigate_left()
        if self.pkey in self.app.kright and self.page < self.pages:
            self.navigate_right()

    def navigate_right(self):
        """ Navigate Right. """

        self.page = self.page + 1
        self.position = (1+(self.app.row_max*(self.page-1)))

    def navigate_left(self):
        """ Navigate Left. """

        self.page = self.page - 1
        self.position = 1+(self.app.row_max*(self.page-1))

    def navigate_up(self):
        """ Navigate Up. """

        if self.page == 1:
            if self.position > 1:
                self.position = self.position - 1
        else:
            if self.position > (1+(self.app.row_max*(self.page-1))):
                self.position = self.position - 1
            else:
                self.page = self.page - 1
                self.position = self.app.row_max+(self.app.row_max*(self.page-1))

    def navigate_down(self):
        """ Navigate Down. """

        if self.page == 1:
            if (self.position < self.app.row_max) and (self.position < self.row_num):
                self.position = self.position + 1
            else:
                if self.pages > 1:
                    self.page = self.page + 1
                    self.position = 1+(self.app.row_max*(self.page-1))
        elif self.page == self.pages:
            if self.position < self.row_num:
                self.position = self.position + 1
        else:
            if self.position < self.app.row_max+(self.app.row_max*(self.page-1)):
                self.position = self.position + 1
            else:
                self.page = self.page + 1
                self.position = 1+(self.app.row_max*(self.page-1))

    def input_panel(self, txt_msg):
        """ """

        # Init Menu
        iwin = self.app.stdscr.subwin(self.app.row_max+2, self.app.screen_width-2, 1, 1)
        iwin.keypad(1)

        # Send menu to a panel
        ipan = panel.new_panel(iwin)

        ipan.top()        # Push the panel to the bottom of the stack.
        ipan.show()       # Display the panel (which might have been hidden)
        iwin.clear()
        iwin.bkgd(self.c_txt)
        iwin.attrset(self.c_bdr | curses.A_BOLD)  # Change border color
        iwin.border(0)
        if self.app.config['font']['pw-font'] == 'True':
            iwin.addstr(0, int((self.app.screen_width-len(self.win_title))/2),
                        '', self.c_pwf)
            iwin.addstr(self.win_title, self.c_ttl | curses.A_BOLD)
            iwin.addstr('', self.c_pwf)
        else:
            iwin.addstr(0, int((self.app.screen_width-len(self.win_title))/2),
                        '| ' + self.win_title + ' |', self.c_ttl | curses.A_BOLD)

        curses.echo()
        iwin.addstr(2, 3, txt_msg, curses.A_BOLD | self.c_txt)
        usr_input = iwin.getstr(2, len(txt_msg) + 4,
                                self.app.screen_width - len(txt_msg) - 8).decode('utf-8')
        curses.noecho()
        ipan.hide()

        return usr_input

    def init_menu(self):
        """ Init the menu """

        self.selected = self.strings[self.position-1]
        self.menu_lst = self.create_menu()

        # Various variables
        self.menu_cursor = 0
        self.menu_title = ' ' + self.selected.split('/')[-1] + ' '

        # Menu dimensions
        self.menu_width = len(max(
            [self.menu_lst[i][0] for i in range(len(self.menu_lst))], key=len))
        self.menu_width = max(self.menu_width, len(self.menu_title)) + 4
        self.menu_height = len(self.menu_lst) + 2
        self.title_pos = int((self.menu_width - len(self.menu_title) - 2)/2)

        # Init Menu
        self.gwin_menu = self.app.stdscr.subwin(self.menu_height,
                                                self.menu_width, 2,
                                                self.app.screen_width-self.menu_width-2)
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
        while menukey not in self.app.kquit:
            self.gwin_menu.border(0)

            # Title
            if self.config['font']['pw-font'] == 'True':
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

            if menukey in self.app.kenter:
                eval(self.menu_lst[self.menu_cursor][1])
                break

            elif menukey in self.app.kup:
                self.navigate_menu(-1)

            elif menukey in self.app.kdown:
                self.navigate_menu(1)

            if menukey == curses.KEY_RESIZE:
                self.resize = True
                break

        self.gwin_menu.clear()
        self.gpan_menu.hide()

    def navigate_menu(self, n):
        """ Navigate through the menu """

        self.menu_cursor += n

        if self.menu_cursor < 0:
            self.menu_cursor = 0
        elif self.menu_cursor >= len(self.menu_lst):
            self.menu_cursor = len(self.menu_lst)-1
