#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : CUISuspend.py
# Creation Date : Thu Nov 10 17:30:23 2016
# Last Modified : mar. 22 nov. 2016 17:35:04 CET
# Created By : Cyril Desjouy
#
# Copyright © 2016-2017 Cyril Desjouy <cyril.desjouy@free.fr>
# Distributed under terms of the BSD license.
"""

DESCRIPTION

@author: Cyril Desjouy
"""


###############################################################################
# IMPORTS
###############################################################################
import curses


class suspend_curses():
    """Context Manager to temporarily leave curses mode"""

    def __enter__(self):
        curses.endwin()

    def __exit__(self, exc_type, exc_val, tb):
        stdscreen = curses.initscr()
        stdscreen.refresh()
        curses.doupdate()
