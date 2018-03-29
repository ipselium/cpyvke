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
# Last Modified : jeu. 29 mars 2018 23:38:17 CEST
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import curses
import locale

from cpyvke.curseswin.explorermenu import ExplorerMenu
from cpyvke.utils.display import whos_to_dic
from cpyvke.utils.comm import recv_msg
from cpyvke.objects.panel import ListPanel

locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()


class ExplorerWin(ListPanel):
    """ Variable explorer panel """

    def __init__(self, app, sock, logger):
        super(ExplorerWin, self).__init__(app, sock, logger)

    @property
    def panel_name(self):
        return 'variable-explorer'

    @property
    def title(self):
        return 'Variable Explorer'

    @property
    def empty(self):
        return 'Interactive namespace is empty'

    def color(self, item):
        if item == 'txt':
            return self.app.c_exp_txt
        elif item == 'bdr':
            return self.app.c_exp_bdr | curses.A_BOLD
        elif item == 'ttl':
            return self.app.c_exp_ttl | curses.A_BOLD
        elif item == 'hh':
            return self.app.c_exp_hh | curses.A_BOLD
        elif item == 'pwf':
            return self.app.c_exp_pwf | curses.A_BOLD

    def custom_tasks(self):
        """ Additional Explorer tasks """

        # Update variable number in bottom bar:
        self.app.var_nb = len(self.item_lst)

    def custom_key_bindings(self):
        """ Key Actions ! """

        # Menu KERNEL
        if self.pkey in [9, 75, ord('\t')]:    # -> TAB/K
            self.app.explorer_switch = True

        # Force Update Variable List sending fake code to daemon
        elif self.pkey == 114:   # -> r
            self.sock.force_update(self.app.wng)

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
                self.item_lst = whos_to_dic(tmp)
                self.logger.info('Variable list updated')
                self.logger.debug('\n%s', tmp)
                try:
                    # remove temporary file used by daemon from the list
                    del self.item_lst['fcpyvke0']
                except KeyError:
                    pass

        return self.item_lst

    def init_menu(self):
        """ Init variable menu """

        # First Update gwin (avoid bug)
        self.refresh()
        # Explorer Menu
        var_menu = ExplorerMenu(self.app, self.sock, self.logger, self)
        if var_menu.is_menu():
            var_menu.display()
            self.resize_curses(True)  # Fix brutal resize crash
