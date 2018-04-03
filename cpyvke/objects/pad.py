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
# Last Modified : lun. 02 avril 2018 13:27:47 CEST
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import curses
import locale
import abc


code = locale.getpreferredencoding()


class PadWin(abc.ABC):
    """ General Pad Abstract Class """

    def __init__(self, app):

        self.app = app

    @abc.abstractmethod
    def color(self, item):
        """ Pad colors """

    @property
    @abc.abstractmethod
    def title(self):
        """ Pad Title. Must be a string """

    @property
    @abc.abstractmethod
    def content(self):
        """ Pad content. Must return a list ! """

    def init_pad(self):
        """ Init Pad """

        self.pad_width = max(len(self.title),
                             max([len(elem) for elem in self.content])) + 8
        self.pad_width = min(self.pad_width, self.app.screen_width-2)
        self.pad_height = len(self.content) + 2
        self.gpad = curses.newpad(self.pad_height, self.pad_width)
        self.gpad.keypad(1)
        self.gpad.bkgd(self.color('txt'))
        self.gpad.attrset(self.color('bdr'))
        self.gpad.border(0)
        self.title_loc = int((self.pad_width - len(self.title) - 2)/2)

        # Pad content
        for i, j in enumerate(self.content):
            self.gpad.addstr(1+i, 3, j.encode(code), self.color('txt'))

        # Pad title
        if self.app.config['font']['pw-font'] == 'True':
            self.gpad.addstr(0, self.title_loc, '', self.color('pwf'))
            self.gpad.addstr(self.title, self.color('ttl'))
            self.gpad.addstr('', self.color('pwf'))
        else:
            self.gpad.addstr(0, self.title_loc, '|' + self.title + '|',
                             self.color('ttl'))

    def display(self):
        """ Create pad to display variable content. """

        self.init_pad()

        pkey = -1
        pad_pos = 0
        pad_y = max(self.pad_height,
                    self.app.screen_height - 2) - (self.app.screen_height - 2)

        while pkey not in self.app.kquit:
            if pkey in self.app.kdown:
                pad_pos = min(pad_y, pad_pos+1)
            elif pkey in self.app.kup:
                pad_pos = max(0, pad_pos-1)
            elif pkey in self.app.kright:
                pad_pos = min(pad_y, pad_pos+5)
            elif pkey in self.app.kleft:
                pad_pos = max(0, pad_pos-5)
            elif pkey == curses.KEY_NPAGE:
                pad_pos = min(pad_y, pad_pos+10)
            elif pkey == curses.KEY_PPAGE:
                pad_pos = max(0, pad_pos-10)
            elif pkey == 262:               # Home
                pad_pos = 0
            elif pkey == 360:               # End
                pad_pos = pad_y
            elif pkey == curses.KEY_RESIZE:
                break

            self.gpad.refresh(pad_pos, 0, 1, 1,
                              self.app.screen_height-2, self.app.screen_width-2)

            pkey = self.gpad.getch()

        self.gpad.erase()
