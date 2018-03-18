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
# Creation Date : Wed Nov 9 10:03:04 2016
# Last Modified : dim. 18 mars 2018 01:28:25 CET
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import curses
from math import ceil
from curses import panel
import locale

from cpyvke.curseswin.varmenu import ExplorerMenu
from cpyvke.curseswin.widgets import WarningMsg, Help
from cpyvke.utils.display import format_cell, type_sort, filter_var_lst, whos_to_dic
from cpyvke.utils.comm import recv_msg
from cpyvke.utils.kernel import restart_daemon
from cpyvke.objects.panel import PanelWin

locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()


class ExplorerWin(PanelWin):
    """ Main window. """

    def __init__(self, app, sock, logger):
        """ Main window constructor """

        super(ExplorerWin, self).__init__(app)

        self.app = app
        self.sock = sock
        self.logger = logger

        # Various Variables :
        self.search = None
        self.filter = None
        self.search_index = 0

        self.win_title = "Variable Explorer"
        self.lst_empty = "Interactive namespace is empty"
        self.wng_msg = ""
        self.mk_sort = 'name'
        self.lst = {}

        # Init Variable Box
        self.row_max = self.screen_height-self.debug_info  # max number of rows
        self.gwin = curses.newwin(self.row_max+2, self.app.screen_width-2, 1, 1)
        self.gwin.bkgd(self.app.c_exp_txt)
        self.gwin.attrset(self.app.c_exp_bdr | curses.A_BOLD)  # border color

    def tasks(self):
        """ Tasks to update curses """

        if self.app.kernel_change:
            self.app.kernel_change = False
            wng_msg = WarningMsg(self.app.stdscr)
            self.sock.force_update(wng_msg)

        # Check Connection to daemon
        self.sock.check_main_socket()

        # Get variables from daemon
        self.get_items()

        # Arange variable list
        self.arange_var_lst()

        # Navigate in the variable list window
        self.navigate_lst()

        # Keys
        self.key_bindings()

        # Update screen size if another menu break because of resizing
        self.resize_curses()

        # Update all static panels
        self.refresh()

        # Get pressed key
        self.pkey = self.app.stdscr.getch()

    def key_bindings(self):
        """ Key Actions ! """

        # Init Warning Msg
        wng_msg = WarningMsg(self.app.stdscr)

        # Menu Variable
        if self.pkey in self.app.kenter and self.row_num != 0:
            # First Update gwin (avoid bug)
            self.refresh()
            # Explorer Menu
            var_menu = ExplorerMenu(self.app, self.sock, self.logger, self)
            if var_menu.is_menu():
                var_menu.display()

        # Menu Help
        elif self.pkey == 63:    # -> ?
            help_menu = Help(self.app)
            help_menu.display()

        # Menu KERNEL
        elif self.pkey in [9, 75, ord('\t')]:    # -> TAB/K
            self.switch = True
#            self.app.kernel_win.display()
#            self.app.cf, self.app.kc = self.app.kernel_win.update_connection()
            # Reset cursor location
            self.position = 1
            self.page = int(ceil(self.position/self.row_max))

        # Menu Search
        elif self.pkey == 47:    # -> /
            self.search_var('Search for :', wng_msg)

        # Sort variable by name/type
        elif self.pkey == 115:       # -> s
            if self.mk_sort == 'name':
                self.mk_sort = 'type'
            elif self.mk_sort == 'type':
                self.mk_sort = 'name'
            self.arange_var_lst()

        # Filter variables
        elif self.pkey == 76:    # -> L
            self.filter = self.search_panel('Limit to :')
            self.mk_sort = 'filter'
            self.position = 1
            self.page = int(ceil(self.position/self.row_max))
            self.arange_var_lst()

        # Reinit
        elif self.pkey == 117:   # -> u
            self.mk_sort = 'name'
            self.wng_msg = ''
            self.position = 1
            self.page = int(ceil(self.position/self.row_max))
            self.arange_var_lst()

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

        # Force Update Variable List sending fake code to daemon
        elif self.pkey == 114:   # -> r
            self.sock.force_update(wng_msg)

    def update_lst(self):
        """ Update the list of variables display """

        # Title
        if self.app.config['font']['pw-font'] == 'True':
            self.gwin.addstr(0, int((self.app.screen_width-len(self.win_title))/2),
                             '', curses.A_BOLD | self.app.c_exp_pwf)
            self.gwin.addstr(self.win_title, self.app.c_exp_ttl | curses.A_BOLD)
            self.gwin.addstr('', self.app.c_exp_pwf | curses.A_BOLD)
        else:
            self.gwin.addstr(0, int((self.app.screen_width-len(self.win_title))/2),
                             '| ' + self.win_title + ' |',
                             self.app.c_exp_ttl | curses.A_BOLD)

        # Reset position if position is greater than the new list of var (reset)
        self.row_num = len(self.strings)
        if self.position > self.row_num:
            self.position = 1
            self.page = 1

        # Items
        for i in range(1+(self.row_max*(self.page-1)),
                       self.row_max+1 + (self.row_max*(self.page-1))):

            if self.row_num == 0:
                self.gwin.addstr(1, 1, self.lst_empty,
                                 curses.A_BOLD | self.app.c_exp_hh)

            else:
                cell = format_cell(self.lst, self.strings[i-1], self.app.screen_width)
                if (i+(self.row_max*(self.page-1)) == self.position+(self.row_max*(self.page-1))):
                    self.gwin.addstr(i-(self.row_max*(self.page-1)), 2,
                                     cell.encode(code), self.app.c_exp_hh)
                else:
                    self.gwin.addstr(i-(self.row_max*(self.page-1)), 2,
                                     cell.encode(code),
                                     curses.A_DIM | self.app.c_exp_txt)
                if i == self.row_num:
                    break

        # Bottom info
        if self.app.config['font']['pw-font'] == 'True' and len(self.wng_msg) > 0:
            self.gwin.addstr(self.row_max+1, int((self.app.screen_width-len(self.wng_msg))/2), '', self.app.c_exp_pwf)
            self.gwin.addstr(self.wng_msg, self.app.c_exp_ttl | curses.A_BOLD)
            self.gwin.addstr('',  self.app.c_exp_pwf | curses.A_BOLD)
        elif len(self.wng_msg) > 0:
            self.gwin.addstr(self.row_max+1,
                             int((self.app.screen_width-len(self.wng_msg))/2),
                             '< ' + self.wng_msg + ' >', curses.A_DIM | self.app.c_exp_ttl)

    def get_items(self):
        """ Get variable from the daemon """

        try:
            tmp = recv_msg(self.sock.MainSock).decode('utf8')
        except BlockingIOError:     # If no message !
            pass
        except OSError:             # If user disconnect cpyvke from socket
            pass
        except AttributeError:      # If kd5 is stopped
            pass
        else:
            if tmp:
                self.lst = whos_to_dic(tmp)
                self.logger.info('Variable list updated')
                self.logger.debug('\n%s', tmp)
                try:
                    # remove temporary file used by daemon from the list
                    del self.lst['fcpyvke0']
                except KeyError:
                    pass

    def arange_var_lst(self):
        """ Organize/Arange variable list. """

        if self.mk_sort == 'name':
            self.strings = sorted(list(self.lst))

        elif self.mk_sort == 'type':
            self.strings = type_sort(self.lst)

        elif self.mk_sort == 'filter':
            self.strings = filter_var_lst(self.lst, self.filter)
            self.wng_msg = 'Filter : ' + self.filter + ' (' + str(len(self.strings)) + ' obj.)'

        # Update number of columns
        self.row_num = len(self.strings)

    def search_panel(self, txt_msg):
        """ """

        # Init Menu
        menu_search = self.app.stdscr.subwin(self.row_max+2, self.app.screen_width-2, 1, 1)
        menu_search.keypad(1)

        # Send menu to a panel
        panel_search = panel.new_panel(menu_search)

        panel_search.top()        # Push the panel to the bottom of the stack.
        panel_search.show()       # Display the panel (which might have been hidden)
        menu_search.clear()
        menu_search.bkgd(self.app.c_exp_txt)
        menu_search.attrset(self.app.c_exp_bdr | curses.A_BOLD)  # Change border color
        menu_search.border(0)
        if self.app.config['font']['pw-font'] == 'True':
            menu_search.addstr(0, int((self.app.screen_width-len(self.win_title))/2),
                               '', self.app.c_exp_pwf)
            menu_search.addstr(self.win_title, self.app.c_exp_ttl | curses.A_BOLD)
            menu_search.addstr('', self.app.c_exp_pwf)
        else:
            menu_search.addstr(0, int((self.app.screen_width-len(self.win_title))/2),
                               '| ' + self.win_title + ' |', self.app.c_exp_ttl | curses.A_BOLD)

        curses.echo()
        menu_search.addstr(2, 3, txt_msg, curses.A_BOLD | self.app.c_exp_txt)
        usr_input = menu_search.getstr(2, len(txt_msg) + 4,
                                       self.screen_width - len(txt_msg) - 8).decode('utf-8')
        curses.noecho()
        panel_search.hide()

        return usr_input

    def search_var(self, txt_msg, wng_msg):
        """ Search an object in the variable list """

        self.search = self.search_panel(txt_msg)

        try:
            self.logger.info('Searching for : {} in :\n{}'.format(self.search, self.strings))
            self.search_index = min([i for i, s in enumerate(self.strings) if self.search in s])
        except ValueError:
            wng_msg.Display('Variable ' + self.search + ' not in kernel')
            pass
        else:
            self.position = self.search_index + 1
            self.page = int(ceil(self.position/self.row_max))
