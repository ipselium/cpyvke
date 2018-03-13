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
# Last Modified : mar. 13 mars 2018 12:42:20 CET
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""


from matplotlib.pyplot import figure, plot, imshow, show
from numpy import shape, save, savetxt, savez_compressed
from multiprocessing import Process
import subprocess
import sys
import locale

from ..libcpyvke.widgets import suspend_curses

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
        for i in range(shape(self.varval)[1]):
            plot(self.varval[:, i])
        show()

    @In_Thread
    def Plot1Dlines(self):
        """ Plot 2D variable : superimpose all lines """

        figure()
        for i in range(shape(self.varval)[0]):
            plot(self.varval[i, :])
        show()

    def SaveNP(self, varname, SaveDir, METHOD='npy'):
        """ Save numpy variable to file """

        if METHOD == 'txt':
            savetxt(SaveDir + varname + '.txt', self.varval)

        if METHOD == 'npy':
            save(SaveDir + varname, self.varval)

        if METHOD == 'npz':
            savez_compressed(SaveDir + varname, var=self.varval)

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
