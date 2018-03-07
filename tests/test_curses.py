# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 15:07:39 2015

- mettre en place indicateur en ncurse qui check si le daemon variable manager tourne
- 


@author: Cyril Desjouy
"""

from __future__ import division  #You don't need this in Python3
import curses
from math import ceil



screen = curses.initscr()
curses.noecho()
curses.cbreak()
curses.start_color()
screen.keypad( 1 )
curses.init_pair(1,curses.COLOR_BLACK, curses.COLOR_CYAN)
curses.use_default_colors()
highlightText = curses.color_pair( 1 )
normalText = curses.A_NORMAL
screen.border( 0 )
curses.curs_set( 0 )
max_row = 10 #max number of rows
box = curses.newwin( max_row + 2, 64, 1, 1 )
box.box()

strings2 = [ "a", "b", "c", "d", "e", "f", "g", "h", "i", "l", "m", "n" ] #list of strings
variables = {'a': {'type': 'int', 'value': '1'}, 'b': {'type': 'int', 'value': '5'},\
    'c': {'type': 'int', 'value': '1'}, 'j': {'type': 'int', 'value': '5'},\
    'd': {'type': 'int', 'value': '1'}, 'k': {'type': 'int', 'value': '5'},\
    'e': {'type': 'int', 'value': '1'}, 'l': {'type': 'int', 'value': '5'},\
    'f': {'type': 'int', 'value': '1'}, 'm': {'type': 'int', 'value': '5'},\
    'g': {'type': 'int', 'value': '1'}, 'n': {'type': 'int', 'value': '5'},\
    'h': {'type': 'int', 'value': '1'}, 'o': {'type': 'int', 'value': '5'},\
    'i': {'type': 'int', 'value': '1'}, 'p': {'type': 'int', 'value': '5'}}
strings = variables.keys()
row_num = len( strings )

pages = int( ceil( row_num / max_row ) )
position = 1
page = 1
for i in range( 1, max_row + 1 ):
    if row_num == 0:
        box.addstr( 1, 1, "There aren't strings", highlightText )
    else:
        cell = strings[i-1] + ' ' + variables[strings[i-1]]['value'] + ' ' + variables[strings[i-1]]['type']
        if (i == position):
            box.addstr( i, 2, cell, highlightText )
        else:
            box.addstr( i, 2, cell, normalText )
        if i == row_num:
            break

screen.refresh()
box.refresh()

x = screen.getch()
while x != 27:
    if x == curses.KEY_DOWN:
        if page == 1:
            if position < i:
                position = position + 1
            else:
                if pages > 1:
                    page = page + 1
                    position = 1 + ( max_row * ( page - 1 ) )
        elif page == pages:
            if position < row_num:
                position = position + 1
        else:
            if position < max_row + ( max_row * ( page - 1 ) ):
                position = position + 1
            else:
                page = page + 1
                position = 1 + ( max_row * ( page - 1 ) )
    if x == curses.KEY_UP:
        if page == 1:
            if position > 1:
                position = position - 1
        else:
            if position > ( 1 + ( max_row * ( page - 1 ) ) ):
                position = position - 1
            else:
                page = page - 1
                position = max_row + ( max_row * ( page - 1 ) )
    if x == curses.KEY_LEFT:
        if page > 1:
            page = page - 1
            position = 1 + ( max_row * ( page - 1 ) )

    if x == curses.KEY_RIGHT:
        if page < pages:
            page = page + 1
            position = ( 1 + ( max_row * ( page - 1 ) ) )
    if x == ord( "\n" ) and row_num != 0:
        screen.erase()
        screen.border( 0 )
        screen.addstr( 14, 3, "YOU HAVE PRESSED '" + strings[ position - 1 ] + "' ON POSITION " + str( position ) )

    box.erase()
    screen.border( 0 )
    box.border( 0 )

    for i in range( 1 + ( max_row * ( page - 1 ) ), max_row + 1 + ( max_row * ( page - 1 ) ) ):
        if row_num == 0:
            box.addstr( 1, 1, "There aren't strings",  highlightText )
        else:
            cell = strings[i-1] + ' ' + variables[strings[i-1]]['value'] + ' ' + variables[strings[i-1]]['type']
            if ( i + ( max_row * ( page - 1 ) ) == position + ( max_row * ( page - 1 ) ) ):
                box.addstr( i - ( max_row * ( page - 1 ) ), 2, cell, highlightText )
            else:
                box.addstr( i - ( max_row * ( page - 1 ) ), 2, cell, normalText )
            if i == row_num:
                break



    screen.refresh()
    box.refresh()
    x = screen.getch()

curses.endwin()
exit()