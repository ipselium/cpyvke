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
# Last Modified : lun. 09 avril 2018 22:51:37 CEST
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

from cpyvke.utils.colors import Colors
from cpyvke.utils.comm import send_msg
from cpyvke.utils.display import str_reduce

locale.setlocale(locale.LC_ALL, '')


def check_size(function):
    """ Decorator to check size of the curses window.
    Blank screen and display a warning if size of the terminal is too small."""

    def wrapper(*args, **kwargs):

        # Fetch self instance which is 1st element of args
        app = args[0].app

        # Min terminal size allowed
        term_min_height = 15
        term_min_width = 70

        # Blank screen if dimension are too small
        if app.screen_height < term_min_height or app.screen_width < term_min_width:
            # Messages
            msg_actual = '{}x{}'.format(app.screen_width, app.screen_height)
            msg_limit = 'Win must be > {}x{}'.format(term_min_width, term_min_height)
            # Message locations
            y_mid = int(app.screen_height/2)
            x_mid_limit = int((app.screen_width-len(msg_limit))/2)
            x_mid_actual = int((app.screen_width-len(msg_actual))/2)
            # Update curses
            app.stdscr.erase()
            try:
                app.stdscr.addstr(y_mid, x_mid_limit, msg_limit, app.c_warn_txt | curses.A_BOLD)
                app.stdscr.addstr(y_mid+1, x_mid_actual, msg_actual, app.c_warn_txt | curses.A_BOLD)
            except curses.error:
                pass
            app.stdscr.refresh()
            time.sleep(0.2)
        else:
            function(*args, **kwargs)

    return wrapper


class InitApp:
    """ Initlication. """

    def __init__(self, kc, cf, config, sock):
        """  """

        # Arguments
        self.kc = kc
        self.cf = cf
        self.config = config
        self.sock = sock

        # Init CUI :
        self.close_signal = 'continue'
        self.stdscr = curses.initscr()   # Init curses

        # Ressources
        self.ressources = psutil.Process(os.getpid())

        # Curses options
        self.stdscr.keypad(1)            #
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

        # Some variables
        self.debug = False
        self.kernel_change = False
        self.explorer_switch = False
        self.kernel_switch = False
        self.var_nb = 0

    @property
    def screen_width(self):
        _, screen_width = self.stdscr.getmaxyx()
        return screen_width

    @property
    def screen_height(self):
        screen_height, _ = self.stdscr.getmaxyx()
        return screen_height

    @property
    def panel_height(self):
        return self.screen_height - 2

    @property
    def row_max(self):
        return self.panel_height - 2

    @property
    def kdown(self):
        """ Down keys """
        return [curses.KEY_DOWN, 258, 106]

    @property
    def kup(self):
        """ Up keys """
        return [curses.KEY_UP, 259, 107]

    @property
    def kleft(self):
        """ Left keys """
        return [curses.KEY_LEFT, 260, 104, 339]

    @property
    def kright(self):
        """ Right keys """
        return [curses.KEY_RIGHT, 261, 108, 338]

    @property
    def kenter(self):
        """ Enter keys """
        return [curses.KEY_ENTER, ord("\n"), 10, 32]

    @property
    def kquit(self):
        """ quit keys """
        return [27, 113]

    def color_def(self):
        """ Definition of all color variables """

        self.c_warn_txt = curses.color_pair(1)
        self.c_warn_bdr = curses.color_pair(2)

        self.c_main_txt = curses.color_pair(11)
        self.c_main_bdr = curses.color_pair(12)
        self.c_main_ttl = curses.color_pair(13)
        self.c_main_hh = curses.color_pair(14)
        self.c_main_pwf = curses.color_pair(15)
        self.c_main_asc = curses.color_pair(16)

        self.c_exp_txt = curses.color_pair(21)
        self.c_exp_bdr = curses.color_pair(22)
        self.c_exp_ttl = curses.color_pair(23)
        self.c_exp_hh = curses.color_pair(24)
        self.c_exp_pwf = curses.color_pair(25)

        self.c_kern_txt = curses.color_pair(31)
        self.c_kern_bdr = curses.color_pair(32)
        self.c_kern_ttl = curses.color_pair(33)
        self.c_kern_hh = curses.color_pair(34)
        self.c_kern_pwf = curses.color_pair(38)

        self.c_kern_co = curses.color_pair(35)
        self.c_kern_al = curses.color_pair(36)
        self.c_kern_di = curses.color_pair(37)

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

    def dbg_pad(self, pkey, search=None, filt=None, mk_sort=None):
        """ Display debug informations """

        pad_width = 19

        lst = [' cpu: {}%'.format(self.ressources.cpu_percent()),
               ' mem: {:.2f}%'.format(self.ressources.memory_percent()),
               ' size : {}x{}'.format(self.screen_width, self.screen_height),
               ' colors : {}'.format(curses.COLORS),
               ' key : {}'.format(pkey),
               ' sort : {}'.format(mk_sort),
               str_reduce(' search : {}'.format(search), pad_width - 3),
               str_reduce(' limit : {}'.format(filt), pad_width - 3)]

        # Init Menu
        pad_height = len(lst) + 2
        pad = self.stdscr.subwin(pad_height, pad_width, 2, int((self.screen_width-pad_width+1)/2))
        pad.attrset(self.c_warn_bdr | curses.A_BOLD)    # change border color
        pad.keypad(1)
        pad.clear()
        pad.border(0)

        # Fill pad
        for idx, item in enumerate(lst):
            if 'None' not in item:
                pad.addstr(idx + 1, 2, item, curses.A_DIM | self.c_main_txt)

        pad.refresh()

    def status_bar(self):
        """ Check and display kernel informations """

        debug_info_id = 'kernel {} '.format(self.cf.split('-')[1].split('.')[0])
        debug_info_obj = '{} obj.'.format(self.var_nb)

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
            self.stdscr.addstr(self.screen_height-2, 0, '< Kernel : ',
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
            self.stdscr.addstr(self.screen_height-2, self.screen_width-10,
                               '< ?:help >', self.c_bar_hlp | curses.A_BOLD)

    def shutdown(self):
        """ Shutdown CUI, Daemon, and kernel """

        curses.endwin()

        if self.close_signal == 'close':
            print('Exiting ! Closing cpyvke...')
        elif self.close_signal == 'shutdown':
            print('Exiting ! Shutting down daemon...')
            send_msg(self.sock.RequestSock, '<_stop>')

        self.kc.stop_channels()
        self.sock.close_sockets()
        self.kill_all_figs()   # Stop all figure subprocesses

    @staticmethod
    def kill_all_figs():
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
