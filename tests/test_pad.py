#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : test_pad.py
# Creation Date : mer. 23 nov. 2016 14:45:08 CET
# Last Modified : mer. 23 nov. 2016 16:24:22 CET
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

###############################################################################
#
###############################################################################
curses.initscr()
mypad = curses.newpad(40, 60)
mypad_pos = 0
mypad.refresh(mypad_pos, 0, 5, 5, 10, 60)

cmd = mypad.getch()
mypad.addstr('test')
if cmd == curses.KEY_DOWN:
    mypad_pos += 1
    mypad.refresh(mypad_pos, 0, 5, 5, 10, 60)
elif cmd == curses.KEY_UP:
    mypad_pos -= 1
    mypad.refresh(mypad_pos, 0, 5, 5, 10, 60)
