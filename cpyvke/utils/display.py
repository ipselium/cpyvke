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
# Creation Date : mar. 13 mars 2018 12:01:45 CET
# Last Modified : ven. 30 mars 2018 23:48:03 CEST
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import textwrap


def str_reduce(msg, maxwidth):
    """ Reduce a string with dots (...) if its length is greater than maxwidth """

    if len(msg) >= maxwidth:
        return msg[:maxwidth-3] + '...'
    else:
        return msg


def str_format(string, width):
    """ Convert a string into a list whose elements length do not exceed a given width. """

    output = []
    for seq in string.split('\n'):
        tmp = textwrap.wrap(seq, width)
        for split in tmp:
            output.append(split)

    return output


def whos_to_dic(string):
    """ Format output of daemon to a dictionnary """

    variables = {}
    for item in string.split('\n')[2:]:
        tmp = [j for j in item.split(' ') if j is not '']
        if tmp:
            var_name = tmp[0]
            var_typ = tmp[1]
            var_val = ' '.join(tmp[2:])
            variables[var_name] = {'value': var_val, 'type': var_typ}
    return variables


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

    elif type(obj) in [set, frozenset]:
        output.append('%s{' % ((nested_level) * spacing))
        for v in obj:
            if hasattr(v, '__iter__'):
                dump(v, nested_level + 1, output)
            else:
                output.append('%s%s' % ((nested_level + 1) * spacing, v))
        output.append('%s}' % ((nested_level) * spacing))

    else:
        output.append('%s%s' % (nested_level * spacing, obj))

    return output


def format_cell(variables, name, screen_width):
    """ Format data for display """

    screen_width = screen_width - 4

    if '/kernel' in variables[name]['value']:
        return format_kernel(variables, name, screen_width)
    else:
        return format_variable(variables, name, screen_width)


def format_variable(variables, name, screen_width):
    """ Format regular variables """

    max_width = int(screen_width/5)

    # Types
    if "@<class '" in variables[name]['type']:
        typ = '[inst. ' + variables[name]['type'].split("'")[1] + ']'
    elif "<class '" in variables[name]['type']:
        typ = '[' + variables[name]['type'].split("'")[1] + ']'
    else:
        typ = '[' + variables[name]['type'] + ']'

    # Only display module name
    if 'module' in variables[name]['value']:
        val = variables[name]['value'].split("'")[1]

    # Only display dimensions of array
    elif 'elem' in variables[name]['value']:
        val1 = variables[name]['value'].split(":")[0]
        val2 = variables[name]['value'].split("`")[1]
        val = val1 + ' [' + val2 + ']'

    elif 'classmethod' in variables[name]['value']:
        val = 'classmethod'

    elif 'staticmethod' in variables[name]['value']:
        val = 'staticmethod'

    elif ' at' in variables[name]['value']:
        val = variables[name]['value'].split(' at ')[0] + '>'

    elif 'frozenset' in variables[name]['value']:
        val = variables[name]['value'].split('(')[1].split(')')[0]

    elif '<...>' in variables[name]['value']:
        val = variables[name]['value'].split('<')[0] + '...'

    else:
        # Repr to avoid interpreting \n in strings
        val = variables[name]['value']

    # Check length of each entry
    if len(val) > 3*max_width:
        val = val[0:3*max_width-4] + '... '

    if len(name) > max_width:
        name = name[0:max_width-4] + '... '

    if len(typ) > max_width:
        typ = typ[0:max_width-4] + '... '

    s1 = "{:{wname}} {:{wval}}".format(name, val, wname=max_width, wval=3*max_width)
    s2 = "{:{wtype}}".format(typ, wtype=screen_width-len(s1))

    return s1, s2


def format_kernel(variables, name, screen_width):
    """ Format regular variables """

    max_width = int(screen_width/5)
    typ = '[' + variables[name]['type'] + ']'

    # Repr to avoid interpreting \n in strings
    val = variables[name]['value']

    # Check length of each entry
    if len(val) > 3*max_width:
        val = val[0:3*max_width-4] + '... '

    if len(name) > max_width:
        name = name[0:max_width-4] + '... '

    if len(typ) > max_width:
        typ = typ[0:max_width-4] + '... '

    s1 = "{:{wname}} {:{wval}}".format(name, val, wname=max_width, wval=3*max_width)
    s2 = "{:{wtype}}".format(typ, wtype=screen_width-len(s1))

    return s1, s2
