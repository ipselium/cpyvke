# -*- coding: utf-8 -*-
"""
Created on Thu Nov 10 17:30:23 2016

@author: cdesjouy
"""

import curses


class suspend_curses():
    """Context Manager to temporarily leave curses mode"""

    def __enter__(self):
        curses.endwin()

    def __exit__(self, exc_type, exc_val, tb):
        stdscreen = curses.initscr()
        stdscreen.refresh()
        curses.doupdate()
