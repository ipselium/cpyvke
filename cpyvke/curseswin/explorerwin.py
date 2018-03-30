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
# Last Modified : ven. 30 mars 2018 17:28:02 CEST
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import curses
import locale
from curses import panel

from cpyvke.curseswin.classwin import ClassWin
from cpyvke.curseswin.widgets import Viewer
from cpyvke.utils.display import whos_to_dic
from cpyvke.utils.comm import recv_msg
from cpyvke.utils.inspector import ProceedInspection, Inspect
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
        self.app.var_nb = len(self.item_dic)

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
                self.item_dic = whos_to_dic(tmp)
                self.logger.info('Variable list updated')
                self.logger.debug('\n%s', tmp)
                try:
                    # remove temporary file used by daemon from the list
                    del self.item_dic['fcpyvke0']
                except KeyError:
                    pass

        return self.item_dic

    def menu_special_init(self):
        """ Additionnal menu init """

        # Save directory
        self.save_dir = self.app.config['path']['save-dir']

        # Variables properties
        self.varname = self.item_keys[self.position]
        self.vartype = self.item_dic[self.item_keys[self.position]]['type']
        self.varval = self.item_dic[self.item_keys[self.position]]['value']

        # Get Variable characteristics
        proc = ProceedInspection(self.app, self.sock, self.logger,
                                 self.varname, self.varval, self.vartype,
                                 self.position, self.page)
        self._ismenu, self.varname, self.varval, self.vartype, self.doc = proc.get_variable()

        # Init all Inspectors
        self.inspect = Inspect(self.varval, self.varname, self.vartype)
        self.class_win = ClassWin(self.app, self.sock, self.logger, self.varval, self.varname)
        self.view = Viewer(self.app, self.varval, self.varname)
        if self.doc:
            self.view_doc = Viewer(self.app, self.doc, self.varname)
            self.inspect_doc = Inspect(self.doc, self.varname, self.vartype)

    def create_menu(self):
        """ Create the item list for the general menu. """

        if self.varval == '[Busy]':
            return [('Busy', ' ')]

        elif self.vartype in self.inspect.type_numeric():
            return [('Delete', "self.sock.del_var(self.varname, self.app.wng)")]

        elif self.vartype in ['module']:
            return [('Help', "self.inspect.display('less', 'help')")]

        elif self.vartype in ['function']:
            return [('Help', 'self.view_doc.display()'),
                    ('Code', 'self.view.display()'),
                    ('Less help', "self.inspect_doc.display('less', 'help')"),
                    ('Less code', "self.inspect.display('less', 'help')")]

        elif self.vartype in ['builtin_function_or_method']:
            return [('Help', 'self.view_doc.display()'),
                    ('Less', "self.inspect_doc.display('less', 'help')")]

        elif self.vartype in self.inspect.type_struct():
            return [('View', 'self.view.display()'),
                    ('Less', "self.inspect.display('less')"),
                    ('Edit', "self.inspect.display('vim')"),
                    ('Save', "self.item_save()"),
                    ('Delete', "self.sock.del_var(self.varname, self.app.wng)")]

        elif (self.vartype == 'ndarray') and (len(self.varval.shape) == 1):
            return [('Plot', 'self.inspect.plot1D()'),
                    ('Save', 'self.menu_save()'),
                    ('Delete', "self.sock.del_var(self.varname, self.app.wng)")]

        elif (self.vartype == 'ndarray') and (len(self.varval.shape) == 2):
            return [('Plot 2D', 'self.inspect.plot2D()'),
                    ('Plot (cols)', 'self.inspect.plot1Dcols()'),
                    ('Plot (lines)', 'self.inspect.plot1Dlines()'),
                    ('Save', 'self.menu_save()'),
                    ('Delete', "self.sock.del_var(self.varname, self.app.wng)")]

        elif self.vartype in ['class', 'type']:
            return [('View', 'self.view.display()'),
                    ('Inspect', 'self.class_win.display()')]

        else:
            return [('No Option', 'exit')]

    def item_save(self):
        """ Item save in menu """

        self.inspect.save(self.save_dir)
        self.app.wng.display('Saved !')

    def menu_save(self):
        """ Create the save menu. """

        # Init Menu
        save_menu = self.app.stdscr.subwin(5, 6, self.menu_height, self.app.screen_width-9)
        save_menu.bkgd(self.color('txt'))
        save_menu.attrset(self.color('bdr'))
        save_menu.border(0)
        save_menu.keypad(1)

        # Send menu to a panel
        panel_save = panel.new_panel(save_menu)
        panel_save.hide()

        # Various variables
        self.menu_cursor = 0

        save_lst = [('txt', "self.inspect.save_np(self.varname, self.save_dir, 'txt')"),
                    ('npy', "self.inspect.save_np(self.varname, self.save_dir, 'npy')"),
                    ('npz', "self.inspect.save_np(self.varname, self.save_dir, 'npz')")]
        panel_save.top()        # Push the panel to the bottom of the stack.
        panel_save.show()       # Display the panel (which might have been hidden)
        save_menu.clear()

        menukey = -1
        while menukey not in self.app.kquit:

            self.logger.error('Save items : {}'.format(len(save_lst)))
            self.logger.error('Menu Cursor : {}'.format(self.menu_cursor))
            self.logger.error('Menu Key : {}'.format(menukey))

            save_menu.border(0)
            save_menu.refresh()

            # Fill the menu
            for index, item in enumerate(save_lst):
                if index == self.menu_cursor:
                    mode = self.color('hh')
                else:
                    mode = self.color('txt') | curses.A_DIM

                save_menu.addstr(1+index, 1, item[0], mode)

            menukey = save_menu.getch()

            if menukey in self.app.kenter:
                try:
                    eval(save_lst[self.menu_cursor][1])
                    self.app.wng.display('Saved !')
                except Exception:
                    self.app.wng.display('Not saved !')
                    self.logger.error('Menu save', exc_info=True)
                else:
                    self.menu_cursor = 0
                    break

            elif menukey in self.app.kup:
                self.navigate_menu(-1, len(save_lst))

            elif menukey in self.app.kdown:
                self.navigate_menu(1, len(save_lst))

            elif menukey == curses.KEY_RESIZE:
                self.menu_cursor = 0
                break

        save_menu.clear()
        panel_save.hide()
