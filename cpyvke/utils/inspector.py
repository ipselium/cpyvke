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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with cpyvke.  If not, see <http://www.gnu.org/licenses/>.
#
#
# Creation Date : Wed Nov  9 16:27:41 2016
# Last Modified : sam. 17 mars 2018 11:49:29 CET
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import curses
from matplotlib.pyplot import figure, plot, imshow, show
import numpy as np
import os
import json
from time import time, sleep
from multiprocessing import Process
import subprocess
import sys
import locale

from cpyvke.curseswin.widgets import suspend_curses
from cpyvke.utils.comm import send_msg


locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()


def inspect_class_instance(class_inst):
    return {i: {'type': str(type(class_inst.__class__.__dict__[i])),
                'value': str(class_inst.__class__.__dict__[i])} for i in
            class_inst.__class__.__dict__ if not i.startswith('_')}


def In_Thread(Func):
    """ Run Func in thread """
    def run(*k, **kw):
        t = Process(target=Func, args=k, kwargs=kw)
        t.start()
        return t
    return run


class Inspect:
    """ Plot/Display variable. """

    def __init__(self, varval, varname, vartype):

        self.varval = varval
        self.vartype = vartype
        self.varname = varname

    @In_Thread
    def Plot2D(self):
        """ Plot 2D variable. """

        figure()
        imshow(self.varval)
        show()

    @In_Thread
    def Plot1D(self):
        """ Plot 1D variable. """

        figure()
        plot(self.varval)
        show()

    @In_Thread
    def Plot1Dcols(self):
        """ Plot 2D variable : superimpose all columns """

        figure()
        for i in range(np.shape(self.varval)[1]):
            plot(self.varval[:, i])
        show()

    @In_Thread
    def Plot1Dlines(self):
        """ Plot 2D variable : superimpose all lines """

        figure()
        for i in range(np.shape(self.varval)[0]):
            plot(self.varval[i, :])
        show()

    def SaveNP(self, varname, SaveDir, METHOD='npy'):
        """ Save numpy variable to file """

        if METHOD == 'txt':
            np.savetxt(SaveDir + varname + '.txt', self.varval)

        if METHOD == 'npy':
            np.save(SaveDir + varname, self.varval)

        if METHOD == 'npz':
            np.savez_compressed(SaveDir + varname, var=self.varval)

    def Save(self, SaveDir):
        """ Save variable to text file """

        filename = SaveDir + self.varname

        if self.vartype != 'str' and self.vartype != 'unicode':
            self.varval = str(self.varval)

        if self.vartype == 'unicode':
            with open(filename, 'w') as f:
                f.write(self.varval.encode(code))

        else:
            with open(filename, 'w') as f:
                f.write(self.varval)

    def Display(self, app='less', Arg='Help'):
        """
        Display variable using **App** (less|vim).
        If a module is provided, use **Arg** to choose wich methode to use.
        """

        filename = '/tmp/tmp_cVKE'

        # Convert all type of variable to string
        if self.vartype != 'str' and self.vartype != 'unicode':
            self.varval = str(self.varval)

        #
        if self.vartype == 'unicode':
            with open(filename, 'w') as f:
                f.write(self.varval.encode(code))

        elif self.vartype == 'function':
            if Arg == 'Help':
                with open(filename, 'w') as f:
                    f.write(self.varval)

        elif self.vartype == 'module':
            if Arg == 'Help':
                sys.stdout = open(filename, 'w')
                print(help(self.varval))

        else:
            with open(filename, 'w') as f:
                f.write(self.varval)

        with suspend_curses():
            subprocess.run([app, filename])
            subprocess.run(['rm', filename])


class ProceedInspection:
    """ Object inspection """

    def __init__(self, app, sock, logger, name, value, typ, pos, page, rmax, wng):
        """ Class constructor """

        self.app = app
        self.sock = sock
        self.logger = logger
        self.varname = name
        self.varval = value
        self.vartype = typ
        self.position = pos
        self.page = page
        self.row_max = rmax
        self.wng = wng

    def get_variable(self):
        """ Get Variable characteristics. """
        if self.vartype == 'module':
            self.get_module()

        elif self.vartype in ('dict', 'list', 'tuple', 'str', 'unicode'):
            self.get_structure()

        elif self.vartype == 'ndarray':
            self.get_ndarray()

        elif '.' + self.vartype in self.varval:     # Class
            self.get_class()

        else:
            self.varval = '[Not Impl.]'
            self._ismenu = True

        return self._ismenu, self.varname, self.varval, self.vartype

    def get_class(self):
        """ Get Class characteristics. """

        self.vartype = 'class'
        self.filename = '/tmp/tmp_' + self.varname
        self.code = "with open('{}' , 'w') as fcpyvke0:\n\t_json.dump(_inspect.inspect_class_instance({}), fcpyvke0)".format(self.filename, self.varname)
        self.send_code()

    def get_module(self):
        """ Get modules characteristics """

        self.filename = '/tmp/tmp_' + self.varname
        self.code = "with open('{}' , 'w') as fcpyvke0:\n\t_json.dump({}.__name__, fcpyvke0)".format(self.filename, self.varname)
        self.send_code()

    def get_structure(self):
        """ Get Dict/List/Tuple characteristics """

        self.filename = '/tmp/tmp_' + self.varname
        self.code = "with open('{}' , 'w') as fcpyvke0:\n\t_json.dump({}, fcpyvke0)".format(self.filename, self.varname)
        self.send_code()

    def get_ndarray(self):
        """ Get ndarray characteristics. """

        self.filename = '/tmp/tmp_' + self.varname + '.npy'
        code = "_np.save('" + self.filename + "', " + self.varname + ')'
        try:
            send_msg(self.sock.RequestSock, '<code>' + code)
            self.logger.debug("Name of module '{}' asked to kd5".format(self.varname))
            self.wait()
            self.varval = np.load(self.filename)
        except Exception:
            self.logger.error('Get traceback : ', exc_info=True)
            self.kernel_busy()
        else:
            self.logger.debug('kd5 answered')
            os.remove(self.filename)
            self._ismenu = True

    def get_help(self):
        """ Help item in menu """

        if self.vartype == 'function':
            self.filename = '/tmp/tmp_' + self.varname
            self.code = "with open('{}' , 'w') as fcpyvke0:\n\t_json.dump({}.__doc__, fcpyvke0)".format(self.filename, self.varname)
            self.send_code()

    def send_code(self):
        """ Send code to kernel and except answer ! """

        try:
            send_msg(self.sock.RequestSock, '<code>' + self.code)
            self.logger.debug("Inspecting '{}'".format(self.varname))
            self.wait()
            with open(self.filename, 'r') as f:
                self.varval = json.load(f)
        except Exception:
            self.logger.error('Get traceback', exc_info=True)
            self.kernel_busy()
        else:
            self.logger.debug('kd5 answered')
            os.remove(self.filename)
            self._ismenu = True

    def kernel_busy(self):
        """ Handle silent kernel. """

        self.wng.Display('Kernel Busy ! Try again...')
        self.varval = '[Busy]'
        self._ismenu = False

    def wait(self):
        """ Wait for variable value. """

        i = 0
        spinner = [['.', 'o', 'O', 'o'],
                   ['.', 'o', 'O', '@', '*'],
                   ['v', '<', '^', '>'],
                   ['(o)(o)', '(-)(-)', '(_)(_)'],
                   ['◴', '◷', '◶', '◵'],
                   ['←', '↖', '↑', '↗', '→', '↘', '↓', '↙'],
                   ['▁', '▃', '▄', '▅', '▆', '▇', '█', '▇', '▆', '▅', '▄', '▃'],
                   ['▉', '▊', '▋', '▌', '▍', '▎', '▏', '▎', '▍', '▌', '▋', '▊', '▉'],
                   ['▖', '▘', '▝', '▗'],
                   ['▌', '▀', '▐', '▄'],
                   ['┤', '┘', '┴', '└', '├', '┌', '┬', '┐'],
                   ['◢', '◣', '◤', '◥'],
                   ['◰', '◳', '◲', '◱'],
                   ['◐', '◓', '◑', '◒'],
                   ['|', '/', '-', '\\'],
                   ['.', 'o', 'O', '@', '*'],
                   ['◡◡', '⊙⊙', '◠◠'],
                   ['◜ ', ' ◝', ' ◞', '◟ '],
                   ['◇', '◈', '◆'],
                   ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷'],
                   ['⠁', '⠂', '⠄', '⡀', '⢀', '⠠', '⠐', '⠈'],
                   ['Searching.', 'Searching..', 'Searching...']
                   ]

        spinner = spinner[19]
        ti = time()
        while os.path.exists(self.filename) is False:
            sleep(0.05)
            self.app.stdscr.addstr(self.position - (self.page-1)*self.row_max + 1,
                                   2, spinner[i], self.app.c_exp_txt | curses.A_BOLD)

            self.app.stdscr.refresh()
            if i < len(spinner) - 1:
                i += 1
            else:
                i = 0

            if time() - ti > 3:
                break

        self.app.stdscr.refresh()
