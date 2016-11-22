# -*- coding: utf-8 -*-
"""
Created on Wed Nov  9 16:27:41 2016

@author: cdesjouy
"""

from matplotlib.pyplot import figure, plot, imshow, show
from numpy import shape, save, savetxt, savez_compressed
from multiprocessing import Process


class SendToMPL(object):
    def __init__(self, varval=None):
        ''' Init SendToMPL CLASS '''

        self.varval = varval

    ###########################################################################
    def Plot2D(self):
        ''' Plot 2D variable : imdraw '''

        self.proc = Process(target=self.ExecPlot2D)
        self.proc.start()

    def ExecPlot2D(self):
        ''' '''

        figure()
        imshow(self.varval)
        show()

    ############################################################################
    def Plot1D(self):
        ''' Plot 2D variable : imdraw '''

        self.proc = Process(target=self.ExecPlot1D)
        self.proc.start()

    def ExecPlot1D(self):
        ''' Plot 1D variable '''

        figure()
        plot(self.varval)
        show()

    ############################################################################
    def Plot1Dcols(self):
        ''' Plot 2D variable : imdraw '''

        self.proc = Process(target=self.ExecPlot1Dcols)
        self.proc.start()

    def ExecPlot1Dcols(self):
        ''' Plot 2D variable : superimpose all columns '''

        figure()
        for i in range(shape(self.varval)[1]):
            plot(self.varval[:, i])
        show()

    ############################################################################
    def Plot1Dlines(self):
        ''' Plot 2D variable : imdraw '''

        self.proc = Process(target=self.ExecPlot1Dlines)
        self.proc.start()

    def ExecPlot1Dlines(self):
        ''' Plot 2D variable : superimpose all lines '''

        figure()
        for i in range(shape(self.varval)[0]):
            plot(self.varval[i, :])
        show()

    ############################################################################
    def SaveVar(self, varname, METHOD='npy'):
        ''' Save variable to file '''

        if METHOD == 'txt':
            savetxt('SaveFiles/' + varname + '.txt', self.varval)

        if METHOD == 'npy':
            save('SaveFiles/' + varname, self.varval)

        if METHOD == 'npz':
            savez_compressed('SaveFiles/' + varname, var=self.varval)
