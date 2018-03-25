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
# Last Modified : dim. 25 mars 2018 23:12:24 CEST
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import os
import curses

from cpyvke.utils.kernel import kernel_dic, start_new_kernel, \
    shutdown_kernel, connect_kernel
from cpyvke.utils.comm import send_msg
from cpyvke.objects.panel import PanelWin


class KernelWin(PanelWin):

    def __init__(self, app, sock, logger):
        """ Class constructor """

        super(KernelWin, self).__init__(app, sock, logger)

        # Define Styles
        self.c_txt = self.app.c_kern_txt
        self.c_bdr = self.app.c_kern_bdr
        self.c_ttl = self.app.c_kern_ttl
        self.c_hh = self.app.c_kern_hh
        self.c_co = self.app.c_kern_co
        self.c_al = self.app.c_kern_al
        self.c_di = self.app.c_kern_di
        self.c_pwf = self.app.c_kern_pwf

        # Some strings
        self.win_title = ' Kernel Manager '
        self.empty_dic = 'No Kernels !'
        self.panel_name = 'kernel-manager'

        # Init Variable Box
        self.gwin.bkgd(self.c_txt)
        self.gwin.attrset(self.c_bdr | curses.A_BOLD)  # Change border color

    def get_items(self):
        """ Get items ! """

        self.app.cf = self.app.kc.connection_file

        return kernel_dic(self.app.cf)

    def custom_key_bindings(self):
        """ Key actions """

        # Menu EXPLORER
        if self.pkey in [9, 69, ord('\t')]:    # -> TAB/E
            self.app.kernel_switch = True

    def update_connection(self):
        """ Return cf and kc """

        return self.app.cf, self.app.kc

    def create_menu(self):
        """ Create the item list for the kernel menu  """

        if self.lst[self.selected]['type'] == 'Connected':
            return [('New', 'self._new_k()'),
                    ('Remove all died', 'self._rm_all_cf()'),
                    ('Shutdown all alive', 'self._kill_all_k()')]

        elif self.lst[self.selected]['type'] == 'Alive':
            return [('Connect', 'self._connect_k()'),
                    ('New', 'self._new_k()'),
                    ('Shutdown', 'self._kill_k()'),
                    ('Shutdown all alive', 'self._kill_all_k()'),
                    ('Remove all died', 'self._rm_all_cf()')]

        elif self.lst[self.selected]['type'] == 'Died':
            return [('Restart', 'self._restart_k()'),
                    ('New', 'self._new_k()'),
                    ('Remove file', 'self._rm_cf()'),
                    ('Remove all died', 'self._rm_all_cf()'),
                    ('Shutdown all alive', 'self._kill_all_k()')]

        else:
            return []

    def _new_k(self):
        """ Create a new kernel. """

        kid = start_new_kernel(version=self.app.config['kernel version']['version'])
        self.wng.display('Kernel id {} created (Python {})'.format(kid,
                                                                   self.app.config['kernel version']['version']))

    def _connect_k(self):
        """ Connect to a kernel. """

        km, self.app.kc = connect_kernel(self.lst[self.selected]['value'])
        send_msg(self.sock.RequestSock, '<cf>' + self.lst[self.selected]['value'])

        # Update kernels connection file and set new kernel flag
        self.app.cf = self.app.kc.connection_file
        self.app.kernel_change = True
        self.app.kernel_switch = True

    def _restart_k(self):
        """ Restart a died kernel. """

        self.wng.display('Not Implement yet!')

    def _kill_k(self):
        """ Kill kernel. """

        shutdown_kernel(self.lst[self.selected]['value'])
        self.position = 1
        self.page = 1

    def _kill_all_k(self):
        """ Kill all kernel marked as Alive. """

        for name in self.lst:
            if self.lst[name]['type'] == 'Alive':
                shutdown_kernel(self.lst[name]['value'])
        self.page = 1
        self.position = 1  # Reinit cursor location

    def _rm_cf(self):
        """ Remove connection file of died kernel. """

        os.remove(self.lst[self.selected]['value'])
        self.page = 1
        self.position = 1  # Reinit cursor location

    def _rm_all_cf(self):
        """ Remove connection files of all died kernels. """

        for name in self.lst:
            if self.lst[name]['type'] == 'Died':
                os.remove(self.lst[name]['value'])
        self.page = 1
        self.position = 1  # Reinit cursor location
