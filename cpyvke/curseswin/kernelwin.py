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
# Last Modified : ven. 30 mars 2018 17:28:23 CEST
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
from cpyvke.objects.panel import ListPanel


class KernelWin(ListPanel):
    """ Kernel manager panel """

    def __init__(self, app, sock, logger):
        super(KernelWin, self).__init__(app, sock, logger)

    @property
    def panel_name(self):
        return 'kernel-manager'

    @property
    def title(self):
        return ' Kernel Manager '

    @property
    def empty(self):
        return 'No Kernels !'

    def color(self, item):
        if item == 'txt':
            return self.app.c_kern_txt
        elif item == 'bdr':
            return self.app.c_kern_bdr | curses.A_BOLD
        elif item == 'ttl':
            return self.app.c_kern_ttl | curses.A_BOLD
        elif item == 'hh':
            return self.app.c_kern_hh | curses.A_BOLD
        elif item == 'co':
            return self.app.c_kern_co | curses.A_BOLD
        elif item == 'al':
            return self.app.c_kern_al | curses.A_BOLD
        elif item == 'di':
            return self.app.c_kern_di | curses.A_BOLD
        elif item == 'pwf':
            return self.app.c_kern_pwf | curses.A_BOLD

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

        if self.item_dic[self.selected]['type'] == 'Connected':
            return [('New', 'self._new_k()'),
                    ('Remove all died', 'self._rm_all_cf()'),
                    ('Shutdown all alive', 'self._kill_all_k()')]

        elif self.item_dic[self.selected]['type'] == 'Alive':
            return [('Connect', 'self._connect_k()'),
                    ('New', 'self._new_k()'),
                    ('Shutdown', 'self._kill_k()'),
                    ('Shutdown all alive', 'self._kill_all_k()'),
                    ('Remove all died', 'self._rm_all_cf()')]

        elif self.item_dic[self.selected]['type'] == 'Died':
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
        self.app.wng.display('Kernel id {} created (Python {})'.format(kid,
                                                                       self.app.config['kernel version']['version']))

    def _connect_k(self):
        """ Connect to a kernel. """

        km, self.app.kc = connect_kernel(self.item_dic[self.selected]['value'])
        send_msg(self.sock.RequestSock, '<cf>' + self.item_dic[self.selected]['value'])

        # Update kernels connection file and set new kernel flag
        self.app.cf = self.app.kc.connection_file
        self.app.kernel_change = True
        self.app.kernel_switch = True

    def _restart_k(self):
        """ Restart a died kernel. """

        self.app.wng.display("Not implemented yet")
        #  restart_kernel(self.item_dic[self.selected]['value'])

    def _kill_k(self):
        """ Kill kernel. """

        shutdown_kernel(self.item_dic[self.selected]['value'])
        self.position = 1
        self.page = 1

    def _kill_all_k(self):
        """ Kill all kernel marked as Alive. """

        for name in self.item_dic:
            if self.item_dic[name]['type'] == 'Alive':
                shutdown_kernel(self.item_dic[name]['value'])
        self.page = 1
        self.position = 1  # Reinit cursor location

    def _rm_cf(self):
        """ Remove connection file of died kernel. """

        os.remove(self.item_dic[self.selected]['value'])
        self.page = 1
        self.position = 1  # Reinit cursor location

    def _rm_all_cf(self):
        """ Remove connection files of all died kernels. """

        for name in self.item_dic:
            if self.item_dic[name]['type'] == 'Died':
                os.remove(self.item_dic[name]['value'])
        self.page = 1
        self.position = 1  # Reinit cursor location
