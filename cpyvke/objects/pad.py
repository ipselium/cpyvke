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
# Last Modified : jeu. 22 mars 2018 23:51:43 CET
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import curses
from curses import panel
import locale

code = locale.getpreferredencoding()


class PadWin:
    """ General Pad example """

    def __init__(self, app):
        """ CLass constructor """

        # Arguments
        self.app = app
        self.config = app.config

        # Define Style
        self.c_txt = app.c_exp_txt
        self.c_bdr = app.c_exp_bdr
        self.c_ttl = app.c_exp_ttl
        self.c_hh = app.c_exp_hh
        self.c_pwf = app.c_exp_pwf

        # Bindings
        self.kup = app.kup
        self.kdown = app.kdown
        self.kright = app.kright
        self.kleft = app.kleft
        self.kquit = app.kquit

        # Screen
        self.stdscr = app.stdscr
        self.screen_height, self.screen_width = self.stdscr.getmaxyx()

        # Create content
        self.title = ' ' + 'Pad Test' + ' '
        self.content = self.create_content()

    def create_content(self):
        """ Create content of the pad """

        content = [str(i) for i in range(50)]
        content[0] = 'This is...'
        content[1] = '... a very very long Example'

        return content

    def init_pad(self):
        """ Init Pad """

        self.pad_width = max(len(self.title),
                             max([len(elem) for elem in self.content])) + 8
        self.pad_width = min(self.pad_width, self.screen_width-2)
        self.pad_height = len(self.content) + 2
        self.gpad = curses.newpad(self.pad_height, self.pad_width)
        self.gpad.keypad(1)
        self.gpad.bkgd(self.c_txt)
        self.gpad.attrset(self.c_bdr | curses.A_BOLD)
        self.gpad.border(0)
        self.title_loc = int((self.pad_width - len(self.title) - 2)/2)

        # Pad content
        for i, j in enumerate(self.content):
            self.gpad.addstr(1+i, 3, j.encode(code), self.c_txt)

        # Pad title
        if self.config['font']['pw-font'] == 'True':
            self.gpad.addstr(0, self.title_loc,
                             '', self.c_pwf | curses.A_BOLD)
            self.gpad.addstr(self.title, self.c_ttl | curses.A_BOLD)
            self.gpad.addstr('', self.c_pwf | curses.A_BOLD)
        else:
            self.gpad.addstr(0, self.title_loc,
                             '|' + self.title + '|', self.c_ttl | curses.A_BOLD)

    def display(self):
        """ Create pad to display variable content. """

        self.init_pad()

        key = -1
        pad_pos = 0
        pad_y = max(self.pad_height,
                    self.screen_height - 2) - (self.screen_height - 2)

        while key not in self.kquit:
            if key in self.kdown:
                pad_pos = min(pad_y, pad_pos+1)
            elif key in self.kup:
                pad_pos = max(0, pad_pos-1)
            elif key in self.kright:
                pad_pos = min(pad_y, pad_pos+5)
            elif key in self.kleft:
                pad_pos = max(0, pad_pos-5)
            elif key == curses.KEY_NPAGE:
                pad_pos = min(pad_y, pad_pos+10)
            elif key == curses.KEY_PPAGE:
                pad_pos = max(0, pad_pos-10)
            elif key == 262:
                pad_pos = 0
            elif key == 360:
                pad_pos = pad_y

            self.gpad.refresh(pad_pos, 0, 1, 1,
                              self.screen_height-2, self.screen_width-2)

            key = self.gpad.getch()

            if key == curses.KEY_RESIZE:
                break

        self.gpad.erase()


class Prompt:
    """ Prompt class. """

    def __init__(self, app):
        """ CLass constructor """

        # Arguments
        self.app = app
        self.config = app.config

        # Screen
        self.stdscr = app.stdscr

    def display(self, key):
        """ Display prompt and return user input. """

        # Dimensions of the main window
        self.app.screen_height, self.app.screen_width = self.stdscr.getmaxyx()

        # Enable echoing of characters
        curses.echo()
        self.app.stdscr.attrset(self.app.c_main_txt | curses.A_DIM)
        # Erase before ! (overwrite with spaces)
        self.app.stdscr.addstr(self.app.screen_height-2, 2,
                               ' '*(self.app.screen_width-4),
                               curses.A_DIM | self.app.c_main_txt)

        self.app.stdscr.addstr(self.app.screen_height-2, 2, key, curses.A_DIM | self.app.c_main_txt)
        usr_input = self.app.stdscr.getstr(self.app.screen_height-2, 2 + len(key),
                                           self.app.screen_width - len(key) - 8).decode('utf-8')
        # Disable echoing of characters
        curses.noecho()
        # Restore color of the main window
        self.app.stdscr.attrset(self.app.c_main_bdr | curses.A_BOLD)

        return usr_input

    def message(self, msg):
        """ display message in prompt. """

        self.app.stdscr.addstr(self.app.screen_height-2, 2,
                               msg, curses.A_BOLD | self.app.c_warn_txt)

    def input_panel(self, txt_msg, win_title):
        """ Prompt on a dedicated panel """

        # Dimensions of the main window
        self.app.screen_height, self.app.screen_width = self.stdscr.getmaxyx()

        # Init Menu
        self.win_title = win_title
        iwin = self.app.stdscr.subwin(self.app.row_max+2, self.app.screen_width-2, 1, 1)
        iwin.keypad(1)

        # Send menu to a panel
        ipan = panel.new_panel(iwin)

        ipan.top()        # Push the panel to the bottom of the stack.
        ipan.show()       # Display the panel (which might have been hidden)
        iwin.clear()
        iwin.bkgd(self.app.c_main_txt)
        iwin.attrset(self.app.c_main_bdr | curses.A_BOLD)  # Change border color
        iwin.border(0)
        if self.app.config['font']['pw-font'] == 'True':
            iwin.addstr(0, int((self.app.screen_width-len(self.win_title))/2),
                        '', self.app.c_main_pwf)
            iwin.addstr(self.win_title, self.app.c_main_ttl | curses.A_BOLD)
            iwin.addstr('', self.app.c_main_pwf)
        else:
            iwin.addstr(0, int((self.app.screen_width-len(self.win_title))/2),
                        '| ' + self.win_title + ' |', self.app.c_main_ttl | curses.A_BOLD)

        curses.echo()
        iwin.addstr(2, 3, txt_msg, curses.A_BOLD | self.app.c_main_txt)
        usr_input = iwin.getstr(2, len(txt_msg) + 4,
                                self.app.screen_width - len(txt_msg) - 8).decode('utf-8')
        curses.noecho()
        ipan.hide()

        return usr_input
