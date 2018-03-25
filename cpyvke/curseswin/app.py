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
# Last Modified : dim. 25 mars 2018 09:34:57 CEST
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import os
import time
import psutil
import locale
import traceback
import curses
from curses import panel

from cpyvke.utils.colors import Colors
from cpyvke.utils.comm import send_msg

locale.setlocale(locale.LC_ALL, '')


class InitApp:
    """ Initlication. """

    def __init__(self, kc, cf, config, sock, DEBUG):
        """  """

        self.sock = sock

        # Basics
        self.kc = kc
        self.cf = cf
        self.config = config
        self.DEBUG = DEBUG

        # Init CUI :
        self.close_signal = 'continue'
        self.stdscr = curses.initscr()   # Init curses
        self.stdscr.keypad(1)            #
        self.screen_height, self.screen_width = self.stdscr.getmaxyx()

        # Ressources
        self.ressources = psutil.Process(os.getpid())

        # Curses options
        self.curse_delay = 10            # 1s timer on each getch
        curses.noecho()             # Wont print the input og getch (keys)
        curses.cbreak()             #
        curses.curs_set(0)          #
        # How many tenths of second are waited to refresh screen, from 1 to 255
        curses.halfdelay(self.curse_delay)
        # Init color pairs
        Colors(self.config)
        # Assign color pairs to variables
        self.color_def()
        # Set some colors
        self.stdscr.bkgd(self.c_main_txt)

        # Min terminal size allowed
        if self.DEBUG:
            self.term_min_height = 20
            self.term_min_width = 80
            self.debug_info = 7       # Size of the bottom text area
        else:
            self.term_min_height = 15
            self.term_min_width = 70
            self.debug_info = 2

        # Some variables
        self.panel_height = self.screen_height - self.debug_info
        self.row_max = self.panel_height - 2  # max number of rows
        self.kernel_change = False
        self.explorer_switch = False
        self.kernel_switch = False
        self.var_nb = 0

        # Bindings :
        self.kdown = [curses.KEY_DOWN, 106]
        self.kup = [curses.KEY_UP, 107]
        self.kleft = [curses.KEY_LEFT, 104, 339]
        self.kright = [curses.KEY_RIGHT, 108, 338]
        self.kenter = [curses.KEY_ENTER, ord("\n"), 10, 32]
        self.kquit = [27, 113]

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

    def dbg_socket(self):
        """ Display queue informations """

        self.stdscr.addstr(self.panel_height + 1, int(2*self.screen_width/3),
                           ' Ressources ', self.c_main_ttl | curses.A_BOLD)
        if self.config['font']['pw-font'] == 'True':
            self.stdscr.addstr('', self.c_main_pwf | curses.A_BOLD)
        self.stdscr.addstr(self.panel_height + 2, 2*int(self.screen_width/3) + 1,
                           ' cpu : {} %'.format(self.ressources.cpu_percent()),
                           curses.A_DIM | self.c_main_txt)
        self.stdscr.addstr(self.panel_height + 3, 2*int(self.screen_width/3) + 1,
                           ' memory : {:.2f} %'.format(self.ressources.memory_percent()),
                           curses.A_DIM | self.c_main_txt)
        self.stdscr.addstr(self.panel_height + 4, 2*int(self.screen_width/3) + 1,
                           ' threads : {} '.format(self.ressources.num_threads()),
                           curses.A_DIM | self.c_main_txt)

    def dbg_term(self, pkey):
        """ Display terminal informations """

        self.stdscr.addstr(self.panel_height + 1, int(self.screen_width/3),
                           ' Terminal ', self.c_main_ttl | curses.A_BOLD)
        if self.config['font']['pw-font'] == 'True':
            self.stdscr.addstr('', self.c_main_pwf | curses.A_BOLD)
        self.stdscr.addstr(self.panel_height + 2, int(self.screen_width/3) + 1,
                           ' key : {}'.format(pkey),
                           curses.A_DIM | self.c_main_txt)
        self.stdscr.addstr(self.panel_height + 3, int(self.screen_width/3) + 1,
                           ' size : {}x{}'.format(self.screen_width,
                                                   self.screen_height),
                           curses.A_DIM | self.c_main_txt)
        self.stdscr.addstr(self.panel_height + 4, int(self.screen_width/3) + 1,
                           ' colors : ' + str(curses.COLORS),
                           curses.A_DIM | self.c_main_txt)

    def dbg_general(self, search, filter, mk_sort):
        """ Display debug informations """

        self.stdscr.addstr(self.panel_height + 1, 2, ' Debug ',
                           self.c_main_ttl | curses.A_BOLD)
        if self.config['font']['pw-font'] == 'True':
            self.stdscr.addstr('', self.c_main_pwf | curses.A_BOLD)
        self.stdscr.addstr(self.panel_height + 2, 3, ' search : {}'.format(search),
                           curses.A_DIM | self.c_main_txt)
        self.stdscr.addstr(self.panel_height + 3, 3, ' limit : {}'.format(filter),
                           curses.A_DIM | self.c_main_txt)
        self.stdscr.addstr(self.panel_height + 4, 3, ' sort : {}'.format(mk_sort),
                           curses.A_DIM | self.c_main_txt)

    def check_size(self):
        """ Blank screen and display a warning if size of the terminal is too small. """

        self.stdscr.erase()
        self.screen_height, self.screen_width = self.stdscr.getmaxyx()
        msg_actual = str(self.screen_width) + 'x' + str(self.screen_height)
        msg_limit = 'Win must be > ' + str(self.term_min_width) + 'x' + str(self.term_min_height)
        try:
            self.stdscr.addstr(int(self.screen_height/2),
                               int((self.screen_width-len(msg_limit))/2),
                               msg_limit, self.c_warn_txt | curses.A_BOLD)
            self.stdscr.addstr(int(self.screen_height/2)+1,
                               int((self.screen_width-len(msg_actual))/2),
                               msg_actual, self.c_warn_txt | curses.A_BOLD)
        except Exception:
            self.logger.error('Error : ', exc_info=True)
            pass
        self.stdscr.refresh()

    def bottom_bar_info(self):
        """ Check and display kernel informations """

        debug_info_id = 'kernel ' + self.cf.split('-')[1].split('.')[0] + ' '
        debug_info_obj = str(self.var_nb) + ' obj.'

        # Kernel Info
        if self.config['font']['pw-font'] == 'True':
            self.stdscr.addstr(self.screen_height-2, 0, ' ', self.c_bar_co | curses.A_BOLD)
            self.stdscr.addstr('', self.c_bar_kn_pwfi | curses.A_BOLD)
            self.stdscr.addstr(' Daemon ', self.c_bar_kn)
            self.stdscr.addstr('', self.c_bar_kn_pwfk | curses.A_BOLD)
            if self.sock.connected:
                self.stdscr.addstr(' connected ', self.c_bar_co | curses.A_BOLD)
                self.stdscr.addstr(' ', self.c_bar_kn_pwfc | curses.A_BOLD)
                self.stdscr.addstr(debug_info_id, self.c_bar_kn)
                self.stdscr.addstr(' ', self.c_bar_kn | curses.A_BOLD)
                self.stdscr.addstr(debug_info_obj, self.c_bar_kn)
                self.stdscr.addstr('', self.c_bar_kn_pwf | curses.A_BOLD)
            else:
                self.stdscr.addstr(' disconnected ', self.c_bar_dco | curses.A_BOLD)
                self.stdscr.addstr('', self.c_bar_kn_pwfd | curses.A_BOLD)

        else:
            self.stdscr.addstr(self.screen_height-2, 2, '< Kernel : ',
                               self.c_bar_kn | curses.A_BOLD)
            if self.kc.is_alive():
                self.stdscr.addstr('connected', self.c_bar_co | curses.A_BOLD)
                self.stdscr.addstr(' [' + debug_info_id + debug_info_obj + ']',
                                   self.c_bar_kn | curses.A_BOLD)
            else:
                self.stdscr.addstr('disconnected ', self.c_bar_dco | curses.A_BOLD)
            self.stdscr.addstr(' >', self.c_bar_kn | curses.A_BOLD)

        # Help
        if self.config['font']['pw-font'] == 'True':
            self.stdscr.addstr(self.screen_height-2, self.screen_width-9,
                               '', self.c_bar_hlp_pwf | curses.A_BOLD)
            self.stdscr.addstr(' ?:help ', self.c_bar_hlp | curses.A_BOLD)
        else:
            self.stdscr.addstr(self.screen_height-2, self.screen_width-12,
                               '< h:help >', self.c_bar_hlp | curses.A_BOLD)

    def close_menu(self):
        """ Close Menu """

        # Init Menu
        cmsg = 'Shutdown daemon (default no) ? [y|n|q]'
        cmsg_width = len(cmsg) + 4
        menu_close = self.stdscr.subwin(3, cmsg_width,
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
        self.stdscr.nodelay(False)
        self.pkey = -1
        while self.pkey not in (121, 110, 113, 89, 78, 27, ord("\n")):
            self.pkey = self.stdscr.getch()
            time.sleep(0.5)

        # Erase the panel
        menu_close.clear()
        panel_close.hide()
        self.stdscr.refresh()

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
            send_msg(self.sock.RequestSock, '<_stop>')
            # self.kc.shutdown()

        self.sock.close_sockets()
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
        self.stdscr.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.endwin()
        self.shutdown()
        traceback.print_exc()           # Print the exception
