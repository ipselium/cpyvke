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
# Last Modified : mar. 03 avril 2018 15:55:45 CEST
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
from cpyvke.curseswin.widgets import Help
from cpyvke.curseswin.prompt import Prompt
from cpyvke.curseswin.app import check_size
from cpyvke.utils.kd import restart_daemon
from cpyvke.utils.display import format_cell
from cpyvke.utils.comm import send_msg

code = locale.getpreferredencoding()


class BasePanel(abc.ABC):
    """ Generic Panel.
    """

    def __init__(self, app, sock, logger):
        """ Class Constructor """

        # Instance arguments
        self.app = app
        self.sock = sock
        self.logger = logger

        # Init constants
        self.resize = False
        self.pkey = -1

        # Init Prompt
        self.prompt = Prompt(self.app)
        self.prompt_time = 0
        self.prompt_msg = ''

        # Update dimensions
        self.screen_height, self.screen_width = self.app.stdscr.getmaxyx()  # Local dimensions

        # Init subwin
        self.gwin = self.app.stdscr.subwin(self.app.panel_height, self.app.screen_width, 0, 0)
        self.gwin.keypad(1)

        # Init Panel
        self.gpan = panel.new_panel(self.gwin)
        self.gpan.hide()

    @property
    @abc.abstractmethod
    def title(self):
        """ Panel title. Must return a string """

    @property
    @abc.abstractmethod
    def panel_name(self):
        """ Panel reference name. Must return a string """

    @abc.abstractmethod
    def color(self, item):
        """ Panel colors. Required :
            * for BasePanel : 'txt', 'bdr', 'ttl', 'hh', 'pwf'
            * for ListPanel : 'co', 'al', 'di'
        """

    @abc.abstractmethod
    def fill_main_box(self):
        """ Fill the main box """

    def display(self):
        """ Display the panel. """

        try:
            self.pkey = -1
            while self.app.close_signal == 'continue':
                self.tasks()
            self.app.shutdown()
        except Exception:
            self.app.exit_with_error()

    @check_size
    def tasks(self):
        """ List of tasks at each iteration """

        self.resize_curses()

        # Check switch panel
        if self.app.explorer_switch:
            self.app.explorer_switch = False
            self.app.kernel_win.display()
            self.resize_curses(True)

        elif self.app.kernel_switch:
            self.app.kernel_switch = False
            self.app.explorer_win.display()
            self.resize_curses(True)

        else:
            # Check Connection to daemon
            self.sock.check_main_socket()

            # Keys
            self.common_key_bindings()

            # Decrease delay right here to avoid some waiting at the getch when not
            # in switch mode. If switch, the halfdelay is set to its normal value
            # just after, in the refresh() method !
            curses.halfdelay(1)

            # Skip end of tasks if switching panel !
            if not self.app.explorer_switch and not self.app.kernel_switch and self.app.close_signal == "continue":

                # Update screen size if another menu break because of resizing
                self.resize_curses()

                # Update all static panels
                self.refresh()

            # Get pressed key (even in case of switch)
            self.pkey = self.app.stdscr.getch()

    def refresh(self):
        """ Refresh all objects. """

        # Erase all windows
        self.gwin.erase()
        self.app.stdscr.erase()

        # Create border before updating fields
        self.gwin.border(0)

        # Fill the main box !
        self.fill_main_box()

        # Update all windows
        if self.app.debug:
            self.app.dbg_pad(self.pkey)

        # Update infos -- Bottom
        self.app.status_bar()
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

        # Debug Pad
        elif self.pkey == 100:      # -> d
            self.toggle_debug()

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

    def list_key_bindings(self):
        """ Not available for BasePanel. See List ListPanel """

        pass

    def custom_key_bindings(self):
        """ Key bindings : To overload """

        pass

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

        elif self.cmd in ['toggle-debug']:
            self.toggle_debug()

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

    def toggle_debug(self):
        """ Display/hide debug informations """

        if self.app.debug:
            self.app.debug = False
        else:
            self.app.debug = True

    def send_code(self):
        """ Send code to current kernel """

        code = self.prompt.simple('Send-code ')
        code, err = self.check_code(code)
        if err:
            self.prompt_msg_setup(err)
        elif code:
            try:
                send_msg(self.sock.RequestSock, '<code>' + code)
                self.logger.info('Code sent to kernel : {}'.format(code))
                self.prompt_msg_setup('Code sent !')
            except Exception:
                self.logger.error('Code not sent !')
                self.prompt_msg_setup('Code not sent !')

    @staticmethod
    def check_code(code):
        """ Check is code is authorized """

        if 'input' in code:
            return '', 'input command is not allowed'
        elif 'reset' in code:
            return 'reset -f', 'Resetting namespace...'
        else:
            return code, None

    def daemon_connect(self):
        """ Connect to daemon socket """

        self.sock.init_sockets()
        self.sock.warning_socket(self.app.wng)

    def daemon_disconnect(self):
        """ Disconnet from daemon socket """

        self.sock.close_sockets()
        self.sock.warning_socket(self.app.wng)

    def daemon_restart_connection(self):
        """ Restart connection to the daemon socket """

        self.app.wng.display(' Restarting connection ')
        self.sock.restart_sockets()
        self.sock.warning_socket(self.app.wng)

    def daemon_restart(self):
        """ Restart kd5 ! """

        restart_daemon()
        self.app.wng.display(' Restarting Daemon ')
        self.sock.init_sockets()
        self.sock.warning_socket(self.app.wng)

    def resize_curses(self, force=False):
        """ Check if terminal is resized and adapt screen """

        # Check difference between self.screen_height and self.app.screen_height
        resize = curses.is_term_resized(self.screen_height, self.screen_width)
        if resize or force:
            # save also these value locally to check if
            self.screen_height, self.screen_width = self.app.stdscr.getmaxyx()
            # Update display
            self.app.stdscr.clear()
            self.gwin.clear()
            self.gwin.resize(self.app.panel_height, self.app.screen_width)
            curses.resizeterm(self.app.screen_height, self.app.screen_width)
            self.app.stdscr.refresh()
            self.gwin.refresh()


class ListPanel(BasePanel):
    """ Generic Panel for lists with menu.
    """

    def __init__(self, app, sock, logger):
        """ Class Constructor """

        super(ListPanel, self).__init__(app, sock, logger)

        # Some variables
        self.filter = None
        self.mk_sort = 'name'
        self.search = None
        self.search_index = 0
        self.search_lst = []
        self.limit_msg = ''
        self.position = 0
        self.page = 1

        # Init variables :
        self.item_dic = {}
        self.item_keys = []

    @property
    @abc.abstractmethod
    def empty(self):
        """ Text for empty list. Must return a string """

        return

    def display(self):
        """ Display the panel. """

        # Init colors
        self.gwin.bkgd(self.color('txt'))
        self.gwin.attrset(self.color('bdr'))

        self.gpan.top()     # Push the panel to the bottom of the stack.
        self.gpan.show()    # Display the panel
        self.gwin.clear()

        # Update size if it has change when panel was hidden
        self.resize_curses(True)

        self.pkey = -1
        while self.pkey not in self.app.kquit and self.app.close_signal == 'continue':

            if self.app.kernel_switch or self.app.explorer_switch:
                break

            self.tasks()

        self.gwin.clear()
        self.gpan.hide()

    def custom_tasks(self):
        """ Supplementary tasks [To overload if needed] """

        pass

    @check_size
    def tasks(self):
        """ List of tasks at each iteration """

        # Listen to resize and adapt Curses
        self.resize_curses()

        # Custom tasks
        self.custom_tasks()

        # Check Connection to daemon
        self.sock.check_main_socket()

        # Get items
        self.item_dic = self.get_items()
        self.row_num = len(self.item_dic) - 1

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

        # Fill the main box !
        self.fill_main_box()

        # Update all windows
        if self.app.debug:
            self.app.dbg_pad(self.pkey, self.search, self.filter, self.mk_sort)

        # Update infos -- Bottom
        self.app.status_bar()
        self.prompt_msg_display()
        self.app.stdscr.refresh()
        self.gwin.refresh()

        # Reactive timeout for getch
        curses.halfdelay(self.app.curse_delay)

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

    def custom_key_bindings(self):
        """ Key bindings : To overload """

        pass

    @abc.abstractmethod
    def get_items(self):
        """ Return a dicionnary with items : self.item_dic """

        return

    def fill_main_box(self):
        """ Update the item list """

        # Title
        if self.app.config['font']['pw-font'] == 'True':
            self.gwin.addstr(0, int((self.app.screen_width-len(self.title))/2),
                             '', self.color('pwf'))
            self.gwin.addstr(self.title, self.color('ttl'))
            self.gwin.addstr('', self.color('pwf'))
        else:
            self.gwin.addstr(0, int((self.app.screen_width-len(self.title))/2),
                             '|' + self.title + '|', self.color('ttl'))

        # Reset position if position is greater than the new list of var (reset)
        self.row_num = len(self.item_keys) - 1
        if self.position > self.row_num:
            self.position = 0
            self.page = 1

        # Items
        for i in range(self.app.row_max*(self.page-1),
                       self.app.row_max + self.app.row_max*(self.page-1)):

            if self.row_num == -1:
                self.gwin.addstr(1, 1, self.empty, self.color('hh'))

            elif i <= self.row_num:
                self.cell1, self.cell2 = format_cell(self.item_dic, self.item_keys[i], self.app.screen_width)
                if i == self.position:
                    self.gwin.addstr(i + 1 - self.app.row_max*(self.page-1), 2,
                                     self.cell1.encode(code), self.color('hh'))
                    self.fill_main_box_type_selected(i)
                else:
                    self.gwin.addstr(i + 1 - self.app.row_max*(self.page-1), 2,
                                     self.cell1.encode(code), curses.A_DIM | self.color('txt'))
                    self.fill_main_box_type(i)

        # Bottom info
        if self.app.config['font']['pw-font'] == 'True' and len(self.limit_msg) > 0:
            self.gwin.addstr(self.app.panel_height-1,
                             int((self.app.screen_width-len(self.limit_msg))/2),
                             '', self.color('pwf'))
            self.gwin.addstr(self.limit_msg, self.color('ttl'))
            self.gwin.addstr('',  self.color('pwf'))
        elif len(self.limit_msg) > 0:
            self.gwin.addstr(self.app.panel_height-1,
                             int((self.app.screen_width-len(self.limit_msg))/2),
                             '< ' + self.limit_msg + ' >', curses.A_DIM | self.color('ttl'))

        self.app.stdscr.refresh()
        self.gwin.refresh()

    def fill_main_box_type_selected(self, i):
        if "[Died]" in self.cell2:
            self.gwin.addstr(i + 1 - self.app.row_max*(self.page-1), len(self.cell1),
                             self.cell2, self.color('di'))
        elif "[Alive]" in self.cell2:
            self.gwin.addstr(i + 1 - self.app.row_max*(self.page-1), len(self.cell1),
                             self.cell2, self.color('al'))
        elif "[Connected]" in self.cell2:
            self.gwin.addstr(i + 1 - self.app.row_max*(self.page-1), len(self.cell1),
                             self.cell2, self.color('co'))
        else:
            self.gwin.addstr(i + 1 - self.app.row_max*(self.page-1), len(self.cell1),
                             self.cell2, self.color('hh'))

    def fill_main_box_type(self, i):
        if "[Died]" in self.cell2:
            self.gwin.addstr(i + 1 - self.app.row_max*(self.page-1), len(self.cell1),
                             self.cell2, self.color('di'))
        elif "[Alive]" in self.cell2:
            self.gwin.addstr(i + 1 - self.app.row_max*(self.page-1), len(self.cell1),
                             self.cell2, self.color('al'))
        elif "[Connected]" in self.cell2:
            self.gwin.addstr(i + 1 - self.app.row_max*(self.page-1), len(self.cell1),
                             self.cell2, self.color('co'))
        else:
            self.gwin.addstr(i + 1 - self.app.row_max*(self.page-1), len(self.cell1),
                             self.cell2, self.color('txt'))

    @staticmethod
    def filter_var_lst(item_dic, filt):
        """ Filter variable list (name|type). """

        filtered = []
        for key in list(item_dic):
            if filt in item_dic[key]['type'] or filt in key:
                filtered.append(key)

        return sorted(filtered)

    @staticmethod
    def type_sort(item_dic):
        """ Sort variable by type. """

        from operator import itemgetter

        types = []
        for key in list(item_dic):
            types.append([key, item_dic[key]['type']])

        types.sort(key=itemgetter(1))

        return [item[0] for item in types]

    def arange_lst(self):
        """ Organize/Arange variable list. """

        if self.mk_sort == 'name':
            self.item_keys = sorted(list(self.item_dic))

        elif self.mk_sort == 'type':
            self.item_keys = self.type_sort(self.item_dic)

        elif self.mk_sort == 'filter' and self.filter:
            self.item_keys = self.filter_var_lst(self.item_dic, self.filter)
            if not self.item_keys:
                self.prompt_msg_setup('{} not found'.format(self.filter))
                self.item_keys = sorted(list(self.item_dic))
                self.filter = None
                self.mk_sort = 'name'
            else:
                self.limit_msg = ' Filter : {} ({} obj.) '.format(self.filter, len(self.item_keys))

        else:
            self.item_keys = list(self.item_dic)

        # Update number of columns
        self.row_num = len(self.item_keys) - 1

    def search_item(self, txt_msg):
        """ Search an object in the variable list """

        self.search = self.prompt.simple(txt_msg)
        self.search_lst = [i for i, s in enumerate(self.item_keys) if self.search in s]
        self.search_index = 0
        self.logger.info('Searching for : {} in :\n{}'.format(self.search, self.item_keys))

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

        self.search_lst = [i for i, s in enumerate(self.item_keys) if self.search in s]

        if self.search_lst and self.search_index < len(self.search_lst) - 1:
            self.search_index += 1
        else:
            self.search_index = 0

        self.position = self.search_lst[self.search_index]
        self.page = ceil((self.position+1)/self.app.row_max)

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

        self.selected = self.item_keys[self.position]

        # Add specific initilization
        self.menu_special_init()

        # Create menu list
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
        self.gwin_menu.bkgd(self.color('txt'))
        self.gwin_menu.attrset(self.color('bdr'))  # Change border color
        self.gwin_menu.keypad(1)

        # Send menu to a panel
        self.gpan_menu = panel.new_panel(self.gwin_menu)
        # Hide the panel. This does not delete the object, it just makes it invisible.
        self.gpan_menu.hide()
        panel.update_panels()

        # Submenu
        self.display_menu()

    def menu_special_init(self):
        """ Additionnal initialization for menu """

        pass

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
            if self.app.config['font']['pw-font'] == 'True':
                self.gwin_menu.addstr(0, self.title_pos, '', self.color('pwf'))
                self.gwin_menu.addstr(self.menu_title, self.color('ttl'))
                self.gwin_menu.addstr('', self.color('pwf'))
            else:
                self.gwin_menu.addstr(0, self.title_pos,
                                      '|' + self.menu_title + '|', self.color('ttl'))

            self.gwin_menu.refresh()

            # Create entries
            for index, item in enumerate(self.menu_lst):
                if index == self.menu_cursor:
                    mode = self.color('hh')
                else:
                    mode = self.color('txt') | curses.A_DIM

                self.gwin_menu.addstr(1+index, 1, item[0], mode)

            # Wait for keyboard event
            menukey = self.gwin_menu.getch()

            if menukey in self.app.kenter:
                eval(self.menu_lst[self.menu_cursor][1])
                break

            elif menukey in self.app.kup:
                self.navigate_menu(-1, len(self.menu_lst))

            elif menukey in self.app.kdown:
                self.navigate_menu(1, len(self.menu_lst))

            if menukey == curses.KEY_RESIZE:
                self.resize = True
                break

        self.gwin_menu.clear()
        self.gpan_menu.hide()

    def navigate_menu(self, n, size):
        """ Navigate through the menu """

        self.menu_cursor += n

        if self.menu_cursor < 0:
            self.menu_cursor = 0
        elif self.menu_cursor >= size:
            self.menu_cursor = size - 1
