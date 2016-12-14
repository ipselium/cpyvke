#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name :
# Creation Date : lun. 05 déc. 2016 23:04:30 CET
# Last Modified : mer. 07 déc. 2016 12:17:13 CET
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


###############################################################################
#
###############################################################################
import curses

def main(stdscr):
    curses.start_color()
    curses.use_default_colors()
    for i in range(curses.COLORS):
        curses.init_pair(i + 1, i, -1)
    try:
        stdscr.addstr('Terminal supports ' + str(curses.COLORS) + ' colors :\n\n', curses.A_UNDERLINE)
        for i in range(curses.COLORS):
            stdscr.addstr(str(i-1) + ' ', curses.color_pair(i))
        stdscr.addstr('\n\nBasic 8 colors :\n\n', curses.A_UNDERLINE)
        for i in range(8):
            stdscr.addstr('Normal ', curses.color_pair(i) | curses.A_NORMAL)
            stdscr.addstr('Dim ', curses.color_pair(i) | curses.A_DIM)
            stdscr.addstr('Bold ', curses.color_pair(i) | curses.A_BOLD)
            stdscr.addstr('Reverse ', curses.color_pair(i) | curses.A_REVERSE)
            stdscr.addstr('Blink ', curses.color_pair(i) | curses.A_BLINK)
            stdscr.addstr('Standout ', curses.color_pair(i) | curses.A_STANDOUT)
            stdscr.addstr('Underline ', curses.color_pair(i) | curses.A_UNDERLINE)
            stdscr.addstr('AltChar ', curses.color_pair(i) | curses.A_ALTCHARSET)
            stdscr.addstr('\n')

    except curses.ERR:
        # End of screen reached
        pass
    stdscr.getch()

curses.wrapper(main)
