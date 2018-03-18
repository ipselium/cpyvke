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
# Last Modified : dim. 18 mars 2018 22:38:49 CET
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import curses
import locale

from cpyvke.curseswin.varmenu import ExplorerMenu
from cpyvke.curseswin.widgets import WarningMsg
from cpyvke.utils.display import whos_to_dic
from cpyvke.utils.comm import recv_msg
from cpyvke.objects.panel import PanelWin

locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()


class ExplorerWin(PanelWin):
    """ Main window. """

    def __init__(self, app, sock, logger):
        """ Main window constructor """

        super(ExplorerWin, self).__init__(app, sock, logger)

        # Various Variables :
        self.win_title = "Variable Explorer"
        self.empty_dic = "Interactive namespace is empty"
        self.wng_msg = ""

        # Init Variable Box
        self.gwin.bkgd(self.app.c_exp_txt)
        self.gwin.attrset(self.app.c_exp_bdr | curses.A_BOLD)  # border color

    def custom_tasks(self):
        """ Additional Explorer tasks """

        if self.app.kernel_change:
            self.app.kernel_change = False
            wng_msg = WarningMsg(self.app.stdscr)
            self.sock.force_update(wng_msg)

    def custom_key_bindings(self):
        """ Key Actions ! """

        # Init Warning Msg
        wng_msg = WarningMsg(self.app.stdscr)

        # Menu KERNEL
        if self.pkey in [9, 75, ord('\t')]:    # -> TAB/K
            self.switch = True

        # Force Update Variable List sending fake code to daemon
        elif self.pkey == 114:   # -> r
            self.sock.force_update(wng_msg)

    def get_items(self):
        """ Get variable from the daemon """

        try:
            tmp = recv_msg(self.sock.MainSock).decode('utf8')
        except BlockingIOError:     # If no message !
            pass
        except OSError:             # If user disconnect cpyvke from socket
            pass
        except AttributeError:      # If kd5 is stopped
            pass
        else:
            if tmp:
                self.lst = whos_to_dic(tmp)
                self.logger.info('Variable list updated')
                self.logger.debug('\n%s', tmp)
                try:
                    # remove temporary file used by daemon from the list
                    del self.lst['fcpyvke0']
                except KeyError:
                    pass

        return self.lst

    def init_menu(self):
        """ Init variable menu """

        # First Update gwin (avoid bug)
        self.refresh()
        # Explorer Menu
        var_menu = ExplorerMenu(self.app, self.sock, self.logger, self)
        if var_menu.is_menu():
            var_menu.display()
