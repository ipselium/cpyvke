#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : cmain.py
# Creation Date : Wed Nov  9 10:03:04 2016
# Last Modified : lun. 05 mars 2018 12:25:13 CET
# Created By : Cyril Desjouy
#
# Copyright © 2016-2017 Cyril Desjouy <ipselium@free.fr>
# Distributed under terms of the BSD license.
"""

DESCRIPTION

@author: Cyril Desjouy
"""

from __future__ import division  # You don't need this in Python3
from builtins import object
import argparse
import curses
import traceback
from math import ceil
from curses import panel
from time import sleep
from jupyter_client import find_connection_file
import sys
import os
import socket
import logging
from logging.handlers import RotatingFileHandler
import locale

from .cvar import MenuVar
from .ckernel import MenuKernel
from .cwidgets import WarningMsg, Help
from .ctools import FormatCell, TypeSort, FilterVarLst
from .ktools import connect_kernel, print_kernel_list
from .stools import WhoToDict, recv_msg, send_msg
from .config import cfg_setup


locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()
logger = logging.getLogger("cpyvke")


class MainWin(object):
    ''' Main window. '''

    def __init__(self, kc, cf, Config, DEBUG=False):

        self.kc = kc
        self.cf = cf
        self.curse_delay = 10
        self.Config = Config
        self.DEBUG = DEBUG

        # Init connection to Main Socket
        self.InitMainSocket()

        # Init connection to Main Socket
        self.InitRequestSocket()

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
        curses.halfdelay(self.curse_delay)         # How many tenths of a second are waited to refresh stdscreen, from 1 to 255

        # Colors
        self.InitColors()
        self.ColorDef()
        self.stdscreen.bkgd(self.c_main_txt)
        self.stdscreen.attrset(self.c_main_bdr | curses.A_BOLD)  # Change border color

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
        self.VarLst = curses.newwin(self.row_max+2, self.screen_width-2, 1, 1)  # (heigh, width, begin_y, begin_x)
        self.VarLst.bkgd(self.c_exp_txt)
        self.VarLst.attrset(self.c_exp_bdr | curses.A_BOLD)  # Change border color

    def CloseMainSocket(self):
        ''' Close Main socket. '''

        try:
            self.MainSock.close()
            logger.debug('Main socket closed')
        except Exception as err:
            logger.debug('Impossible to close socket : {}'.format(err))
            pass

    def CloseRequestSocket(self):
        ''' Close Request socket. '''

        try:
            self.RequestSock.close()
            logger.debug('Request socket closed')
        except Exception as err:
            logger.debug('Impossible to close socket : {}'.format(err))
            pass

    def InitMainSocket(self):
        ''' Init Main Socket. '''

        try:
            hote = "localhost"
            sport = int(self.Config['comm']['s-port'])
            self.MainSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.MainSock.connect((hote, sport))
            self.MainSock.setblocking(0)
            logger.debug('Connected to main socket')
        except Exception as err:
            logger.error('Connection to stream socket failed :\n{}'.format(err))

    def InitRequestSocket(self):
        ''' Init Request Socket. '''

        try:
            hote = "localhost"
            rport = int(self.Config['comm']['r-port'])
            self.RequestSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.RequestSock.connect((hote, rport))
            self.RequestSock.setblocking(0)
            logger.debug('Connected to request socket')
        except Exception as err:
            logger.error('Connection to stream socket failed : {}'.format(err))

    def RestartSocketConnection(self):
        ''' Stop then start connection to sockets. '''

        Wmsg = WarningMsg(self.stdscreen)
        Wmsg.Display(' Restarting connection ')
        self.CloseMainSocket()
        self.CloseRequestSocket()
        self.InitMainSocket()
        self.InitRequestSocket()

    def WngSock(self):
        ''' Check connection and display warning. '''

        Wmsg = WarningMsg(self.stdscreen)
        self.CheckSocket()
        if self.connected:
            Wmsg.Display('  Connected to socket  ')
        else:
            Wmsg.Display(' Disconnected from socket ')

    def EvalColor(self, color):
        ''' Check if a color is set to transparent. '''

        if color == 'transparent':
            curses.use_default_colors()
            return -1
        elif color.isdigit():
            if curses.COLORS > 8:
                return int(color)
            else:
                logger.error('TERM accept only 8 colors')
                return eval('curses.COLOR_UNDEFINED')
        else:
            return eval('curses.COLOR_' + color.upper())

    def InitColors(self):
        ''' Initialize colors. '''

        curses.start_color()        #
        curses.setupterm()

        # Define warning color
        wgtxt = self.Config['wg']['txt'].replace(' ', '').split(',')
        wgbdr = self.Config['wg']['bdr'].replace(' ', '').split(',')
        try:
            wgtxt_fg = self.EvalColor(wgtxt[0])
            wgtxt_bg = self.EvalColor(wgtxt[1])
            wgbdr_fg = self.EvalColor(wgbdr[0])
            wgbdr_bg = self.EvalColor(wgbdr[1])
        except Exception as err:
            wgtxt_fg = curses.COLOR_RED
            wgtxt_bg = -1
            wgbdr_fg = curses.COLOR_RED
            wgbdr_bg = -1
            logger.error('%s', err)

        # Define bar color
        brkn = self.Config['br']['kn'].replace(' ', '').split(',')
        brhlp = self.Config['br']['hlp'].replace(' ', '').split(',')
        brco = self.Config['br']['co'].replace(' ', '').split(',')
        brdco = self.Config['br']['dco'].replace(' ', '').split(',')
        try:
            brkn_fg = self.EvalColor(brkn[0])
            brkn_bg = self.EvalColor(brkn[1])
            brhlp_fg = self.EvalColor(brhlp[0])
            brhlp_bg = self.EvalColor(brhlp[1])
            brco_fg = self.EvalColor(brco[0])
            brco_bg = self.EvalColor(brco[1])
            brdco_fg = self.EvalColor(brdco[0])
            brdco_bg = self.EvalColor(brdco[1])
        except Exception as err:
            brkn_fg = curses.COLOR_WHITE
            brkn_bg = -1
            brhlp_fg = curses.COLOR_WHITE
            brhlp_bg = -1
            brco_fg = curses.COLOR_GREEN
            brco_bg = -1
            brdco_fg = curses.COLOR_RED
            brdco_bg = -1
            logger.error('%s', err)

        # Define explorer color
        xptxt = self.Config['xp']['txt'].replace(' ', '').split(',')
        xpbdr = self.Config['xp']['bdr'].replace(' ', '').split(',')
        xpttl = self.Config['xp']['ttl'].replace(' ', '').split(',')
        xphh = self.Config['xp']['hh'].replace(' ', '').split(',')
        try:
            xptxt_fg = self.EvalColor(xptxt[0])
            xptxt_bg = self.EvalColor(xptxt[1])
            xpbdr_fg = self.EvalColor(xpbdr[0])
            xpbdr_bg = self.EvalColor(xpbdr[1])
            xpttl_fg = self.EvalColor(xpttl[0])
            xpttl_bg = self.EvalColor(xpttl[1])
            xphh_fg = self.EvalColor(xphh[0])
            xphh_bg = self.EvalColor(xphh[1])
        except Exception as err:
            xptxt_fg = curses.COLOR_WHITE
            xptxt_bg = -1
            xpbdr_fg = curses.COLOR_CYAN
            xpbdr_bg = -1
            xpttl_fg = curses.COLOR_CYAN
            xpttl_bg = -1
            xphh_fg = curses.COLOR_BLACK
            xphh_bg = curses.COLOR_CYAN
            logger.error('%s', err)

        # Define main color
        mntxt = self.Config['mn']['txt'].replace(' ', '').split(',')
        mnbdr = self.Config['mn']['bdr'].replace(' ', '').split(',')
        mnttl = self.Config['mn']['ttl'].replace(' ', '').split(',')
        mnhh = self.Config['mn']['hh'].replace(' ', '').split(',')
        try:
            mntxt_fg = self.EvalColor(mntxt[0])
            mntxt_bg = self.EvalColor(mntxt[1])
            mnbdr_fg = self.EvalColor(mnbdr[0])
            mnbdr_bg = self.EvalColor(mnbdr[1])
            mnttl_fg = self.EvalColor(mnttl[0])
            mnttl_bg = self.EvalColor(mnttl[1])
            mnhh_fg = self.EvalColor(mnhh[0])
            mnhh_bg = self.EvalColor(mnhh[1])
        except Exception as err:
            mntxt_fg = curses.COLOR_WHITE
            mntxt_bg = -1
            mnbdr_fg = curses.COLOR_WHITE
            mnbdr_bg = -1
            mnttl_fg = curses.COLOR_WHITE
            mnttl_bg = -1
            mnhh_fg = curses.COLOR_BLACK
            mnhh_bg = curses.COLOR_WHITE
            logger.error('%s', err)

        # Define kernel color
        kntxt = self.Config['kn']['txt'].replace(' ', '').split(',')
        knbdr = self.Config['kn']['bdr'].replace(' ', '').split(',')
        knttl = self.Config['kn']['ttl'].replace(' ', '').split(',')
        knhh = self.Config['kn']['hh'].replace(' ', '').split(',')
        knco = self.Config['kn']['co'].replace(' ', '').split(',')
        kndi = self.Config['kn']['di'].replace(' ', '').split(',')
        knal = self.Config['kn']['al'].replace(' ', '').split(',')
        try:
            kntxt_fg = self.EvalColor(kntxt[0])
            kntxt_bg = self.EvalColor(kntxt[1])
            knbdr_fg = self.EvalColor(knbdr[0])
            knbdr_bg = self.EvalColor(knbdr[1])
            knttl_fg = self.EvalColor(knttl[0])
            knttl_bg = self.EvalColor(knttl[1])
            knhh_fg = self.EvalColor(knhh[0])
            knhh_bg = self.EvalColor(knhh[1])
            knco_fg = self.EvalColor(knco[0])
            knco_bg = self.EvalColor(knco[1])
            kndi_fg = self.EvalColor(kndi[0])
            kndi_bg = self.EvalColor(kndi[1])
            knal_fg = self.EvalColor(knal[0])
            knal_bg = self.EvalColor(knal[1])
        except Exception as err:
            kntxt_fg = curses.COLOR_RED
            kntxt_bg = -1
            knbdr_fg = curses.COLOR_RED
            knbdr_bg = -1
            knttl_fg = curses.COLOR_RED
            knttl_bg = -1
            knhh_fg = curses.COLOR_WHITE
            knhh_bg = -1
            knco_fg = curses.COLOR_GREEN
            knco_bg = -1
            knal_fg = curses.COLOR_CYAN
            knal_bg = -1
            kndi_fg = curses.COLOR_RED
            kndi_bg = -1
            logger.error('%s', err)

        # Define Pairs
        curses.init_pair(1, wgtxt_fg, wgtxt_bg)
        curses.init_pair(2, wgbdr_fg, wgbdr_bg)

        curses.init_pair(11, mntxt_fg, mntxt_bg)
        curses.init_pair(12, mnbdr_fg, mnbdr_bg)
        curses.init_pair(13, mnttl_fg, mnttl_bg)
        curses.init_pair(14, mnhh_fg, mnhh_bg)
        if mnttl_bg != -1:
            curses.init_pair(15, mnttl_bg, mnbdr_bg)
        else:
            curses.init_pair(15, mnbdr_fg, mnbdr_bg)

        curses.init_pair(21, xptxt_fg, xptxt_bg)
        curses.init_pair(22, xpbdr_fg, xpbdr_bg)
        curses.init_pair(23, xpttl_fg, xpttl_bg)
        curses.init_pair(24, xphh_fg, xphh_bg)
        if xpttl_bg != -1:
            curses.init_pair(25, xpttl_bg, xpbdr_bg)
        else:
            curses.init_pair(25, xpbdr_fg, xpbdr_bg)

        curses.init_pair(31, kntxt_fg, kntxt_bg)
        curses.init_pair(32, knbdr_fg, knbdr_bg)
        curses.init_pair(33, knttl_fg, knttl_bg)
        curses.init_pair(34, knhh_fg, knhh_bg)
        curses.init_pair(35, knco_fg, knco_bg)
        curses.init_pair(36, knal_fg, knal_bg)
        curses.init_pair(37, kndi_fg, kndi_bg)
        if knttl_bg != -1:
            curses.init_pair(38, knttl_bg, knbdr_bg)
        else:
            curses.init_pair(38, knbdr_fg, knbdr_bg)

        curses.init_pair(41, brkn_fg, brkn_bg)
        curses.init_pair(42, brhlp_fg, brhlp_bg)
        curses.init_pair(43, brco_fg, brco_bg)
        curses.init_pair(44, brdco_fg, brdco_bg)
        curses.init_pair(47, mnbdr_fg, brkn_bg)

        if brdco_bg != -1:
            curses.init_pair(40, brdco_bg, mnbdr_bg)
        else:
            curses.init_pair(40, mnbdr_fg, mnbdr_bg)

        if brco_bg != -1:
            curses.init_pair(49, brco_bg, brkn_bg)
        else:
            curses.init_pair(49, mnbdr_fg, brkn_bg)

        if brkn_bg != -1:
            curses.init_pair(45, brkn_bg, mnbdr_bg)
            curses.init_pair(48, brkn_bg, brco_bg)
        else:
            curses.init_pair(45, mnbdr_fg, mnbdr_bg)
            curses.init_pair(48, mnbdr_fg, brco_bg)

        if brhlp_bg != -1:
            curses.init_pair(46, brhlp_bg, mnbdr_bg)
        else:
            curses.init_pair(46, mnbdr_fg, mnbdr_bg)

    def ColorDef(self):
        ''' Color variables. '''

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
        ''' Run daemon '''
        try:
            self.GetVars()    # Init Variables
            self.pkey = -1    # Init pressed Key
            while self.close_signal == 'continue':
                self.UpdateCurses()
            self.ShutdownApp()
        except Exception:
            self.ExitWithError()

    def UpdateCurses(self):
        ''' Update Curses '''

        # Listen to resize and adapt Curses
        self.ResizeCurses()

        # Check if size is enough
        if self.screen_height < self.term_min_height or self.screen_width < self.term_min_width:
            self.SizeWng()
            sleep(0.5)
        else:

            # Check Connection to daemon
            self.CheckSocket()

            # Get variables from daemon
            self.GetVars()

            # Arange variable list
            self.ArangeVarLst()

            # Navigate in the variable list window
            self.NavigateVarLst()

            # Menu Variable
            if self.pkey == ord("\n") and self.row_num != 0:
                # First Update VarLst (avoid bug)
                self.VarLst.border(0)
                self.UpdateVarLst()
                self.stdscreen.refresh()
                self.VarLst.refresh()
                # MenuVar
                var_menu = MenuVar(self)
                if var_menu.IsMenu():
                    var_menu.Display()

            # Menu Help
            if self.pkey == 104:    # -> h
                help_menu = Help(self)
                help_menu.Display()

            # Menu KERNEL
            if self.pkey == 99:    # -> c
                kernel_menu = MenuKernel(self)
                self.cf, self.kc = kernel_menu.Display()
                # Reset cursor location
                self.position = 1
                self.page = int(ceil(self.position/self.row_max))

            # Menu Search
            if self.pkey == 47:    # -> /
                self.SearchVar()
                try:
                    logger.info('Searching for : {} in :\n{}'.format(self.search, self.strings))
                    self.search_index = min([i for i, s in enumerate(self.strings) if self.search in s])
                except ValueError:
                    Wmsg = WarningMsg(self.stdscreen)
                    Wmsg.Display('Variable ' + self.search + ' not in kernel')
                    pass
                else:
                    self.position = self.search_index + 1
                    self.page = int(ceil(self.position/self.row_max))

            # Reconnection to socket
            if self.pkey == 82:    # -> R
                self.RestartSocketConnection()
                self.WngSock()

            # Disconnect from daemon
            if self.pkey == 68:    # -> D
                Wmsg = WarningMsg(self.stdscreen)
                self.CloseMainSocket()
                self.CloseRequestSocket()
                self.WngSock()

            # Connect to daemon
            if self.pkey == 67:     # -> C
                Wmsg = WarningMsg(self.stdscreen)
                self.InitMainSocket()
                self.InitRequestSocket()
                self.WngSock()

            # Update screen size if another menu break because of resizing
            self.ResizeCurses()

            # Update all static panels
            self.UpdateStatic()

            # Get pressed key
            self.pkey = self.stdscreen.getch()

            # Close menu
            if self.pkey == 113:
                self.MenuClose()

    def ArangeVarLst(self):
        ''' Organize/Arange variable list. '''

        if self.mk_sort == 'name':
            self.strings = sorted(list(self.variables))

        elif self.mk_sort == 'type':
            self.strings = TypeSort(self.variables)

        elif self.mk_sort == 'filter':
            self.strings = FilterVarLst(self.variables, self.filter)
            self.VarLst_wng = 'Filter : ' + self.filter + ' (' + str(len(self.strings)) + ' obj.)'

        # Sort variable by name/type
        if self.pkey == 115:
            if self.mk_sort == 'name':    # -> s
                self.mk_sort = 'type'
            elif self.mk_sort == 'type':
                self.mk_sort = 'name'

        # Filter variables
        if self.pkey == 108:    # -> l
            self.FilterVar()
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

    def FilterVar(self):
        ''' Apply filter for the variable list'''

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
            menu_filter.addstr(0, int((self.screen_width-len(self.VarLst_name))/2), '| ' + self.VarLst_name + ' |', self.c_exp_ttl | curses.A_BOLD)

        curses.echo()
        menu_filter.addstr(2, 3, "Filter :", curses.A_BOLD | self.c_exp_txt)
        self.filter = menu_filter.getstr(2, 14, 20).decode('utf-8')
        curses.noecho()

        panel_filter.hide()
        curses.halfdelay(self.curse_delay)  # Relaunch autorefresh !

    def SearchVar(self):
        ''' Search an object in the variable list'''

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
            menu_search.addstr(0, int((self.screen_width-len(self.VarLst_name))/2), '', self.c_exp_pwf)
            menu_search.addstr(self.VarLst_name, self.c_exp_ttl | curses.A_BOLD)
            menu_search.addstr('', self.c_exp_pwf)
        else:
            menu_search.addstr(0, int((self.screen_width-len(self.VarLst_name))/2), '| ' + self.VarLst_name + ' |', self.c_exp_ttl | curses.A_BOLD)

        curses.echo()
        menu_search.addstr(2, 3, "Search Variable :", curses.A_BOLD | self.c_exp_txt)
        self.search = menu_search.getstr(2, 21, 20).decode('utf-8')
        curses.noecho()

        panel_search.hide()
        curses.halfdelay(self.curse_delay)  # Relaunch autorefresh !

    def UpdateStatic(self):
        ''' Update all static windows. '''

        # Erase all windows
        self.VarLst.erase()
        self.stdscreen.erase()

        # Create border before updating fields
        self.stdscreen.border(0)
        self.VarLst.border(0)

        # Update all windows (virtually)
        if self.DEBUG:
            self.QueueInfo()         # Display infos about the process
            self.TermInfo()         # Display infos about the process
            self.DebugInfo()        # Display debug infos

        self.UpdateVarLst()     # Update variables list

        # Update display
        self.BottomInfo()      # Display infos about kernel at bottom
        self.stdscreen.refresh()
        self.VarLst.refresh()

    def UpdateVarLst(self):
        ''' Update the list of variables display '''

        # Title
        if self.Config['font']['pw-font'] == 'True':
            self.VarLst.addstr(0, int((self.screen_width-len(self.VarLst_name))/2), '', self.c_exp_pwf | curses.A_BOLD)
            self.VarLst.addstr(self.VarLst_name, self.c_exp_ttl | curses.A_BOLD)
            self.VarLst.addstr('', self.c_exp_pwf | curses.A_BOLD)
        else:
            self.VarLst.addstr(0, int((self.screen_width-len(self.VarLst_name))/2), '| ' + self.VarLst_name + ' |', self.c_exp_ttl | curses.A_BOLD)

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
                cell = FormatCell(self.variables, self.strings[i-1], self.screen_width)
                if (i+(self.row_max*(self.page-1)) == self.position+(self.row_max*(self.page-1))):
                    self.VarLst.addstr(i-(self.row_max*(self.page-1)), 2, cell.encode(code), self.c_exp_hh)
                else:
                    self.VarLst.addstr(i-(self.row_max*(self.page-1)), 2, cell.encode(code), curses.A_DIM | self.c_exp_txt)
                if i == self.row_num:
                    break

        # Bottom info
        if self.Config['font']['pw-font'] == 'True' and len(self.VarLst_wng) > 0:
            self.VarLst.addstr(self.row_max+1, int((self.screen_width-len(self.VarLst_wng))/2), '', self.c_exp_pwf)
            self.VarLst.addstr(self.VarLst_wng, self.c_exp_ttl | curses.A_BOLD)
            self.VarLst.addstr('',  self.c_exp_pwf | curses.A_BOLD)
        elif len(self.VarLst_wng) > 0:
            self.VarLst.addstr(self.row_max+1, int((self.screen_width-len(self.VarLst_wng))/2), '< ' + self.VarLst_wng + ' >', curses.A_DIM | self.c_exp_ttl)

    def NavigateVarLst(self):
        ''' Navigation though the variable list'''

        self.pages = int(ceil(self.row_num/self.row_max))
        if self.pkey == curses.KEY_DOWN:
            self.NavDown()
        if self.pkey == curses.KEY_UP:
            self.NavUp()
        if self.pkey in (curses.KEY_LEFT, 339):
            self.NavLeft()
        if self.pkey in (curses.KEY_RIGHT, 338):
            self.NavRight()
        if self.pkey == 262:
            self.position = 1
            self.page = 1
        if self.pkey == 360:
            self.position = self.row_num
            self.page = self.pages

    def NavUp(self):
        ''' Navigate Up. '''

        if self.page == 1:
            if self.position > 1:
                self.position = self.position - 1
        else:
            if self.position > (1+(self.row_max*(self.page-1))):
                self.position = self.position - 1
            else:
                self.page = self.page - 1
                self.position = self.row_max + (self.row_max*(self.page-1))

    def NavDown(self):
        ''' Navigate Down. '''

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

    def NavLeft(self):
        ''' Navigate Left. '''

        if self.page > 1:
            self.page = self.page - 1
            self.position = 1 + (self.row_max*(self.page-1))

    def NavRight(self):
        ''' Navigate Right. '''

        if self.page < self.pages:
            self.page = self.page + 1
            self.position = (1+(self.row_max*(self.page-1)))

    def GetVars(self):
        ''' Get variable from the daemon '''

        try:
            tmp = recv_msg(self.MainSock).decode('utf8')
        except BlockingIOError:
            pass
        except OSError:     # If user disconnect cpyvke from socket
            pass
        else:
            if tmp:
                self.variables = WhoToDict(tmp)
                logger.info('Variable list updated')
                logger.debug('\n%s', tmp)
                try:
                    # remove temporary file used by daemon from the list
                    del self.variables['fcpyvke0']
                except KeyError:
                    pass

    def CheckSocket(self):
        ''' Test if connection to daemon is alive. '''

        try:
            send_msg(self.MainSock, '<TEST>')
            self.connected = True
        except OSError:
            self.connected = False

    def ResizeCurses(self):
        ''' Check if terminal is resized and adapt screen '''

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

    def SizeWng(self):
        ''' Blank screen and display a warning if size of the terminal is too small. '''

        self.stdscreen.erase()
        self.screen_height, self.screen_width = self.stdscreen.getmaxyx()
        msg_actual = str(self.screen_width) + 'x' + str(self.screen_height)
        msg_limit = 'Win must be > ' + str(self.term_min_width) + 'x' + str(self.term_min_height)
        try:
            self.stdscreen.addstr(int(self.screen_height/2), int((self.screen_width-len(msg_limit))/2), msg_limit, self.c_warn_txt | curses.A_BOLD)
            self.stdscreen.addstr(int(self.screen_height/2)+1, int((self.screen_width-len(msg_actual))/2), msg_actual, self.c_warn_txt | curses.A_BOLD)
        except:
            pass
        self.stdscreen.border(0)
        self.stdscreen.refresh()

    def BottomInfo(self):
        ''' Check and display kernel informations '''

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
            self.stdscreen.addstr(self.screen_height-1, self.screen_width-12, '', self.c_bar_hlp_pwf | curses.A_BOLD)
            self.stdscreen.addstr(' h:help ', self.c_bar_hlp | curses.A_BOLD)
            self.stdscreen.addstr('', self.c_bar_hlp_pwf | curses.A_BOLD)
        else:
            self.stdscreen.addstr(self.screen_height-1, self.screen_width-12, '< h:help >', self.c_bar_hlp | curses.A_BOLD)

    def QueueInfo(self):
        ''' Display queue informations '''

        self.stdscreen.addstr(self.row_max + 4, int(2*self.screen_width/3), ' Socket ', self.c_main_ttl | curses.A_BOLD)
        if self.Config['font']['pw-font'] == 'True':
            self.stdscreen.addstr('', self.c_main_pwf | curses.A_BOLD)

    def TermInfo(self):
        ''' Display terminal informations '''

        self.stdscreen.addstr(self.row_max + 4, int(self.screen_width/3), ' Terminal ', self.c_main_ttl | curses.A_BOLD)
        if self.Config['font']['pw-font'] == 'True':
            self.stdscreen.addstr('', self.c_main_pwf | curses.A_BOLD)
        self.stdscreen.addstr(self.row_max + 5, int(self.screen_width/3) + 1, ' width : ' + str(self.screen_width), curses.A_DIM | self.c_main_txt)
        self.stdscreen.addstr(self.row_max + 6, int(self.screen_width/3) + 1, ' heigh : ' + str(self.screen_height), curses.A_DIM | self.c_main_txt)
        self.stdscreen.addstr(self.row_max + 7, int(self.screen_width/3) + 1, ' color : ' + str(curses.COLORS), curses.A_DIM | self.c_main_txt)

    def DebugInfo(self):
        ''' Display debug informations '''

        self.stdscreen.addstr(self.row_max + 4, 2, ' Debug ', self.c_main_ttl | curses.A_BOLD)
        if self.Config['font']['pw-font'] == 'True':
            self.stdscreen.addstr('', self.c_main_pwf | curses.A_BOLD)
        self.stdscreen.addstr(self.row_max + 5, 3, ' key : ' + str(self.pkey), curses.A_DIM | self.c_main_txt)
        self.stdscreen.addstr(self.row_max + 6, 3, ' search : ' + str(self.search), curses.A_DIM | self.c_main_txt)
        self.stdscreen.addstr(self.row_max + 7, 3, ' limit : ' + str(self.filter), curses.A_DIM | self.c_main_txt)
        self.stdscreen.addstr(self.row_max + 8, 3, ' sort : ' + str(self.mk_sort), curses.A_DIM | self.c_main_txt)

    def MenuClose(self):
        ''' Close Menu '''

        # Init Menu
        cmsg = 'Shutdown daemon (default no) ? [y|n|q]'
        cmsg_width = len(cmsg) + 4
        menu_close = self.stdscreen.subwin(3, cmsg_width, int(self.screen_height/2), int((self.screen_width-cmsg_width)/2))
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
            sleep(0.1)

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

    def ShutdownApp(self):
        ''' Shutdown CUI, Daemon, and kernel '''

        curses.endwin()

        if self.close_signal == 'close':
            print('Exiting ! Closing cpyvke...')
        elif self.close_signal == 'shutdown':
            print('Exiting ! Shutting down daemon...')
            send_msg(self.RequestSock, '<_stop>')
            # self.kc.shutdown()

        self.MainSock.close()
        self.RequestSock.close()
        self.KillAllFigures()   # Stop all figure subprocesses

    def KillAllFigures(self):
        ''' Kill all figures (running in different processes) '''

        import multiprocessing

        if len(multiprocessing.active_children()) == 1:
            print(str(len(multiprocessing.active_children())) + ' figures killed')
        elif len(multiprocessing.active_children()) > 1:
            print(str(len(multiprocessing.active_children())) + ' figure killed')

        for child in multiprocessing.active_children():
            child.terminate()

    def ExitWithError(self):
        ''' If error, send terminate signal to daemon and resore terminal to
            sane state '''

        self.close_signal = 'close'
        self.stdscreen.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.endwin()
        self.ShutdownApp()
        traceback.print_exc()           # Print the exception


def InitCf(lockfile, pidfile):
    ''' Init connection file. '''

    with open(lockfile, 'r') as f:
        kernel_id = f.readline()

    return find_connection_file(kernel_id)


def WithDaemon(lockfile, pidfile, cmd):
    ''' Launch daemon. '''

    os.system(cmd)

    while os.path.exists(pidfile) is False:
        sleep(0.1)

    return InitCf(lockfile, pidfile)


def ParseArgs(lockfile, pidfile):
    ''' Parse Arguments. '''

    parser = argparse.ArgumentParser()
    parser.add_argument("-D", "--debug", help="Debug mode", action="store_true")
    parser.add_argument("-L", "--list", help="List all kernels", action="store_true")
    parser.add_argument("integer",
                        help="Start up with existing kernel. \
                        INTEGER is the id of the connection file.",
                        nargs='?')

    args = parser.parse_args()

    if args.list:
        print_kernel_list()
        sys.exit(2)

    elif os.path.exists(lockfile) and os.path.exists(pidfile):

        try:
            cf = InitCf(lockfile, pidfile)
        except:
            missing(lockfile, pidfile)
            sys.exit(2)

    elif args.integer:

        try:
            find_connection_file(str(args.integer))
        except:
            message = 'Error :\tCannot find kernel id. {} !\n\tExiting\n'
            sys.stderr.write(message.format(args.integer))
            sys.exit(2)

        cmd = 'kd5 start ' + str(args.integer)
        cf = WithDaemon(lockfile, pidfile, cmd)

    else:

        cmd = 'kd5 start'
        cf = WithDaemon(lockfile, pidfile, cmd)

    return args, cf


def missing(lockfile, pidfile):
    ''' Fix missing connection file. '''

    print('An old lock file already exists, but the kernel connection file is missing.')
    print('As this issue is not fixed, cpyvke cannot run.')
    rm_lock = input('Remove the old lock file ? [y|n] : ')

    if rm_lock == 'y':
        os.remove(lockfile)
        os.remove(pidfile)
        print('You can now restart cpyvke.')
    elif rm_lock == 'n':
        print('Exiting...')
    else:
        print('Wrong choice. exiting... ')


def main(args=None):
    ''' Launch cpyvke. '''

    # Parse Config
    cfg = cfg_setup()
    Config = cfg.RunCfg()

    # Define Paths
    logdir = os.path.expanduser('~') + '/.cpyvke/'
    lockfile = logdir + 'kd5.lock'
    pidfile = logdir + 'kd5.pid'
    logfile = logdir + 'cpyvke.log'

    # Logger
    logger.setLevel(logging.DEBUG)

    # create the logging file handler
    handler = RotatingFileHandler(logfile, maxBytes=10*1024*1024,
                                  backupCount=5)
    formatter = logging.Formatter('%(asctime)s :: %(name)s :: %(threadName)s :: %(levelname)s :: %(message)s', datefmt='%Y-%m-%d - %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Parse arguments
    args, cf = ParseArgs(lockfile, pidfile)

    # Init kernel
    km, kc = connect_kernel(cf)

    # Run App
    logger.info('cpyvke started')
    App = MainWin(kc, cf, Config, args.debug)
    App.run()


if __name__ == "__main__":
    main()
