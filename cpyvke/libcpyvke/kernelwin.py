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
# Last Modified : mer. 14 mars 2018 23:39:31 CET
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import os
import curses

from ..utils.kernel import kernel_list, start_new_kernel, shutdown_kernel, connect_kernel
from ..utils.comm import send_msg
from .widgets import WarningMsg
from .temppanel import PanelWin


class KernelWin(PanelWin):

    def __init__(self, *args, **kwargs):
        """ Class constructor """

        # Inherit parent class attributes
        super(KernelWin, self).__init__(*args, **kwargs)

        # Socket
        self.RequestSock = self.parent.RequestSock

        # Queue for kernel changes
        self.kc = self.parent.kc

        # Define Styles
        self.Config = self.parent.Config
        self.c_txt = self.parent.c_kern_txt
        self.c_bdr = self.parent.c_kern_bdr
        self.c_ttl = self.parent.c_kern_ttl
        self.c_hh = self.parent.c_kern_hh
        self.c_co = self.parent.c_kern_co
        self.c_al = self.parent.c_kern_al
        self.c_di = self.parent.c_kern_di
        self.c_pwf = self.parent.c_kern_pwf

    def get_items(self):
        """ Get items ! """

        self.cf = self.kc.connection_file

        return kernel_list(self.cf)

    def update_lst(self):
        """ Update the kernel list """

        if self.Config['font']['pw-font'] == 'True':
            self.gwin.addstr(0, int((self.screen_width-len(self.win_title))/2),
                             '', curses.A_BOLD | self.c_pwf)
            self.gwin.addstr(self.win_title, curses.A_BOLD | self.c_ttl)
            self.gwin.addstr('', curses.A_BOLD | self.c_pwf)
        else:
            self.gwin.addstr(0, int((self.screen_width-len(self.win_title))/2),
                             '|' + self.win_title + '|',
                             curses.A_BOLD | self.c_ttl)

        for i in range(1+(self.row_max*(self.page-1)),
                       self.row_max+1+(self.row_max*(self.page-1))):

            if self.row_num == 0:
                self.gwin.addstr(1, 1, "No kernel available",
                                 self.c_hh | curses.A_BOLD)

            else:
                if (i+(self.row_max*(self.page-1)) == self.position+(self.row_max*(self.page-1))):
                    self.gwin.addstr(i, 2, self.lst[i-1][0].ljust(self.screen_width-5),
                                     self.c_hh | curses.A_BOLD)
                    if str(self.lst[i-1][1]) == "[Died]":
                        self.gwin.addstr(i, self.screen_width-15,
                                         str(self.lst[i-1][1]),
                                         curses.A_BOLD | self.c_di)
                    elif str(self.lst[i-1][1]) == "[Alive]":
                        self.gwin.addstr(i, self.screen_width-15,
                                         str(self.lst[i-1][1]),
                                         curses.A_BOLD | self.c_al)
                    elif str(self.lst[i-1][1]) == "[Connected]":
                        self.gwin.addstr(i, self.screen_width-15,
                                         str(self.lst[i-1][1]),
                                         curses.A_BOLD | self.c_co)
                else:
                    self.gwin.addstr(i, 2,
                                     self.lst[i-1][0].ljust(self.screen_width-5),
                                     self.c_txt | curses.A_DIM)
                    if str(self.lst[i-1][1]) == "[Died]":
                        self.gwin.addstr(i, self.screen_width-15,
                                         str(self.lst[i-1][1]),
                                         curses.A_BOLD | self.c_di)
                    elif str(self.lst[i-1][1]) == "[Alive]":
                        self.gwin.addstr(i, self.screen_width-15,
                                         str(self.lst[i-1][1]),
                                         curses.A_BOLD | self.c_al)
                    elif str(self.lst[i-1][1]) == "[Connected]":
                        self.gwin.addstr(i, self.screen_width-15,
                                         str(self.lst[i-1][1]),
                                         curses.A_BOLD | self.c_co)
                if i == self.row_num:
                    break

        self.stdscreen.refresh()
        self.gwin.refresh()

    def update_connection(self):
        """ Return cf and kc """

        return self.cf, self.kc

    def create_menu(self):
        """ Create the item list for the kernel menu  """

        if self.selected[1] == '[Connected]':
            return [('New', 'self._new_k()'),
                    ('Remove all died', 'self._rm_all_cf()'),
                    ('Shutdown all alive', 'self._kill_all_k()')]

        elif self.selected[1] == '[Alive]':
            return [('Connect', 'self._connect_k()'),
                    ('New', 'self._new_k()'),
                    ('Shutdown', 'self._kill_k()'),
                    ('Shutdown all alive', 'self._kill_all_k()'),
                    ('Remove all died', 'self._rm_all_cf()')]

        elif self.selected[1] == '[Died]':
            return [('Restart', 'self._restart_k()'),
                    ('New', 'self._new_k()'),
                    ('Remove file', 'self._rm_cf()'),
                    ('Remove all died', 'self._rm_all_cf()'),
                    ('Shutdown all alive', 'self._kill_all_k()')]

        else:
            return []

    def _new_k(self):
        """ Create a new kernel. """

        kid = start_new_kernel(version=self.Config['kernel version']['version'])
        msg = WarningMsg(self.stdscreen)
        msg.Display('Kernel id {} created (Python {})'.format(kid,
                    self.Config['kernel version']['version']))

    def _connect_k(self):
        """ Connect to a kernel. """

        km, self.kc = connect_kernel(self.selected[0])
        send_msg(self.RequestSock, '<cf>' + self.selected[0])

        # Update kernels connection file and set new kernel flag
        self.cf = self.kc.connection_file
        self.quit = True

    def _restart_k(self):
        """ Restart a died kernel. """

        msg = WarningMsg(self.stdscreen)
        msg.Display('Not Implement yet!')

    def _kill_k(self):
        """ Kill kernel. """

        shutdown_kernel(self.selected[0])
        self.position = 1
        self.page = 1

    def _kill_all_k(self):
        """ Kill all kernel marked as Alive. """

        for json_path, status in self.lst:
            if status == '[Alive]':
                shutdown_kernel(json_path)
        self.page = 1
        self.position = 1  # Reinit cursor location

    def _rm_cf(self):
        """ Remove connection file of died kernel. """

        os.remove(self.selected[0])
        self.page = 1
        self.position = 1  # Reinit cursor location

    def _rm_all_cf(self):
        """ Remove connection files of all died kernels. """

        for json_path, status in self.lst:
            if status == '[Died]':
                os.remove(json_path)
        self.page = 1
        self.position = 1  # Reinit cursor location
