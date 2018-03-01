#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : ModuleInspector.py
# Creation Date : Wed Nov  9 16:27:41 2016
# Last Modified : jeu. 01 mars 2018 22:02:56 CET
# Created By : Cyril Desjouy
#
# Copyright © 2016-2017 Cyril Desjouy <ipselium@free.fr>
# Distributed under terms of the BSD license.
"""

DESCRIPTION

@author: Cyril Desjouy
"""


from builtins import object
from matplotlib.pyplot import figure, plot, imshow, show
from numpy import shape, save, savetxt, savez_compressed
from multiprocessing import Process
import subprocess
import sys
import locale

from .ctools import suspend_curses

locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()


def In_Thread(Func):
    ''' Run Func in thread '''
    def run(*k, **kw):
        t = Process(target=Func, args=k, kwargs=kw)
        t.start()
        return t
    return run


class Inspect(object):
    ''' Plot/Display variable. '''

    def __init__(self, varval, varname, vartype):

        self.varval = varval
        self.vartype = vartype
        self.varname = varname

    @In_Thread
    def Plot2D(self):
        ''' Plot 2D variable. '''

        figure()
        imshow(self.varval)
        show()

    @In_Thread
    def Plot1D(self):
        ''' Plot 1D variable. '''

        figure()
        plot(self.varval)
        show()

    @In_Thread
    def Plot1Dcols(self):
        ''' Plot 2D variable : superimpose all columns '''

        figure()
        for i in range(shape(self.varval)[1]):
            plot(self.varval[:, i])
        show()

    @In_Thread
    def Plot1Dlines(self):
        ''' Plot 2D variable : superimpose all lines '''

        figure()
        for i in range(shape(self.varval)[0]):
            plot(self.varval[i, :])
        show()

    def SaveNP(self, varname, SaveDir, METHOD='npy'):
        ''' Save numpy variable to file '''

        if METHOD == 'txt':
            savetxt(SaveDir + varname + '.txt', self.varval)

        if METHOD == 'npy':
            save(SaveDir + varname, self.varval)

        if METHOD == 'npz':
            savez_compressed(SaveDir + varname, var=self.varval)

    def Save(self, SaveDir):
        ''' Save variable to text file '''

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
        '''
        Display variable using **App** (less|vim).
        If a module is provided, use **Arg** to choose wich methode to use.
        '''

        filename = '/tmp/tmp_cVKE'

        # Convert all type of variable to string
        if self.vartype != 'str' and self.vartype != 'unicode':
            self.varval = str(self.varval)

        #
        if self.vartype == 'unicode':
            with open(filename, 'w') as f:
                f.write(self.varval.encode(code))

        elif self.vartype == 'module':
            if Arg == 'Help':
                manual(self.varval, filename)

        else:
            with open(filename, 'w') as f:
                f.write(self.varval)

        with suspend_curses():
            subprocess.call([app, filename])
            subprocess.call(['rm', filename])


def manual(module, filename):
    ''' Display help of a module. '''

    sys.stdout = open(filename, 'w')
    print(help(module))

