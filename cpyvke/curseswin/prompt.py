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
# Last Modified : mar. 03 avril 2018 11:12:09 CEST
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import curses
from curses import panel


def cmd_lst():
    """ Prompt command list """

    lst = ['kernel-manager',
           'daemon-restart-connection', 'daemon-connect', 'daemon-disconnect',
           'daemon-restart',
           'help',
           'variable-explorer',
           'toggle-debug']
    lst.sort()

    return lst


class Prompt:
    """ Prompt class.

    Prompt.simple : simple prompt that returns a user input
    Prompt.with_completion : Prompt with completion capabitilies that returns a user input
    Prompt.panel : a simple prompt in a panel that returns a user input

    """

    def __init__(self, app):
        """ Class constructor """

        # Arguments
        self.app = app
        self.config = app.config

        # Init input
        self.usr_input = ''

        # Screen
        self.stdscr = app.stdscr

    def simple(self, prefix):
        """ Display prompt and return user input. """

        # Reinit input
        self.usr_input = ''

        # Enable echoing of characters
        curses.echo()
        self.app.stdscr.attrset(self.app.c_main_txt | curses.A_BOLD)
        # Erase before ! (overwrite with spaces)
        self.app.stdscr.addstr(self.app.screen_height-1, 0,
                               ' '*(self.app.screen_width-1),
                               curses.A_DIM | self.app.c_main_txt)

        self.app.stdscr.addstr(self.app.screen_height-1, 0, prefix, curses.A_DIM | self.app.c_main_txt)
        self.usr_input = self.app.stdscr.getstr(self.app.screen_height-1, len(prefix),
                                                self.app.screen_width - len(prefix) - 1).decode('utf-8')
        # Disable echoing of characters
        curses.noecho()
        # Restore color of the main window
        self.app.stdscr.attrset(self.app.c_main_bdr | curses.A_BOLD)

        return self.usr_input

    def with_completion(self, prefix):
        """ Display prompt with completion and return user input. """

        # Reinit input
        self.usr_input = ''
        self.app.stdscr.attrset(self.app.c_main_txt | curses.A_BOLD)
        # Enable echoing of characters
        curses.echo()
        curses.halfdelay(1)

        mkey = ''
        pkey = -1
        while pkey not in ['\n']:    # ESC/ENTER

            try:
                # get_wch return a character for most keys, or an integer
                # for function keys, keypad keys, and other special keys
                if not mkey:
                    pkey = self.app.stdscr.get_wch()

                else:
                    pkey = mkey
                    mkey = ''

                if pkey in ['^[', 27, curses.KEY_RESIZE]:
                    self.usr_input = ''
                    break

                elif pkey in ['\t']:    # TAB
                    match = [cmd for cmd in cmd_lst() if cmd.startswith(self.usr_input)]

                    if not match:
                        pass
                    elif len(match) == 1:
                        self.usr_input = match[0]
                    else:
                        mkey = self._complete(match, prefix)

                elif pkey in [263]:    # DEL
                    self.usr_input = self.usr_input[:-1]
                    if not self.usr_input:
                        break

                elif type(pkey) is not int and len(self.usr_input + pkey.rstrip()) < self.app.screen_width - 2:
                    self.usr_input = self.usr_input + pkey.rstrip()

            except curses.error:
                pass

            # Erase before ! (overwrite with space characters)
            self.app.stdscr.addstr(self.app.screen_height-1, 0,
                                   ' '*(self.app.screen_width-1),
                                   curses.A_BOLD | self.app.c_main_txt)

            self.app.stdscr.addstr(self.app.screen_height-1, 0,
                                   prefix + self.usr_input,
                                   curses.A_BOLD | self.app.c_main_txt)

        # Restore color of the main window and switch of echo !
        curses.noecho()
        self.app.stdscr.attrset(self.app.c_main_bdr | curses.A_BOLD)

        return self.usr_input

    def _complete(self, match, prefix):
        """ Completion method """

        mkey = -1
        i = 0
        proposal = match[0]
        while mkey not in ['\n']:
            try:
                mkey = self.app.stdscr.get_wch()
                if mkey in ['\t'] and i < len(match) - 1:
                    i += 1
                    proposal = match[i]
                    if i == len(match) - 1:
                        i = -1
                elif mkey not in ['\t', '\n']:
                    return mkey
            except curses.error:
                pass

            self.app.stdscr.addstr(self.app.screen_height-1, 0,
                                   ' '*(self.app.screen_width-1),
                                   curses.A_BOLD | self.app.c_main_txt)
            self.app.stdscr.addstr(self.app.screen_height-1, 0,
                                   prefix + proposal, curses.A_DIM | self.app.c_main_txt)
            self.app.stdscr.addstr(self.app.screen_height-1, 0,
                                   prefix + self.usr_input, curses.A_BOLD | self.app.c_exp_txt)

        self.usr_input = match[i]
        return mkey

    def display(self, msg):
        """ display message in prompt. """

        self.app.stdscr.addstr(self.app.screen_height-1, 0,
                               msg, curses.A_BOLD | self.app.c_warn_txt)

    def panel(self, txt_msg, win_title):
        """ Prompt on a dedicated panel """

        # Init Menu
        self.win_title = win_title
        iwin = self.app.stdscr.subwin(self.app.panel_height, self.app.screen_width, 0, 0)
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
        self.usr_input = iwin.getstr(2, len(txt_msg) + 4,
                                     self.app.screen_width - len(txt_msg) - 8).decode('utf-8')
        curses.noecho()
        ipan.hide()

        return self.usr_input
