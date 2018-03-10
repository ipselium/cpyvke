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
# Creation Date : Mon Nov 21 23:26:57 2016
# Last Modified : sam. 10 mars 2018 20:06:19 CET
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import curses


def FilterVarLst(lst, filter):
    """ Filter variable list (name|type). """

    filtered = []
    for key in list(lst):
        if filter in lst[key]['type'] or filter in key:
            filtered.append(key)

    return sorted(filtered)


def TypeSort(lst):
    """ Sort variable by type. """

    from operator import itemgetter

    types = []
    for key in list(lst):
        types.append([key, lst[key]['type']])

    types.sort(key=itemgetter(1))

    return [item[0] for item in types]


def FormatCell(variables, name, max_width):
    """ Format cells for display """

    max_width = int((max_width-7)/5)
    typ = '[' + variables[name]['type'] + ']'

    # Only display module name
    if 'module' in variables[name]['value']:
        val = variables[name]['value'].split("'")[1]

    # Only display dimensions of array
    elif 'elem' in variables[name]['value']:
        val1 = variables[name]['value'].split(":")[0]
        val2 = variables[name]['value'].split("`")[1]
        val = val1 + ' [' + val2 + ']'
    else:
        # Repr to avoid interpreting \n in strings
        val = variables[name]['value']

    # Check length of each entry
    if len(val) > 2*max_width:
        val = val[0:2*max_width-4] + '... '

    if len(name) > 2*max_width:
        name = name[0:2*max_width-4] + '... '

    if len(typ) > max_width:
        typ = typ[0:max_width-4] + '... '

    s = "{:{wname}} {:{wval}} {:{wtype}}".format(name, val, typ,
                                                 wname=2*max_width,
                                                 wval=2*max_width,
                                                 wtype=max_width)
    return s


def dump(obj, nested_level=0, output=[]):
    """ Format dict, list and tuples variables for displaying. """

    if nested_level == 0:
        output = []

    spacing = '   '
    if type(obj) is dict:
        output.append('%s{' % ((nested_level) * spacing))
        for k, v in obj.items():
            if hasattr(v, '__iter__'):
                output.append('%s%s:' % ((nested_level + 1) * spacing, k))
                dump(v, nested_level + 1, output)
            else:
                output.append('%s%s: %s' % ((nested_level + 1) * spacing, k, v))
        output.append('%s}' % (nested_level * spacing))

    elif type(obj) is list:
        output.append('%s[' % ((nested_level) * spacing))
        for v in obj:
            if hasattr(v, '__iter__'):
                dump(v, nested_level + 1, output)
            else:
                output.append('%s%s' % ((nested_level + 1) * spacing, v))
        output.append('%s]' % ((nested_level) * spacing))

    elif type(obj) is tuple:
        output.append('%s(' % ((nested_level) * spacing))
        for v in obj:
            if hasattr(v, '__iter__'):
                dump(v, nested_level + 1, output)
            else:
                output.append('%s%s' % ((nested_level + 1) * spacing, v))
        output.append('%s)' % ((nested_level) * spacing))

    else:
        output.append('%s%s' % (nested_level * spacing, obj))
    return output


class suspend_curses():
    """Context Manager to temporarily leave curses mode"""

    def __enter__(self):
        curses.endwin()

    def __exit__(self, exc_type, exc_val, tb):
        stdscreen = curses.initscr()
        stdscreen.refresh()
        curses.doupdate()
