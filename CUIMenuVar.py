# -*- coding: utf-8 -*-
"""
Created on Wed Nov  9 16:29:28 2016

@author: cdesjouy
"""
import curses
from curses import panel
from PlotServer import SendToMPL
from numpy import array

from CUIWidgets import Inspector, Viewer, WarningMsg


class MenuVarCUI(object):
    def __init__(self, CUI_self):
        ''' Init MenuCUI Class '''

        self.CUI_self = CUI_self
        self.cyan_text = CUI_self.cyan_text
        self.stdscreen = CUI_self.stdscreen

        # Variables properties
        self.varname = CUI_self.strings[CUI_self.position-1]
        self.vartype = CUI_self.variables[CUI_self.strings[CUI_self.position-1]]['type']
        self.screen_width = CUI_self.screen_width

        # Get variable value
        if CUI_self.variables[CUI_self.strings[CUI_self.position-1]]['type'] == 'module':
            self.varval = CUI_self.variables[CUI_self.strings[CUI_self.position-1]]['value']
            self.varval = self.varval.split("'")[1]
            self.plot = Inspector(self)

        elif CUI_self.variables[CUI_self.strings[CUI_self.position-1]]['type'] in ('str', 'dict', 'list', 'tuple'):
            CUI_self.qreq.put(self.varname)
            self.varval = CUI_self.qans.get()
            self.varval = eval(self.varval)
            self.plot = Viewer(self)

        elif CUI_self.variables[CUI_self.strings[CUI_self.position-1]]['type'] in ('function'):
            self.varval = '[function]'

        elif CUI_self.variables[CUI_self.strings[CUI_self.position-1]]['type'] in ('file'):
            self.varval = '[file]'

        else:
            CUI_self.qreq.put(self.varname)
            self.varval = CUI_self.qans.get()
            self.varval = eval(self.varval)
            # Init SendToMPL Class
            self.plot = SendToMPL(self.varval)

        # Create Menu List
        self.menu_title = '| ' + self.varname + ' |'
        self.menu_lst = self.CreateMenuLst()
        if len(self.menu_lst) == 0:
            self.menu_lst.append(('No Options', 'exit'))

        # Menu dimensions
        self.menu_width = len(max([self.menu_lst[i][0] for i in range(len(self.menu_lst))], key=len))
        self.menu_width = max(self.menu_width, len(self.menu_title)) + 5
        self.menu_height = len(self.menu_lst) + 2

        # Init Menu
        self.menu = self.stdscreen.subwin(self.menu_height, self.menu_width, 2, self.screen_width-self.menu_width-2)
        self.menu.attrset(self.cyan_text)    # change border color
        self.menu.border(0)
        self.menu.keypad(1)

        # Send menu to a panel
        self.panel_menu = panel.new_panel(self.menu)
        self.panel_menu.hide()       # Hide the panel. Doesnt delete the object
        panel.update_panels()

        # Various variables
        self.menuposition = 0

###############################################################################
    def Display(self):
        ''' '''
        self.panel_menu.top()        # Push the panel to the bottom of the stack
        self.panel_menu.show()       # Display the panel
        self.menu.clear()

        menukey = -1
        while menukey not in (27, 113):
            self.menu.border(0)
            self.menu.addstr(0, int((self.menu_width-len(self.menu_title))/2), self.menu_title, curses.A_BOLD | self.cyan_text)
            self.menu.refresh()
            curses.doupdate()
            for index, item in enumerate(self.menu_lst):
                if index == self.menuposition:
                    mode = curses.A_REVERSE
                else:
                    mode = curses.A_NORMAL

                msg = item[0]
                self.menu.addstr(1+index, 1, msg, mode)

            menukey = self.menu.getch()

            if menukey in [curses.KEY_ENTER, ord('\n')]:
                eval(self.menu_lst[self.menuposition][1])
                break

            elif menukey == curses.KEY_UP:
                self.Navigate(-1)

            elif menukey == curses.KEY_DOWN:
                self.Navigate(1)

        self.menu.clear()
        self.panel_menu.hide()
        panel.update_panels()
        curses.doupdate()

###############################################################################
    def Navigate(self, n):
        self.menuposition += n
        if self.menuposition < 0:
            self.menuposition = 0
        elif self.menuposition >= len(self.menu_lst):
            self.menuposition = len(self.menu_lst)-1

###############################################################################
    def CreateMenuLst(self):
        ''' Create the item list for the varmenu  '''
        if self.vartype == 'int':
            return []

        elif self.vartype == 'float':
            return []

        elif self.vartype == 'str':
            return [('View', 'self.plot.Display()')]

        elif self.vartype == 'module':
            return [('Description', "self.plot.Display('Description')"), ('Help', "self.plot.Display('Help')")]

        elif self.vartype == 'list':
            return [('View', 'self.plot.Display()')]

        elif self.vartype == 'dict':
            return [('View', 'self.plot.Display()')]

        elif self.vartype == 'tuple':
            return [('View', 'self.plot.Display()')]

        elif (self.vartype == 'ndarray') and (len(self.varval.shape) == 1):
            return [('Plot', 'self.plot.Plot1D()'),
                    ('Save', 'self.MenuSave()')]

        elif (self.vartype == 'ndarray') and (len(self.varval.shape) == 2):
            return [('Plot 2D', 'self.plot.Plot2D()'),
                    ('Plot (cols)', 'self.plot.Plot1Dcols()'),
                    ('Plot (lines)', 'self.plot.Plot1Dlines()'),
                    ('Save', 'self.MenuSave()')]
        else:
            return []

###############################################################################
    def MenuSave(self):

        # Init Menu
        save_menu = self.CUI_self.stdscreen.subwin(5, 6, self.menu_height-2, self.screen_width-9)
        save_menu.attrset(self.cyan_text)    # change border color
        save_menu.border(0)
        save_menu.keypad(1)

        # Send menu to a panel
        panel_save = panel.new_panel(save_menu)
        panel_save.hide()
        panel.update_panels()

        # Various variables
        self.menuposition = 0

        save_items = [('txt', "self.plot.SaveVar(self.varname, 'txt')"),
                      ('npy', "self.plot.SaveVar(self.varname, 'npy')"),
                      ('npz', "self.plot.SaveVar(self.varname, 'npz')")]
        panel_save.top()        # Push the panel to the bottom of the stack.
        panel_save.show()       # Display the panel (which might have been hidden)
        save_menu.clear()

        menukey = -1
        while menukey not in (27, 113):
            save_menu.border(0)
            save_menu.refresh()
            curses.doupdate()
            for index, item in enumerate(save_items):
                if index == self.menuposition:
                    mode = curses.A_REVERSE
                else:
                    mode = curses.A_NORMAL

                msg = item[0]
                save_menu.addstr(1+index, 1, msg, mode)

            menukey = save_menu.getch()

            if menukey in [curses.KEY_ENTER, ord('\n')]:
                if self.menuposition == len(save_items)-1:
                    break
                else:
                    Wng = WarningMsg(self.CUI_self)
                    try:
                        eval(save_items[self.menuposition][1])
                        Wng.Display('Saved !')
                    except:
                        Wng.Display('Not saved !')
                    else:
                        break

            elif menukey == curses.KEY_UP:
                self.Navigate(-1)

            elif menukey == curses.KEY_DOWN:
                self.Navigate(1)

        save_menu.clear()
        panel_save.hide()
        panel.update_panels()
        curses.doupdate()
