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
# Last Modified : mer. 28 mars 2018 23:12:01 CEST
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import time
import locale
import curses
import abc
from curses import panel
from math import ceil
from cpyvke.curseswin.widgets import Help, WarningMsg
from cpyvke.curseswin.prompt import Prompt
from cpyvke.utils.kd import restart_daemon
from cpyvke.utils.display import format_cell
from cpyvke.utils.comm import send_msg


code = locale.getpreferredencoding()


class PanelWin(abc.ABC):
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

        # Some strings
        self.win_title = ' template '
        self.empty_dic = "No item available"
        self.limit_msg = ''
        self.prompt_msg = ''
        self.panel_name = 'template'

        # Init constants
        self.position = 0
        self.page = 1
        self.resize = False
        self.pkey = -1
        self.filter = None
        self.mk_sort = 'name'
        self.search = None
        self.search_index = 0
        self.search_lst = []
        self.prompt_time = 0

        # Init variables :
        self.lst = {}
        self.strings = []

        # Prompt
        self.prompt = Prompt(self.app)

        # Init Warning Msg
        self.wng = WarningMsg(self.app.stdscr)

        # Init Variable Box
        self.app.panel_height = self.app.screen_height-self.app.debug_info  # max number of rows
        self.app.row_max = self.app.panel_height - 2
        self.gwin = self.app.stdscr.subwin(self.app.panel_height, self.app.screen_width, 0, 0)
        self.gwin.keypad(1)
        self.gwin.bkgd(self.c_txt)
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
        while self.pkey not in self.app.kquit and self.app.close_signal == 'continue':

            if self.app.kernel_switch or self.app.explorer_switch:
                break

            # Listen to resize and adapt Curses
            self.resize_curses()

            if self.app.screen_height < self.app.term_min_height or self.app.screen_width < self.app.term_min_width:
                self.app.check_size()
                time.sleep(0.5)
            else:
                self.tasks()

        self.gwin.clear()
        self.gpan.hide()

    def custom_tasks(self):
        """ Supplementary tasks [To overload if needed] """

        pass

    def tasks(self):
        """ List of tasks at each iteration """

        # Custom tasks
        self.custom_tasks()

        # Check Connection to daemon
        self.sock.check_main_socket()

        # Get items
        self.lst = self.get_items()
        self.row_num = len(self.lst) - 1

        # Arange item list
        self.arange_lst()

        # Key bindings
        self.common_key_bindings()

        if not self.app.kernel_switch and not self.app.explorer_switch and self.app.close_signal == "continue":

            # Navigate in the variable list window
            self.navigate_lst()

            # Update screen size
            self.resize_curses()

            # Update all
            self.refresh()

            # Get key
            self.pkey = self.app.stdscr.getch()

    def refresh(self):
        """ Refresh all objects. """

        # Erase all windows
        self.gwin.erase()
        self.app.stdscr.erase()

        # Create border before updating fields
        self.gwin.border(0)

        # Update all windows
        if self.app.DEBUG:
            self.app.dbg_socket()         # Display infos about the process
            self.app.dbg_term(self.pkey)         # Display infos about the process
            self.app.dbg_general(self.search, self.filter, self.mk_sort)        # Display debug infos

        # Fill the main box !
        self.fill_main_box()

        # Update infos -- Bottom
        self.app.bottom_bar_info()
        self.prompt_msg_display()
        self.app.stdscr.refresh()
        self.gwin.refresh()

        # Reactive timeout for getch
        curses.halfdelay(self.app.curse_delay)

    def common_key_bindings(self):
        """ Common key bindings """

        # Custom key bindings
        self.custom_key_bindings()

        # Socket actions
        self.socket_key_bindings()

        # Item list
        self.list_key_bindings()

        # Menu Help
        if self.pkey == 63:    # -> ?
            help_menu = Help(self.app)
            help_menu.display()

        # Prompt
        elif self.pkey == 58:     # -> :
            self.cmd = self.prompt.with_completion(chr(self.pkey))
            self.prompt_cmd()

        # Send code
        elif self.pkey == 120:    # -> x
            self.send_code()

    def list_key_bindings(self):
        """ Actions linked to list of item. """

        # Menu Search
        if self.pkey == 47:    # -> /
            self.search_item('Search for : ')

        # Next item (search)
        if self.pkey == 110:    # -> n
            self.search_item_next()

        # Sort variable by name/type
        elif self.pkey == 115:       # -> s
            if self.mk_sort == 'name':
                self.mk_sort = 'type'
            elif self.mk_sort == 'type':
                self.mk_sort = 'name'
            self.arange_lst()

        # Filter variables
        elif self.pkey == 102:    # -> f
            self.filter = self.prompt.simple('Limit to : ')
            if self.filter:
                self.mk_sort = 'filter'
                self.position = 0
                self.page = 1
                self.arange_lst()
            else:
                self.filter = None

        # Reinit
        elif self.pkey == 117:   # -> u
            self.mk_sort = 'name'
            self.limit_msg = ''
            self.position = 0
            self.page = 1
            self.arange_lst()

        # Panel Menu
        elif self.pkey in self.app.kenter and self.row_num != -1:
            self.init_menu()

    def socket_key_bindings(self):
        """ Socket actions key bindings. """

        if self.pkey == 82:    # -> R
            self.daemon_restart_connection()

        elif self.pkey == 68:    # -> D
            self.daemon_disconnect()

        elif self.pkey == 67:     # -> C
            self.daemon_connect()

        elif self.pkey == 18:    # -> c-r
            self.daemon_restart()

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

    def fill_main_box(self):
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
        self.row_num = len(self.strings) - 1
        if self.position > self.row_num:
            self.position = 0
            self.page = 1

        # Items
        for i in range(self.app.row_max*(self.page-1),
                       self.app.row_max + self.app.row_max*(self.page-1)):

            if self.row_num == -1:
                self.gwin.addstr(1, 1, self.empty_dic,
                                 curses.A_BOLD | self.c_hh)

            elif i <= self.row_num:
                self.cell1, self.cell2 = format_cell(self.lst, self.strings[i], self.app.screen_width)
                if i == self.position:
                    self.gwin.addstr(i + 1 - self.app.row_max*(self.page-1), 2,
                                     self.cell1.encode(code), curses.A_BOLD | self.c_hh)
                    self.fill_main_box_type_selected(i)
                else:
                    self.gwin.addstr(i + 1 - self.app.row_max*(self.page-1), 2,
                                     self.cell1.encode(code), curses.A_DIM | self.c_txt)
                    self.fill_main_box_type(i)

        # Bottom info
        if self.app.config['font']['pw-font'] == 'True' and len(self.limit_msg) > 0:
            self.gwin.addstr(self.app.panel_height-1,
                             int((self.app.screen_width-len(self.limit_msg))/2),
                             '', self.c_pwf)
            self.gwin.addstr(self.limit_msg, self.c_ttl | curses.A_BOLD)
            self.gwin.addstr('',  self.c_pwf | curses.A_BOLD)
        elif len(self.limit_msg) > 0:
            self.gwin.addstr(self.app.panel_height-1,
                             int((self.app.screen_width-len(self.limit_msg))/2),
                             '< ' + self.limit_msg + ' >', curses.A_DIM | self.c_ttl)

        self.app.stdscr.refresh()
        self.gwin.refresh()

    def fill_main_box_type_selected(self, i):
        if "[Died]" in self.cell2:
            self.gwin.addstr(i + 1 - self.app.row_max*(self.page-1), len(self.cell1),
                             self.cell2, curses.A_BOLD | self.c_di)
        elif "[Alive]" in self.cell2:
            self.gwin.addstr(i + 1 - self.app.row_max*(self.page-1), len(self.cell1),
                             self.cell2, curses.A_BOLD | self.c_al)
        elif "[Connected]" in self.cell2:
            self.gwin.addstr(i + 1 - self.app.row_max*(self.page-1), len(self.cell1),
                             self.cell2, curses.A_BOLD | self.c_co)
        else:
            self.gwin.addstr(i + 1 - self.app.row_max*(self.page-1), len(self.cell1),
                             self.cell2, curses.A_BOLD | self.c_hh)

    def fill_main_box_type(self, i):
        if "[Died]" in self.cell2:
            self.gwin.addstr(i + 1 - self.app.row_max*(self.page-1), len(self.cell1),
                             self.cell2, curses.A_BOLD | self.c_di)
        elif "[Alive]" in self.cell2:
            self.gwin.addstr(i + 1 - self.app.row_max*(self.page-1), len(self.cell1),
                             self.cell2, curses.A_BOLD | self.c_al)
        elif "[Connected]" in self.cell2:
            self.gwin.addstr(i + 1 - self.app.row_max*(self.page-1), len(self.cell1),
                             self.cell2, curses.A_BOLD | self.c_co)
        else:
            self.gwin.addstr(i + 1 - self.app.row_max*(self.page-1), len(self.cell1),
                             self.cell2, curses.A_BOLD | self.c_txt)

    @staticmethod
    def filter_var_lst(lst, filt):
        """ Filter variable list (name|type). """

        filtered = []
        for key in list(lst):
            if filt in lst[key]['type'] or filt in key:
                filtered.append(key)

        return sorted(filtered)

    @staticmethod
    def type_sort(lst):
        """ Sort variable by type. """

        from operator import itemgetter

        types = []
        for key in list(lst):
            types.append([key, lst[key]['type']])

        types.sort(key=itemgetter(1))

        return [item[0] for item in types]

    def arange_lst(self):
        """ Organize/Arange variable list. """

        if self.mk_sort == 'name':
            self.strings = sorted(list(self.lst))

        elif self.mk_sort == 'type':
            self.strings = self.type_sort(self.lst)

        elif self.mk_sort == 'filter' and self.filter:
            self.strings = self.filter_var_lst(self.lst, self.filter)
            if not self.strings:
                self.prompt_msg_setup('{} not found'.format(self.filter))
                self.strings = sorted(list(self.lst))
                self.filter = None
                self.mk_sort = 'name'
            else:
                self.limit_msg = 'Filter : ' + self.filter + ' (' + str(len(self.strings)) + ' obj.)'

        else:
            self.strings = list(self.lst)

        # Update number of columns
        self.row_num = len(self.strings) - 1

    def prompt_msg_display(self):
        """ Erase prompt message after some delay """

        if self.prompt_msg and time.time() - self.prompt_time > 3:
            self.prompt_msg = ''
        else:
            self.prompt.display(self.prompt_msg)

    def prompt_msg_setup(self, msg):
        """ Set up the message to display in the prompt """

        self.prompt_msg = msg
        self.prompt_time = time.time()

    def prompt_cmd(self):
        """ Actions for prompt """

        if not self.cmd:
            pass

        elif self.cmd in ["q", "quit"]:
            self.app.close_signal = 'close'

        elif self.cmd in ["Q", "Quit"]:
            self.app.close_signal = 'shutdown'

        elif self.cmd in ['k', 'K', 'kernel-manager']:
            self.prompt_cmd_kernel_manager()

        elif self.cmd in ['v', 'V', 'e', 'E', 'variable-explorer']:
            self.prompt_cmd_variable_explorer()

        elif self.cmd in ['h', 'help']:
            help_menu = Help(self.app)
            help_menu.display()

        elif self.cmd in ['R', 'daemon-restart']:
            self.daemon_restart()

        elif self.cmd in ['r', 'daemon-restart-connection']:
            self.daemon_restart_connection()

        elif self.cmd in ['c', 'daemon-connect']:
            self.daemon_connect()

        elif self.cmd in ['d', 'daemon-disconnect']:
            self.daemon_disconnect()

        else:
            self.prompt_msg_setup('Command not found !')

    def prompt_cmd_kernel_manager(self):
        """ 'kernel-manager' prompt command"""

        if self.panel_name in ['variable-explorer']:
            self.app.explorer_switch = True
        elif self.panel_name not in ['kernel-manager']:
            self.app.kernel_win.display()
        else:
            self.prompt_msg_setup('Already in kernel manager !')

    def prompt_cmd_variable_explorer(self):
        """ 'variable-explorer' prompt command """

        if self.panel_name in ['kernel-manager']:
            self.app.kernel_switch = True
        elif self.panel_name not in ['variable-explorer']:
            self.app.explorer_win.display()
        else:
            self.prompt_msg_setup('Already in variable explorer !')

    def send_code(self):
        """ Send code to current kernel """

        code = self.prompt.simple('Send-code ')
        if code:
            try:
                send_msg(self.sock.RequestSock, '<code>' + code)
                self.logger.info('Code sent to kernel : {}'.format(code))
                self.prompt_msg_setup('Code sent !')
            except Exception:
                self.logger.error('Code not sent !')
                self.prompt_msg_setup('Code not sent !')

    def search_item(self, txt_msg):
        """ Search an object in the variable list """

        self.search = self.prompt.simple(txt_msg)
        self.search_lst = [i for i, s in enumerate(self.strings) if self.search in s]
        self.search_index = 0
        self.logger.info('Searching for : {} in :\n{}'.format(self.search, self.strings))

        if self.search_lst and self.search:
            if len(self.search_lst) == 1:
                self.prompt_msg_setup("{} occurence of '{}' found".format(len(self.search_lst), self.search))
            else:
                self.prompt_msg_setup("{} occurences of '{}' found".format(len(self.search_lst), self.search))
            self.position = self.search_lst[self.search_index]
            self.page = ceil((self.position+1)/self.app.row_max)
        elif not self.search:
            pass
        else:
            self.prompt_msg_setup(self.search + ' not found !')
            self.position = 0
            self.page = 1

    def search_item_next(self):
        """ Next occurence of the searching. """

        self.search_lst = [i for i, s in enumerate(self.strings) if self.search in s]

        if self.search_lst and self.search_index < len(self.search_lst) - 1:
            self.search_index += 1
        else:
            self.search_index = 0

        self.position = self.search_lst[self.search_index]
        self.page = ceil((self.position+1)/self.app.row_max)

    def daemon_connect(self):
        """ Connect to daemon socket """

        self.sock.init_sockets()
        self.sock.warning_socket(self.wng)

    def daemon_disconnect(self):
        """ Disconnet from daemon socket """

        self.sock.close_sockets()
        self.sock.warning_socket(self.wng)

    def daemon_restart_connection(self):
        """ Restart connection to the daemon socket """

        self.wng.display(' Restarting connection ')
        self.sock.restart_sockets()
        self.sock.warning_socket(self.wng)

    def daemon_restart(self):
        """ Restart kd5 ! """

        restart_daemon()
        self.wng.display(' Restarting Daemon ')
        self.sock.init_sockets()
        self.sock.warning_socket(self.wng)

    def resize_curses(self, force=False):
        """ Check if terminal is resized and adapt screen """

        # Check difference between self.screen_height and self.app.screen_height
        resize = curses.is_term_resized(self.screen_height, self.screen_width)
        min_size_cond = self.app.screen_height >= self.app.term_min_height and self.app.screen_width >= self.app.term_min_width
        if (min_size_cond and resize) or force:
            # new heigh and width of object stdscreen
            self.app.screen_height, self.app.screen_width = self.app.stdscr.getmaxyx()
            # save also these value locally to check if
            self.screen_height, self.screen_width = self.app.stdscr.getmaxyx()
            # Update number of lines
            self.app.panel_height = self.app.screen_height-self.app.debug_info
            self.app.row_max = self.app.panel_height - 2
            # Update display
            self.app.stdscr.clear()
            self.gwin.clear()
            self.gwin.resize(self.app.panel_height, self.app.screen_width)
            curses.resizeterm(self.app.screen_height, self.app.screen_width)
            self.app.stdscr.refresh()
            self.gwin.refresh()

    def navigate_lst(self):
        """ Navigation though the item list"""

        self.pages = ceil((self.row_num + 1)/self.app.row_max)
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
        self.position = self.app.row_max*(self.page-1)

    def navigate_left(self):
        """ Navigate Left. """

        self.page = self.page - 1
        self.position = self.app.row_max*(self.page-1)

    def navigate_up(self):
        """ Navigate Up. """

        if self.page == 1:
            if self.position > 0:
                self.position = self.position - 1
        else:
            if self.position > self.app.row_max*(self.page - 1):
                self.position = self.position - 1
            else:
                self.page = self.page - 1
                self.position = self.app.row_max - 1 + self.app.row_max*(self.page - 1)

    def navigate_down(self):
        """ Navigate Down. """

        # First page
        if self.page == 1:
            if (self.position < self.app.row_max - 1) and (self.position < self.row_num):
                self.position = self.position + 1
            else:
                if self.pages > 1:
                    self.page = self.page + 1
                    self.position = self.app.row_max*(self.page - 1)

        # Last page
        elif self.page == self.pages:
            if self.position < self.row_num:
                self.position = self.position + 1

        # Between
        else:
            if self.position < self.app.row_max - 1 + self.app.row_max*(self.page - 1):
                self.position = self.position + 1
            else:
                self.page = self.page + 1
                self.position = self.app.row_max*(self.page - 1)

    def init_menu(self):
        """ Init the menu """

        self.selected = self.strings[self.position]
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
