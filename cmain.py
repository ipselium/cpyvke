#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : CUIMainWin.py
# Creation Date : Wed Nov  9 10:03:04 2016
# Last Modified : mar. 06 déc. 2016 00:49:30 CET
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
from threading import Thread
import curses
import traceback
from math import ceil
from Queue import Empty
from curses import panel
import time
import os
# Personal Libs
from cvar import MenuVarCUI
from ckernel import MenuKernelCUI
from cwidgets import WarningMsg, MenuHelpCUI, SizeWng
from ctools import FormatCell, TypeSort, FilterVarLst


class CUI(Thread):
    ''' Main window. '''

    def __init__(self, kc, cf, qstop, qvar, qreq, qans, qkc, Config, DEBUG=False):

        Thread.__init__(self)
        self.kc = kc
        self.cf = cf
        self.qstop = qstop
        self.qvar = qvar
        self.qreq = qreq
        self.qans = qans
        self.qkc = qkc
        self.curse_delay = 5
        self.Config = Config
        self.DEBUG = DEBUG
        self.LogDir = os.path.expanduser("~") + "/.cpyvke/"
        # Init CUI :
        self.close_signal = 'continue'
        self.stdscreen = curses.initscr()   # Init curses
        self.stdscreen.keypad(1)            #
        self.stdscreen.border(0)            # draw a border around screen
        self.screen_height, self.screen_width = self.stdscreen.getmaxyx()  # get heigh and width of stdscreen

        # Curses options
        curses.noecho()             # Wont print the input
        curses.cbreak()             #
        curses.curs_set(0)          #
        curses.halfdelay(self.curse_delay)         # How many tenths of a second are waited to refresh stdscreen, from 1 to 255

        # Colors
        self.InitColors()
        self.stdscreen.bkgd(self.c_main_txt)
        self.stdscreen.attrset(self.c_main_bdr | curses.A_BOLD)  # Change border color

        # Min terminal size accepted
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
        self.search_index = 0

        # Various Variables :
        self.VarLst_name = "| Variable Explorer |"
        self.VarLst_wng = ""
        self.mk_varlst = 'name'

        # Init Variable Box
        self.row_max = self.screen_height-self.kernel_info  # max number of rows
        self.VarLst = curses.newwin(self.row_max+2, self.screen_width-2, 1, 1)  # (heigh, width, begin_y, begin_x)
        self.VarLst.bkgd(self.c_exp_txt)
        self.VarLst.attrset(self.c_exp_bdr | curses.A_BOLD)  # Change border color

    def EvalColor(self, color):
        ''' Check if a color is set to transparent. '''

        if color == 'transparent':
            curses.use_default_colors()
            return -1
        else:
            return eval('curses.COLOR_' + color.upper())

    def InitColors(self):
        ''' Initialize colors. '''

        curses.start_color()        #

        # Define warning color
        wgtxt = self.Config['wg']['txt'].replace(' ', '').split(',')
        wgbdr = self.Config['wg']['bdr'].replace(' ', '').split(',')
        try:
            wgtxt_fg = self.EvalColor(wgtxt[0])
            wgtxt_bg = self.EvalColor(wgtxt[1])
            wgbdr_fg = self.EvalColor(wgbdr[0])
            wgbdr_bg = self.EvalColor(wgbdr[1])
        except Exception, err:
            wgtxt_fg = curses.COLOR_RED
            wgtxt_bg = -1
            wgbdr_fg = curses.COLOR_RED
            wgbdr_bg = -1
            with open(self.LogDir + 'cpyvke.log', 'a') as f:
                f.write(time.strftime("[%D :: %H:%M:%S] ::  Error ::") + str(err) + '\n')

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
        except Exception, err:
            xptxt_fg = curses.COLOR_WHITE
            xptxt_bg = -1
            xpbdr_fg = curses.COLOR_CYAN
            xpbdr_bg = -1
            xpttl_fg = curses.COLOR_CYAN
            xpttl_bg = -1
            xphh_fg = curses.COLOR_BLACK
            xphh_bg = curses.COLOR_CYAN
            with open(self.LogDir + 'cpyvke.log', 'a') as f:
                f.write(time.strftime("[%D :: %H:%M:%S] ::  Error ::") + str(err) + '\n')

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
        except Exception, err:
            mntxt_fg = curses.COLOR_WHITE
            mntxt_bg = -1
            mnbdr_fg = curses.COLOR_WHITE
            mnbdr_bg = -1
            mnttl_fg = curses.COLOR_WHITE
            mnttl_bg = -1
            mnhh_fg = curses.COLOR_BLACK
            mnhh_bg = curses.COLOR_WHITE
            with open(self.LogDir + 'cpyvke.log', 'a') as f:
                f.write(time.strftime("[%D :: %H:%M:%S] ::  Error ::") + str(err) + '\n')

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
        except Exception, err:
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
            with open(self.LogDir + 'cpyvke.log', 'a') as f:
                f.write(time.strftime("[%D :: %H:%M:%S] ::  Error ::") + str(err) + '\n')

        # Define Styles
        curses.init_pair(1, wgtxt_fg, wgtxt_bg)
        curses.init_pair(2, wgbdr_fg, wgbdr_bg)

        curses.init_pair(11, mntxt_fg, mntxt_bg)
        curses.init_pair(12, mnbdr_fg, mnbdr_bg)
        curses.init_pair(13, mnttl_fg, mnttl_bg)
        curses.init_pair(14, mnhh_fg, mnhh_bg)
        curses.init_pair(14, mnhh_fg, mnhh_bg)

        curses.init_pair(21, xptxt_fg, xptxt_bg)
        curses.init_pair(22, xpbdr_fg, xpbdr_bg)
        curses.init_pair(23, xpttl_fg, xpttl_bg)
        curses.init_pair(24, xphh_fg, xphh_bg)

        curses.init_pair(31, kntxt_fg, kntxt_bg)
        curses.init_pair(32, knbdr_fg, knbdr_bg)
        curses.init_pair(33, knttl_fg, knttl_bg)
        curses.init_pair(34, knhh_fg, knhh_bg)
        curses.init_pair(35, knco_fg, knco_bg)
        curses.init_pair(36, knal_fg, knal_bg)
        curses.init_pair(37, kndi_fg, kndi_bg)

        self.c_warn_txt = curses.color_pair(1)
        self.c_warn_bdr = curses.color_pair(2)

        self.c_main_txt = curses.color_pair(11)
        self.c_main_bdr = curses.color_pair(12)
        self.c_main_ttl = curses.color_pair(13)
        if mnhh_fg == 0: # Black
            self.c_main_hh = curses.color_pair(14)
        else:
            self.c_main_hh = curses.color_pair(14) | curses.A_BOLD

        self.c_exp_txt = curses.color_pair(21)
        self.c_exp_bdr = curses.color_pair(22)
        self.c_exp_ttl = curses.color_pair(23)
        if xphh_fg == 0:
            self.c_exp_hh = curses.color_pair(24)
        else:
            self.c_exp_hh = curses.color_pair(24) | curses.A_BOLD

        self.c_kern_txt = curses.color_pair(31)
        self.c_kern_bdr = curses.color_pair(32)
        self.c_kern_ttl = curses.color_pair(33)
        self.c_kern_hh = curses.color_pair(34)
        self.c_kern_co = curses.color_pair(35)
        self.c_kern_al = curses.color_pair(36)
        self.c_kern_di = curses.color_pair(37)
        if knhh_fg == 0:
            self.c_kn_hh = curses.color_pair(34)
        else:
            self.c_kn_hh = curses.color_pair(34) | curses.A_BOLD

    def run(self):
        ''' Run daemon '''
        try:
            self.GetVars()    # Init Variables
            self.pkey = -1    # Init pressed Key
            while self.close_signal == 'continue':
                self.UpdateCUI()
            self.ShutdownApp()
        except:
            self.ExitWithError()

    def UpdateCUI(self):
        ''' Update Curses '''

        # Listen to resize and adapt Curses
        self.ResizeCUI()

        # Check if size is enough
        if self.screen_height < self.term_min_height or self.screen_width < self.term_min_width:
            SizeWng(self)
            time.sleep(0.1)
        else:

            # Get variables from daemon
            self.GetVars()

            # Arange variable list
            self.ArangeVarLst()

            # Navigate in the variable list window
            self.NavigateVarLst()

            # Menu Variable
            if self.pkey == ord("\n") and self.row_num != 0:
                var_menu = MenuVarCUI(self)
                var_menu.Display()

            # Menu Help
            if self.pkey == 104:    # -> h
                help_menu = MenuHelpCUI(self.stdscreen)
                help_menu.Display()

            # Menu KERNEL
            if self.pkey == 99:    # -> c
                kernel_menu = MenuKernelCUI(self)
                self.cf, self.kc = kernel_menu.Display()
                # Reset cursor location
                self.position = 1
                self.page = int(ceil(self.position/self.row_max))

            # Menu Search
            if self.pkey == 47:    # -> /
                self.SearchVar()
                try:
                    self.search_index = min([i for i, s in enumerate(self.strings) if self.search in s])
                except ValueError:
                    Wmsg = WarningMsg(self.stdscreen)
                    Wmsg.Display('Variable ' + self.search + ' not in kernel')
                    pass
                else:
                    self.position = self.search_index + 1
                    self.page = int(ceil(self.position/self.row_max))

            # Update screen size if another menu break because of resizing
            self.ResizeCUI()

            # Update all static panels
            self.UpdateStatic()

            # Get pressed key
            self.pkey = self.stdscreen.getch()

            # Close menu
            if self.pkey == 113:
                self.MenuCloseCUI()

    def ArangeVarLst(self):
        ''' Organize/Arange variable list. '''

        if self.mk_varlst == 'name':
            self.strings = sorted(self.variables.keys())

        elif self.mk_varlst == 'type':
            self.strings = TypeSort(self.variables)

        elif self.mk_varlst == 'filter':
            self.strings = FilterVarLst(self.variables, self.filter)
            self.VarLst_wng = '< Filter : ' + str(self.filter) + ' (' + str(len(self.strings)) + ' obj.) >'

        # Sort variable by name/type
        if self.pkey == 115:
            if self.mk_varlst == 'name':    # -> s
                self.mk_varlst = 'type'
            elif self.mk_varlst == 'type':
                self.mk_varlst = 'name'

        # Filter variables
        if self.pkey == 108:    # -> l
            self.FilterVar()
            self.mk_varlst = 'filter'
            self.position = 1
            self.page = int(ceil(self.position/self.row_max))

        # Reinit
        if self.pkey == 117:
            self.mk_varlst = 'name'
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
        menu_filter.addstr(0, int((self.screen_width-len(self.VarLst_name))/2), self.VarLst_name, self.c_exp_ttl | curses.A_BOLD)

        curses.echo()
        menu_filter.addstr(2, 3, "Filter :", curses.A_BOLD | self.c_exp_txt)
        self.filter = menu_filter.getstr(2, 14, 20)
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

        menu_search.addstr(0, int((self.screen_width-len(self.VarLst_name))/2), self.VarLst_name, self.c_exp_ttl | curses.A_BOLD)

        curses.echo()
        menu_search.addstr(2, 3, "Search Variable :", curses.A_BOLD | self.c_exp_txt)
        self.search = menu_search.getstr(2, 21, 20)
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
            self.ProcInfo()         # Display infos about the process
            self.DebugInfo()        # Display debug infos

        self.UpdateVarLst()     # Update variables list

        # Update display
        self.stdscreen.refresh()
        self.VarLst.refresh()
        self.BottomInfo()      # Display infos about kernel at bottom

    def UpdateVarLst(self):
        ''' Update the list of variables display '''

        self.VarLst.addstr(0, int((self.screen_width-len(self.VarLst_name))/2), self.VarLst_name, self.c_exp_ttl | curses.A_BOLD)

        for i in range(1+(self.row_max*(self.page-1)), self.row_max+1 + (self.row_max*(self.page-1))):

            if self.row_num == 0:
                self.VarLst.addstr(1, 1, "No Variable in kernel", self.c_exp_hh)

            else:
                cell = FormatCell(self.variables, self.strings[i-1], self.screen_width)
                if (i+(self.row_max*(self.page-1)) == self.position+(self.row_max*(self.page-1))):
                    self.VarLst.addstr(i-(self.row_max*(self.page-1)), 2, cell, self.c_exp_hh)
                else:
                    self.VarLst.addstr(i-(self.row_max*(self.page-1)), 2, cell, curses.A_DIM | self.c_exp_txt)
                if i == self.row_num:
                    break

        self.VarLst.addstr(self.row_max+1, int((self.screen_width-len(self.VarLst_wng))/2), self.VarLst_wng, curses.A_DIM | self.c_exp_ttl)

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
            if self.qvar.qsize() > 0:
                self.variables = self.qvar.get()
        except Empty:
            pass

    def ResizeCUI(self):
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

    def BottomInfo(self):
        ''' Check and display kernel informations '''

        self.stdscreen.addstr(self.screen_height-1, 2, '< Kernel : ', self.c_main_ttl | curses.A_BOLD)

        if self.kc.is_alive():
            self.stdscreen.addstr(self.screen_height-1, 13, 'connected ', self.c_kern_al | curses.A_BOLD)
            self.stdscreen.addstr(self.screen_height-1, 23, '[' + str(len(self.variables.keys())) + ' obj, id ' + self.cf.split('-')[1].split('.')[0] + '] >', self.c_main_ttl | curses.A_BOLD)
        else:
            self.stdscreen.addstr(self.screen_height-1, 13, 'disconnected ', self.c_warn_txt | curses.A_BOLD)

        self.stdscreen.addstr(self.screen_height-1, self.screen_width-12, '< h:help >', self.c_main_ttl | curses.A_BOLD)

    def ProcInfo(self):
        ''' Display process informations '''

        self.stdscreen.addstr(self.row_max + 4, 3, 'Process informations :', self.c_main_ttl | curses.A_BOLD)
        self.stdscreen.addstr(self.row_max + 5, 5, '+ ' + 'queue stop     : ' + str(self.qstop.qsize()), curses.A_DIM | self.c_main_txt)
        self.stdscreen.addstr(self.row_max + 6, 5, '+ ' + 'queue variable : ' + str(self.qvar.qsize()), curses.A_DIM | self.c_main_txt)
        self.stdscreen.addstr(self.row_max + 7, 5, '+ ' + 'queue request  : ' + str(self.qreq.qsize()), curses.A_DIM | self.c_main_txt)
        self.stdscreen.addstr(self.row_max + 8, 5, '+ ' + 'queue answer   : ' + str(self.qans.qsize()), curses.A_DIM | self.c_main_txt)
        self.stdscreen.addstr(self.row_max + 9, 5, '+ ' + 'queue kernel   : ' + str(self.qkc.qsize()), curses.A_DIM | self.c_main_txt)

    def DebugInfo(self):
        ''' Display debug informations '''

        self.stdscreen.addstr(self.row_max + 4, int(self.screen_width/2), 'Debug informations :', self.c_main_ttl | curses.A_BOLD)
        self.stdscreen.addstr(self.row_max + 5, int(self.screen_width/2) + 2, '+ ' + 'width : ' + str(self.screen_width), curses.A_DIM | self.c_main_txt)
        self.stdscreen.addstr(self.row_max + 6, int(self.screen_width/2) + 2, '+ ' + 'heigh : ' + str(self.screen_height), curses.A_DIM | self.c_main_txt)
        self.stdscreen.addstr(self.row_max + 7, int(self.screen_width/2) + 2, '+ ' + 'key : ' + str(self.pkey), curses.A_DIM | self.c_main_txt)
        self.stdscreen.addstr(self.row_max + 8, int(self.screen_width/2) + 2, '+ ' + 'Search : ' + str(self.search), curses.A_DIM | self.c_main_txt)
        self.stdscreen.addstr(self.row_max + 9, int(self.screen_width/2) + 2, '+ ' + 'Sort : ' + str(self.mk_varlst), curses.A_DIM | self.c_main_txt)
        self.stdscreen.addstr(self.row_max + 10, int(self.screen_width/2) + 2, '+ ' + 'Color : ' + str(curses.COLOR_BLACK), curses.A_DIM | self.c_main_txt)

    def MenuCloseCUI(self):
        ''' Close Menu '''

        # Init Menu
        cmsg = 'Shutdown kernel (default no) ? [y|n|q]'
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
            time.sleep(0.1)

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
            print('Exiting ! Closing kernel connexion...')
        elif self.close_signal == 'shutdown':
            print('Exiting ! Shuting down kernel...')
            self.kc.shutdown()

        self.KillAllFigures()

        if self.qstop.qsize() > 0:
            self.qstop.queue.clear()
        self.qstop.put(True)

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

        if self.qstop.qsize() > 0:
            self.qstop.queue.clear()
        self.qstop.put(True)

        self.stdscreen.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.endwin()
        traceback.print_exc()           # Print the exception
