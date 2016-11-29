#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : CUIMainWin.py
# Creation Date : Wed Nov  9 10:03:04 2016
# Last Modified : mar. 29 nov. 2016 13:14:56 CET
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
from time import sleep
# Personal Libs
from cvar import MenuVarCUI
from ckernel import MenuKernelCUI
from cwidgets import WarningMsg, MenuHelpCUI, SizeWng
from ctools import format_cell


class CUI(Thread):
    ''' Main window. '''

    def __init__(self, kc, cf, qstop, qvar, qreq, qans, qkc, DEBUG=False):

        Thread.__init__(self)
        self.kc = kc
        self.cf = cf
        self.qstop = qstop
        self.qvar = qvar
        self.qreq = qreq
        self.qans = qans
        self.qkc = qkc
        self.curse_delay = 5
        self.DEBUG = DEBUG

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

        curses.start_color()        #
        curses.use_default_colors()  # To have transparency : default colors
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
        curses.init_pair(2, curses.COLOR_CYAN, -1)
        curses.init_pair(3, curses.COLOR_RED, -1)
        curses.init_pair(4, curses.COLOR_GREEN, -1)

        # Define Styles
        self.highlightText = curses.color_pair(1)
        self.cyan_text = curses.color_pair(2)
        self.red_text = curses.color_pair(3)
        self.green_text = curses.color_pair(4)
        self.normalText = curses.A_NORMAL

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

        # Various Texts :
        self.VarLst_name = "| Variable Explorer |"

        # Init Variable Box
        self.row_max = self.screen_height-self.kernel_info  # max number of rows
        self.VarLst = curses.newwin(self.row_max+2, self.screen_width-2, 1, 1)  # (heigh, width, begin_y, begin_x)
        self.VarLst.attrset(self.cyan_text)  # Change border color
        self.VarLst.box()

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
            sleep(0.1)
        else:
            # Get variables from daemon
            self.GetVars()
            self.strings = sorted(self.variables.keys())
            self.row_num = len(self.strings)

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

            # Erase all windows
            self.VarLst.erase()
            self.stdscreen.erase()

            # Create border before updating fields
            self.stdscreen.border(0)
            self.VarLst.border(0)

            # Update all windows (virtually)
            self.ProcInfo()         # Display infos about the process
            self.DebugInfo()        # Display debug infos
            self.UpdateVarLst()     # Update variables list

            # Update display
            self.stdscreen.refresh()
            self.VarLst.refresh()
            self.BottomInfo()      # Display infos about kernel at bottom

            # Get pressed key
            self.pkey = self.stdscreen.getch()

            # Close menu
            if self.pkey == 113:
                self.MenuCloseCUI()

    def SearchVar(self):
        ''' Search an object in the variable list'''

        # Init Menu
        menu_search = self.stdscreen.subwin(self.row_max+2, self.screen_width-2, 1, 1)
        menu_search.attrset(self.cyan_text)    # change border color
        menu_search.border(0)
        menu_search.keypad(1)

        # Send menu to a panel
        panel_search = panel.new_panel(menu_search)
        panel.update_panels()

        panel_search.top()        # Push the panel to the bottom of the stack.
        panel_search.show()       # Display the panel (which might have been hidden)
        menu_search.clear()
        menu_search.border(0)
        menu_search.addstr(0, int((self.screen_width-len(self.VarLst_name))/2), self.VarLst_name, curses.A_BOLD | self.cyan_text)

        curses.echo()
        menu_search.addstr(2, 3, "Search Variable :", curses.A_BOLD)
        self.search = menu_search.getstr(2, 21, 20)
        curses.noecho()

        panel_search.hide()
        panel.update_panels()
        curses.doupdate()
        curses.halfdelay(self.curse_delay)  # Relaunch autorefresh !

    def UpdateVarLst(self):
        ''' Update the list of variables display '''

        self.VarLst.addstr(0, int((self.screen_width-len(self.VarLst_name))/2), self.VarLst_name, curses.A_BOLD | self.cyan_text)

        for i in range(1+(self.row_max*(self.page-1)), self.row_max+1 + (self.row_max*(self.page-1))):

            if self.row_num == 0:
                self.VarLst.addstr(1, 1, "No Variable in kernel", self.highlightText)

            else:
                cell = format_cell(self.variables, self.strings[i-1], self.screen_width)
                if (i+(self.row_max*(self.page-1)) == self.position+(self.row_max*(self.page-1))):
                    self.VarLst.addstr(i-(self.row_max*(self.page-1)), 2, cell, self.highlightText)
                else:
                    self.VarLst.addstr(i-(self.row_max*(self.page-1)), 2, cell, self.normalText)
                if i == self.row_num:
                    break

        self.stdscreen.refresh()
        self.VarLst.refresh()

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

        self.stdscreen.addstr(self.screen_height-1, 2, '< Kernel : ', curses.A_BOLD)

        if self.kc.is_alive():
            self.stdscreen.addstr(self.screen_height-1, 13, 'connected ', curses.A_BOLD | self.cyan_text)
            self.stdscreen.addstr(self.screen_height-1, 23, '[' + str(self.row_num) + ' obj, id ' + self.cf.split('-')[1].split('.')[0] + '] >', curses.A_BOLD)
        else:
            self.stdscreen.addstr(self.screen_height-1, 13, 'disconnected ', curses.A_BOLD | self.red_text)

        self.stdscreen.addstr(self.screen_height-1, self.screen_width-12, '< h:help >', curses.A_BOLD)

    def ProcInfo(self):
        ''' Display process informations '''

        if self.DEBUG:
            self.stdscreen.addstr(self.row_max + 4, 3, 'Process informations :', curses.A_BOLD | self.cyan_text)
            self.stdscreen.addstr(self.row_max + 5, 5, '+ ' + 'queue stop     : ' + str(self.qstop.qsize()))
            self.stdscreen.addstr(self.row_max + 6, 5, '+ ' + 'queue variable : ' + str(self.qvar.qsize()))
            self.stdscreen.addstr(self.row_max + 7, 5, '+ ' + 'queue request  : ' + str(self.qreq.qsize()))
            self.stdscreen.addstr(self.row_max + 8, 5, '+ ' + 'queue answer   : ' + str(self.qans.qsize()))
            self.stdscreen.addstr(self.row_max + 9, 5, '+ ' + 'queue kernel   : ' + str(self.qkc.qsize()))

    def DebugInfo(self):
        ''' Display debug informations '''

        if self.DEBUG:
            self.stdscreen.addstr(self.row_max + 4, int(self.screen_width/2), 'Debug informations :', curses.A_BOLD | self.cyan_text)
            self.stdscreen.addstr(self.row_max + 5, int(self.screen_width/2) + 2, '+ ' + 'width : ' + str(self.screen_width))
            self.stdscreen.addstr(self.row_max + 6, int(self.screen_width/2) + 2, '+ ' + 'heigh : ' + str(self.screen_height))
            self.stdscreen.addstr(self.row_max + 7, int(self.screen_width/2) + 2, '+ ' + 'key : ' + str(self.pkey))
            self.stdscreen.addstr(self.row_max + 8, int(self.screen_width/2) + 2, '+ ' + 'Search : ' + str(self.search))
            self.stdscreen.addstr(self.row_max + 9, int(self.screen_width/2) + 2, '+ ' + 'Search Index : ' + str(self.search_index))

    def MenuCloseCUI(self):
        ''' Close Menu '''

        # Init Menu
        cmsg = 'Shutdown kernel (default no) ? [y|n|q]'
        cmsg_width = len(cmsg) + 4
        menu_close = self.stdscreen.subwin(3, cmsg_width, int(self.screen_height/2), int((self.screen_width-cmsg_width)/2))
        menu_close.attrset(self.cyan_text)    # change border color
        menu_close.border(0)
        menu_close.keypad(1)

        # Send menu to a panel
        panel_close = panel.new_panel(menu_close)
        panel_close.top()        # Push the panel to the bottom of the stack.

        menu_close.addstr(1, 2, cmsg, curses.A_BOLD | self.red_text)
        panel_close.show()       # Display the panel (which might have been hidden)
        menu_close.refresh()
        curses.doupdate()

        # Wait for yes or no
        self.stdscreen.nodelay(False)
        self.pkey = -1
        while self.pkey not in (121, 110, 113, 89, 78, 27, ord("\n")):
            self.pkey = self.stdscreen.getch()
            sleep(0.1)

        # Erase the panel
        menu_close.clear()
        panel_close.hide()
        panel.update_panels()
        curses.doupdate()
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
