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
# Last Modified : jeu. 15 mars 2018 09:34:32 CET
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

from .temppanel import PanelWin
from ..utils.display import format_class

class ClassWin(PanelWin):

    def __init__(self, parent):
        """ Class Constructor """

        super(ClassWin, self).__init__(parent)

        # Define Styles
        self.c_txt = self.parent.c_exp_txt
        self.c_bdr = self.parent.c_exp_bdr
        self.c_ttl = self.parent.c_exp_ttl
        self.c_hh = self.parent.c_exp_hh
        self.c_pwf = self.parent.c_exp_pwf

        # Values
        self.varval = self.parent.varval
        self.varname = self.parent.varname
        # Init Menu
        self.win_title = ' {} inspection '.format(self.varname)

    def get_items(self):
        """ List of items """

        items = []
        for i in self.varval.keys():
            items.append([format_class(self.varval, i, self.screen_width-2)])

        return items
