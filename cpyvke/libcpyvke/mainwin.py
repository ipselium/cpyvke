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
# Last Modified : mar. 13 mars 2018 16:34:27 CET
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import curses
import traceback
from math import ceil
from curses import panel
from time import sleep
import socket
import logging
import locale

from .varmenu import MenuVar
from .kernelwin import KernelWin
from .widgets import WarningMsg, Help
from .colors import Colors
from ..utils.display import format_cell, type_sort, filter_var_lst, whos_to_dic
from ..utils.comm import recv_msg, send_msg
from ..utils.kernel import restart_daemon

locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()
logger = logging.getLogger("cpyvke")


class MainWin:
    """ Main window. """

    def __init__(self, kc, cf, Config, DEBUG=False):
        """ Main window constructor """

        # Basics
        self.kc = kc
        self.cf = cf
        self.curse_delay = 25
        self.Config = Config
        self.DEBUG = DEBUG

        # Init connection to Main and request sockets
        self.init_sockets()

        # Init CUI :
        self.close_signal = 'continue'
        self.stdscreen = curses.initscr()   # Init curses
        self.stdscreen.keypad(1)            #
        self.stdscreen.border(0)            # draw a border around screen
        self.screen_height, self.screen_width = self.stdscreen.getmaxyx()

        # Curses options
        curses.noecho()             # Wont print the input
        curses.cbreak()             #
        curses.curs_set(0)          #
        # How many tenths of second are waited to refresh screen, from 1 to 255
        curses.halfdelay(self.curse_delay)
        # Init color pairs
        Colors(self.Config)
        # Assign color pairs to variables
        self.color_def()
        # Set some colors
        self.stdscreen.bkgd(self.c_main_txt)
        self.stdscreen.attrset(self.c_main_bdr | curses.A_BOLD)  # border color

        # Min terminal size allowed
        if self.DEBUG:
            self.term_min_height = 20
            self.term_min_width = 80
            self.kernel_info = 12       # Size of the bottom text area
        else:
            self.term_min_height = 10
            self.term_min_width = 60
            self.kernel_info = 4

        self.position = 1
        self.page = 1
        self.search = None
        self.filter = None
        self.search_index = 0

        # Various Variables :
        self.VarLst_name = "Variable Explorer"
        self.VarLst_wng = ""
        self.mk_sort = 'name'
        self.variables = {}
        self.connected = False

        # Init Variable Box
        self.row_max = self.screen_height-self.kernel_info  # max number of rows
        # newwin(heigh, width, begin_y, begin_x)
        self.VarLst = curses.newwin(self.row_max+2, self.screen_width-2, 1, 1)
        self.VarLst.bkgd(self.c_exp_txt)
        self.VarLst.attrset(self.c_exp_bdr | curses.A_BOLD)  # border color

    def init_main_socket(self):
        """ Init Main Socket. """

        try:
            hote = "localhost"
            sport = int(self.Config['comm']['s-port'])
            self.MainSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.MainSock.connect((hote, sport))
            self.MainSock.setblocking(0)
            logger.debug('Connected to main socket')
        except Exception:
            logger.error('Connection to stream socket failed : \n', exc_info=True)

    def init_request_socket(self):
        """ Init Request Socket. """

        try:
            hote = "localhost"
            rport = int(self.Config['comm']['r-port'])
            self.RequestSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.RequestSock.connect((hote, rport))
            self.RequestSock.setblocking(0)
            logger.debug('Connected to request socket')
        except Exception:
            logger.error('Connection to stream socket failed : \n', exc_info=True)

    def init_sockets(self):
        """ Init all sockets """

        self.init_main_socket()
        self.init_request_socket()

    def close_main_socket(self):
        """ Close Main socket. """

        try:
            self.MainSock.close()
            logger.debug('Main socket closed')
        except Exception:
            logger.error('Unable to close socket : ', exc_info=True)
            pass

    def close_request_socket(self):
        """ Close Request socket. """

        try:
            self.RequestSock.close()
            logger.debug('Request socket closed')
        except Exception:
            logger.error('Unable to close socket : ', exc_info=True)
            pass

    def close_sockets(self):
        """ Close all sockets """

        self.close_main_socket()
        self.close_request_socket()

    def restart_sockets(self):
        """ Stop then start connection to sockets. """

        self.close_sockets()
        self.init_sockets()

    def check_main_socket(self):
        """ Test if connection to daemon is alive. """

        try:
            send_msg(self.MainSock, '<TEST>')
            self.connected = True
        except OSError:
            self.connected = False

    def warning_socket(self, WngMsg):
        """ Check connection and display warning. """

        self.check_main_socket()
        if self.connected:
            WngMsg.Display('  Connected to socket  ')
        else:
            WngMsg.Display(' Disconnected from socket ')

    def color_def(self):
        """ Definition of all color variables """

        self.c_warn_txt = curses.color_pair(1)
        self.c_warn_bdr = curses.color_pair(2)

        self.c_main_txt = curses.color_pair(11)
        self.c_main_bdr = curses.color_pair(12)
        self.c_main_ttl = curses.color_pair(13)
        self.c_main_hh = curses.color_pair(14)
        self.c_main_pwf = curses.color_pair(15)

        self.c_exp_txt = curses.color_pair(21)
        self.c_exp_bdr = curses.color_pair(22)
        self.c_exp_ttl = curses.color_pair(23)
        self.c_exp_hh = curses.color_pair(24)
        self.c_exp_pwf = curses.color_pair(25)

        self.c_kern_txt = curses.color_pair(31)
        self.c_kern_bdr = curses.color_pair(32)
        self.c_kern_ttl = curses.color_pair(33)
        self.c_kern_hh = curses.color_pair(34)
        self.c_kern_co = curses.color_pair(35)
        self.c_kern_al = curses.color_pair(36)
        self.c_kern_di = curses.color_pair(37)
        self.c_kern_pwf = curses.color_pair(38)

        self.c_bar_kn = curses.color_pair(41)
        self.c_bar_hlp = curses.color_pair(42)
        self.c_bar_co = curses.color_pair(43)
        self.c_bar_dco = curses.color_pair(44)
        self.c_bar_kn_pwf = curses.color_pair(45)
        self.c_bar_hlp_pwf = curses.color_pair(46)
        self.c_bar_kn_pwfi = curses.color_pair(47)
        self.c_bar_kn_pwfk = curses.color_pair(48)
        self.c_bar_kn_pwfc = curses.color_pair(49)
        self.c_bar_kn_pwfd = curses.color_pair(40)

    def run(self):
        """ Run daemon """

        try:
            self.get_vars()    # Init Variables
            self.pkey = -1    # Init pressed Key
            while self.close_signal == 'continue':
                self.update_curses()
            self.shutdown()
        except Exception:
            self.exit_with_error()

    def update_curses(self):
        """ Update Curses """

        # Listen to resize and adapt Curses
        self.resize_curses()

        # Check if size is enough
        if self.screen_height < self.term_min_height or self.screen_width < self.term_min_width:
            self.check_size()
            sleep(0.5)
        else:
            self.tasks()

    def tasks(self):
        """ Tasks to update curses """

        # Check Connection to daemon
        self.check_main_socket()

        # Get variables from daemon
        self.get_vars()

        # Arange variable list
        self.arange_var_lst()

        # Navigate in the variable list window
        self.navigate_var_lst()

        # Keys
        self.key_bindings()

        # Update screen size if another menu break because of resizing
        self.resize_curses()

        # Update all static panels
        self.update_static()

        # Get pressed key
        self.pkey = self.stdscreen.getch()

        # Close menu
        if self.pkey == 113:
                self.close_menu()

    def key_bindings(self):
        """ Key Actions ! """

        # Init Warning Msg
        WngMsg = WarningMsg(self.stdscreen)

        # Menu Variable
        if self.pkey == ord("\n") and self.row_num != 0:
            # First Update VarLst (avoid bug)
            self.VarLst.border(0)
            self.update_var_lst()
            self.stdscreen.refresh()
            self.VarLst.refresh()
            # MenuVar
            var_menu = MenuVar(self)
            if var_menu.is_menu():
                var_menu.display()
            sleep(0.5)

        # Menu Help
        elif self.pkey == 104:    # -> h
            help_menu = Help(self)
            help_menu.Display()

        # Menu KERNEL
        elif self.pkey == 107:    # -> k
            kernel_win = KernelWin(self)
            self.cf, self.kc = kernel_win.display()
            # Reset cursor location
            self.position = 1
            self.page = int(ceil(self.position/self.row_max))

        # Menu Search
        elif self.pkey == 47:    # -> /
            self.search_var(WngMsg)

        # Reconnection to socket
        elif self.pkey == 82:    # -> R
            WngMsg.Display(' Restarting connection ')
            self.restart_sockets()
            self.warning_socket(WngMsg)

        # Disconnect from daemon
        elif self.pkey == 68:    # -> D
            self.close_sockets()
            self.warning_socket(WngMsg)

        # Connect to daemon
        elif self.pkey == 67:     # -> C
            self.init_sockets()
            self.warning_socket(WngMsg)

        # Restart daemon
        elif self.pkey == 18:    # -> c-r
            restart_daemon()
            WngMsg.Display(' Restarting Daemon ')
            self.init_sockets()
            self.warning_socket(WngMsg)

        # Force Update VarLst
        elif self.pkey == 114:   # -> r
            send_msg(self.RequestSock, '<code> ')
            WngMsg.Display('Reloading Variable List...')

    def arange_var_lst(self):
        """ Organize/Arange variable list. """

        if self.mk_sort == 'name':
            self.strings = sorted(list(self.variables))

        elif self.mk_sort == 'type':
            self.strings = type_sort(self.variables)

        elif self.mk_sort == 'filter':
            self.strings = filter_var_lst(self.variables, self.filter)
            self.VarLst_wng = 'Filter : ' + self.filter + ' (' + str(len(self.strings)) + ' obj.)'

        # Sort variable by name/type
        if self.pkey == 115:
            if self.mk_sort == 'name':    # -> s
                self.mk_sort = 'type'
            elif self.mk_sort == 'type':
                self.mk_sort = 'name'

        # Filter variables
        if self.pkey == 108:    # -> l
            self.filter_var()
            self.mk_sort = 'filter'
            self.position = 1
            self.page = int(ceil(self.position/self.row_max))

        # Reinit
        if self.pkey == 117:
            self.mk_sort = 'name'
            self.VarLst_wng = ''
            self.position = 1
            self.page = int(ceil(self.position/self.row_max))

        # Update number of columns
        self.row_num = len(self.strings)

    def filter_var(self):
        """ Apply filter for the variable list"""

        # Init Menu
        menu_filter = self.stdscreen.subwin(self.row_max+2, self.screen_width-2, 1, 1)
        menu_filter.keypad(1)

        # Send menu to a panel
        panel_filter = panel.new_panel(menu_filter)

        panel_filter.top()        # Push the panel to the bottom of the stack.
        panel_filter.show()       # Display the panel (which might have been hidden)
        menu_filter.clear()
        menu_filter.bkgd(self.c_exp_txt)
        menu_filter.attrset(self.c_exp_bdr | curses.A_BOLD)  # Change border color
        menu_filter.border(0)
        if self.Config['font']['pw-font'] == 'True':
            menu_filter.addstr(0, int((self.screen_width-len(self.VarLst_name))/2), '', self.c_exp_pwf)
            menu_filter.addstr(self.VarLst_name, self.c_exp_ttl | curses.A_BOLD)
            menu_filter.addstr('', self.c_exp_pwf)
        else:
            menu_filter.addstr(0, int((self.screen_width-len(self.VarLst_name))/2),
                               '| ' + self.VarLst_name + ' |', self.c_exp_ttl | curses.A_BOLD)

        curses.echo()
        menu_filter.addstr(2, 3, "Filter :", curses.A_BOLD | self.c_exp_txt)
        self.filter = menu_filter.getstr(2, 14, 20).decode('utf-8')
        curses.noecho()

        panel_filter.hide()
        curses.halfdelay(self.curse_delay)  # Relaunch autorefresh !

    def search_var(self, WngMsg):
        """ Search an object in the variable list"""

        # Init Menu
        menu_search = self.stdscreen.subwin(self.row_max+2, self.screen_width-2, 1, 1)
        menu_search.keypad(1)

        # Send menu to a panel
        panel_search = panel.new_panel(menu_search)

        panel_search.top()        # Push the panel to the bottom of the stack.
        panel_search.show()       # Display the panel (which might have been hidden)
        menu_search.clear()
        menu_search.bkgd(self.c_exp_txt)
        menu_search.attrset(self.c_exp_bdr | curses.A_BOLD)  # Change border color
        menu_search.border(0)
        if self.Config['font']['pw-font'] == 'True':
            menu_search.addstr(0, int((self.screen_width-len(self.VarLst_name))/2),
                               '', self.c_exp_pwf)
            menu_search.addstr(self.VarLst_name, self.c_exp_ttl | curses.A_BOLD)
            menu_search.addstr('', self.c_exp_pwf)
        else:
            menu_search.addstr(0, int((self.screen_width-len(self.VarLst_name))/2),
                               '| ' + self.VarLst_name + ' |', self.c_exp_ttl | curses.A_BOLD)

        curses.echo()
        menu_search.addstr(2, 3, "Search Variable :", curses.A_BOLD | self.c_exp_txt)
        self.search = menu_search.getstr(2, 21, 20).decode('utf-8')
        curses.noecho()

        panel_search.hide()
        curses.halfdelay(self.curse_delay)  # Relaunch autorefresh !

        try:
            logger.info('Searching for : {} in :\n{}'.format(self.search, self.strings))
            self.search_index = min([i for i, s in enumerate(self.strings) if self.search in s])
        except ValueError:
            WngMsg.Display('Variable ' + self.search + ' not in kernel')
            pass
        else:
            self.position = self.search_index + 1
            self.page = int(ceil(self.position/self.row_max))

    def update_static(self):
        """ Update all static windows. """

        # Erase all windows
        self.VarLst.erase()
        self.stdscreen.erase()

        # Create border before updating fields
        self.stdscreen.border(0)
        self.VarLst.border(0)

        # Update all windows (virtually)
        if self.DEBUG:
            self.dbg_socket()         # Display infos about the process
            self.dbg_term()         # Display infos about the process
            self.dbg_general()        # Display debug infos

        self.update_var_lst()     # Update variables list

        # Update display
        self.bottom_bar_info()      # Display infos about kernel at bottom
        self.stdscreen.refresh()
        self.VarLst.refresh()

    def update_var_lst(self):
        """ Update the list of variables display """

        # Title
        if self.Config['font']['pw-font'] == 'True':
            self.VarLst.addstr(0, int((self.screen_width-len(self.VarLst_name))/2),
                               '', self.c_exp_pwf | curses.A_BOLD)
            self.VarLst.addstr(self.VarLst_name, self.c_exp_ttl | curses.A_BOLD)
            self.VarLst.addstr('', self.c_exp_pwf | curses.A_BOLD)
        else:
            self.VarLst.addstr(0, int((self.screen_width-len(self.VarLst_name))/2),
                               '| ' + self.VarLst_name + ' |', self.c_exp_ttl | curses.A_BOLD)

        # Reset position if position is greater than the new list of var (reset)
        self.row_num = len(self.strings)
        if self.position > self.row_num:
            self.position = 1
            self.page = 1

        # VarLst
        for i in range(1+(self.row_max*(self.page-1)), self.row_max+1 + (self.row_max*(self.page-1))):

            if self.row_num == 0:
                self.VarLst.addstr(1, 1, "No Variable in kernel", self.c_exp_hh)

            else:
                cell = format_cell(self.variables, self.strings[i-1], self.screen_width)
                if (i+(self.row_max*(self.page-1)) == self.position+(self.row_max*(self.page-1))):
                    self.VarLst.addstr(i-(self.row_max*(self.page-1)), 2,
                                       cell.encode(code), self.c_exp_hh)
                else:
                    self.VarLst.addstr(i-(self.row_max*(self.page-1)), 2,
                                       cell.encode(code), curses.A_DIM | self.c_exp_txt)
                if i == self.row_num:
                    break

        # Bottom info
        if self.Config['font']['pw-font'] == 'True' and len(self.VarLst_wng) > 0:
            self.VarLst.addstr(self.row_max+1, int((self.screen_width-len(self.VarLst_wng))/2), '', self.c_exp_pwf)
            self.VarLst.addstr(self.VarLst_wng, self.c_exp_ttl | curses.A_BOLD)
            self.VarLst.addstr('',  self.c_exp_pwf | curses.A_BOLD)
        elif len(self.VarLst_wng) > 0:
            self.VarLst.addstr(self.row_max+1,
                               int((self.screen_width-len(self.VarLst_wng))/2),
                               '< ' + self.VarLst_wng + ' >', curses.A_DIM | self.c_exp_ttl)

    def navigate_var_lst(self):
        """ Navigation though the variable list"""

        self.pages = int(ceil(self.row_num/self.row_max))
        if self.pkey == curses.KEY_DOWN:
            self.navigate_down()
        if self.pkey == curses.KEY_UP:
            self.navigate_up()
        if self.pkey in (curses.KEY_LEFT, 339):
            self.navigate_left()
        if self.pkey in (curses.KEY_RIGHT, 338):
            self.navigate_right()
        if self.pkey == 262:
            self.position = 1
            self.page = 1
        if self.pkey == 360:
            self.position = self.row_num
            self.page = self.pages

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
                self.position = self.row_max + (self.row_max*(self.page-1))

    def navigate_down(self):
        """ Navigate Down. """

        if self.page == 1:
            if (self.position < self.row_max) and (self.position < self.row_num):
                self.position = self.position + 1
            else:
                if self.pages > 1:
                    self.page = self.page + 1
                    self.position = 1 + (self.row_max*(self.page-1))
        elif self.page == self.pages:
            if self.position < self.row_num:
                self.position = self.position + 1
        else:
            if self.position < self.row_max + (self.row_max*(self.page-1)):
                self.position = self.position + 1
            else:
                self.page = self.page + 1
                self.position = 1 + (self.row_max * (self.page-1))

    def navigate_left(self):
        """ Navigate Left. """

        if self.page > 1:
            self.page = self.page - 1
            self.position = 1 + (self.row_max*(self.page-1))

    def navigate_right(self):
        """ Navigate Right. """

        if self.page < self.pages:
            self.page = self.page + 1
            self.position = (1+(self.row_max*(self.page-1)))

    def get_vars(self):
        """ Get variable from the daemon """

        try:
            tmp = recv_msg(self.MainSock).decode('utf8')
        except BlockingIOError:     # If no message !
            pass
        except OSError:             # If user disconnect cpyvke from socket
            pass
        except AttributeError:      # If kd5 is stopped
            pass
        else:
            if tmp:
                self.variables = whos_to_dic(tmp)
                logger.info('Variable list updated')
                logger.debug('\n%s', tmp)
                try:
                    # remove temporary file used by daemon from the list
                    del self.variables['fcpyvke0']
                except KeyError:
                    pass

    def resize_curses(self):
        """ Check if terminal is resized and adapt screen """

        resize = curses.is_term_resized(self.screen_height, self.screen_width)
        if resize is True and self.screen_height >= self.term_min_height and self.screen_width >= self.term_min_width:
            self.screen_height, self.screen_width = self.stdscreen.getmaxyx()  # new heigh and width of object stdscreen
            self.row_max = self.screen_height-self.kernel_info
            self.stdscreen.clear()
            self.VarLst.clear()
            self.VarLst.resize(self.row_max+2, self.screen_width-2)
            curses.resizeterm(self.screen_height, self.screen_width)
            self.stdscreen.refresh()
            self.VarLst.refresh()

    def check_size(self):
        """ Blank screen and display a warning if size of the terminal is too small. """

        self.stdscreen.erase()
        self.screen_height, self.screen_width = self.stdscreen.getmaxyx()
        msg_actual = str(self.screen_width) + 'x' + str(self.screen_height)
        msg_limit = 'Win must be > ' + str(self.term_min_width) + 'x' + str(self.term_min_height)
        try:
            self.stdscreen.addstr(int(self.screen_height/2),
                                  int((self.screen_width-len(msg_limit))/2),
                                  msg_limit, self.c_warn_txt | curses.A_BOLD)
            self.stdscreen.addstr(int(self.screen_height/2)+1,
                                  int((self.screen_width-len(msg_actual))/2),
                                  msg_actual, self.c_warn_txt | curses.A_BOLD)
        except Exception:
            logger.error('Error : ', exc_info=True)
            pass
        self.stdscreen.border(0)
        self.stdscreen.refresh()

    def bottom_bar_info(self):
        """ Check and display kernel informations """

        kernel_info_id = 'kernel ' + self.cf.split('-')[1].split('.')[0] + ' '
        kernel_info_obj = str(len(list(self.variables))) + ' obj.'

        # Kernel Info
        if self.Config['font']['pw-font'] == 'True':
            self.stdscreen.addstr(self.screen_height-1, 2, '', self.c_bar_kn_pwfi | curses.A_BOLD)
            self.stdscreen.addstr(' Daemon ', self.c_bar_kn)
            self.stdscreen.addstr('', self.c_bar_kn_pwfk | curses.A_BOLD)
            if self.connected:
                self.stdscreen.addstr(' connected ', self.c_bar_co | curses.A_BOLD)
                self.stdscreen.addstr(' ', self.c_bar_kn_pwfc | curses.A_BOLD)
                self.stdscreen.addstr(kernel_info_id, self.c_bar_kn)
                self.stdscreen.addstr(' ', self.c_bar_kn | curses.A_BOLD)
                self.stdscreen.addstr(kernel_info_obj, self.c_bar_kn)
                self.stdscreen.addstr('', self.c_bar_kn_pwf | curses.A_BOLD)
            else:
                self.stdscreen.addstr(' disconnected ', self.c_bar_dco | curses.A_BOLD)
                self.stdscreen.addstr('', self.c_bar_kn_pwfd | curses.A_BOLD)

        else:
            self.stdscreen.addstr(self.screen_height-1, 2, '< Kernel : ', self.c_bar_kn | curses.A_BOLD)
            if self.kc.is_alive():
                self.stdscreen.addstr('connected', self.c_bar_co | curses.A_BOLD)
                self.stdscreen.addstr(' [' + kernel_info_id + kernel_info_obj + ']', self.c_bar_kn | curses.A_BOLD)
            else:
                self.stdscreen.addstr('disconnected ', self.c_bar_dco | curses.A_BOLD)
            self.stdscreen.addstr(' >', self.c_bar_kn | curses.A_BOLD)

        # Help
        if self.Config['font']['pw-font'] == 'True':
            self.stdscreen.addstr(self.screen_height-1, self.screen_width-12,
                                  '', self.c_bar_hlp_pwf | curses.A_BOLD)
            self.stdscreen.addstr(' h:help ', self.c_bar_hlp | curses.A_BOLD)
            self.stdscreen.addstr('', self.c_bar_hlp_pwf | curses.A_BOLD)
        else:
            self.stdscreen.addstr(self.screen_height-1, self.screen_width-12,
                                  '< h:help >', self.c_bar_hlp | curses.A_BOLD)

    def dbg_socket(self):
        """ Display queue informations """

        self.stdscreen.addstr(self.row_max + 4, int(2*self.screen_width/3),
                              ' Socket ', self.c_main_ttl | curses.A_BOLD)
        if self.Config['font']['pw-font'] == 'True':
            self.stdscreen.addstr('', self.c_main_pwf | curses.A_BOLD)

    def dbg_term(self):
        """ Display terminal informations """

        self.stdscreen.addstr(self.row_max + 4, int(self.screen_width/3),
                              ' Terminal ', self.c_main_ttl | curses.A_BOLD)
        if self.Config['font']['pw-font'] == 'True':
            self.stdscreen.addstr('', self.c_main_pwf | curses.A_BOLD)
        self.stdscreen.addstr(self.row_max + 5, int(self.screen_width/3) + 1,
                              ' width : ' + str(self.screen_width),
                              curses.A_DIM | self.c_main_txt)
        self.stdscreen.addstr(self.row_max + 6, int(self.screen_width/3) + 1,
                              ' heigh : ' + str(self.screen_height),
                              curses.A_DIM | self.c_main_txt)
        self.stdscreen.addstr(self.row_max + 7, int(self.screen_width/3) + 1,
                              ' color : ' + str(curses.COLORS),
                              curses.A_DIM | self.c_main_txt)

    def dbg_general(self):
        """ Display debug informations """

        self.stdscreen.addstr(self.row_max + 4, 2, ' Debug ', self.c_main_ttl | curses.A_BOLD)
        if self.Config['font']['pw-font'] == 'True':
            self.stdscreen.addstr('', self.c_main_pwf | curses.A_BOLD)
        self.stdscreen.addstr(self.row_max + 5, 3, ' key : ' + str(self.pkey), curses.A_DIM | self.c_main_txt)
        self.stdscreen.addstr(self.row_max + 6, 3, ' search : ' + str(self.search), curses.A_DIM | self.c_main_txt)
        self.stdscreen.addstr(self.row_max + 7, 3, ' limit : ' + str(self.filter), curses.A_DIM | self.c_main_txt)
        self.stdscreen.addstr(self.row_max + 8, 3, ' sort : ' + str(self.mk_sort), curses.A_DIM | self.c_main_txt)

    def close_menu(self):
        """ Close Menu """

        # Init Menu
        cmsg = 'Shutdown daemon (default no) ? [y|n|q]'
        cmsg_width = len(cmsg) + 4
        menu_close = self.stdscreen.subwin(3, cmsg_width,
                                           int(self.screen_height/2),
                                           int((self.screen_width-cmsg_width)/2))
        menu_close.bkgd(self.c_warn_txt)
        menu_close.attrset(self.c_warn_bdr | curses.A_BOLD)  # Change border color
        menu_close.border(0)
        menu_close.keypad(1)

        # Send menu to a panel
        panel_close = panel.new_panel(menu_close)
        panel_close.top()        # Push the panel to the bottom of the stack.

        menu_close.addstr(1, 2, cmsg, curses.A_BOLD | self.c_warn_txt)
        panel_close.show()       # Display the panel (which might have been hidden)
        menu_close.refresh()

        # Wait for yes or no
        self.stdscreen.nodelay(False)
        self.pkey = -1
        while self.pkey not in (121, 110, 113, 89, 78, 27, ord("\n")):
            self.pkey = self.stdscreen.getch()
            sleep(0.5)

        # Erase the panel
        menu_close.clear()
        panel_close.hide()
        self.stdscreen.refresh()

        if self.pkey in (110, 78, ord("\n")):
            self.close_signal = 'close'
        elif self.pkey in (121, 89):
            self.close_signal = 'shutdown'
        elif self.pkey in (113, 27):  # escape this menu
            self.close_signal = 'continue'

    def shutdown(self):
        """ Shutdown CUI, Daemon, and kernel """

        curses.endwin()

        if self.close_signal == 'close':
            print('Exiting ! Closing cpyvke...')
        elif self.close_signal == 'shutdown':
            print('Exiting ! Shutting down daemon...')
            send_msg(self.RequestSock, '<_stop>')
            # self.kc.shutdown()

        self.close_sockets()
        self.kill_all_figs()   # Stop all figure subprocesses

    def kill_all_figs(self):
        """ Kill all figures (running in different processes) """

        import multiprocessing

        if len(multiprocessing.active_children()) == 1:
            print('{} figure killed'.format(len(multiprocessing.active_children())))
        elif len(multiprocessing.active_children()) > 1:
            print('{} figures killed'.format(len(multiprocessing.active_children())))

        for child in multiprocessing.active_children():
            child.terminate()

    def exit_with_error(self):
        """ If error, send terminate signal to daemon and resore terminal to
            sane state """

        self.close_signal = 'close'
        self.stdscreen.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.endwin()
        self.shutdown()
        traceback.print_exc()           # Print the exception
