#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : init_var4test.py
# Creation Date : Thu Nov 17 12:09:09 2016
# Last Modified : ven. 23 déc. 2016 14:59:44 CET
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
import numpy as np
import sys

alonglist1 = list(range(1000))
alonglist2 = list(range(5000))

array1 = np.random.rand(50, 50)
array2 = np.sin(2*np.pi*100*np.linspace(0, 0.01, 1000))
dict1 = {'air': {'c': 344., 'rho': 1.2}, 'eau': {'c': 1000., 'rho': 1000}}
dict2 = {'cube': 6, 'penta': 8}
lst1 = ['janvier', 'fevrier', 'mars', '...']
lst2 = [('lundi', 1), ('mardi', 2), ('mercredi', 3), ('jeudi', 4), ('vendredi', 5)]
tuple1 = ('dophin', 'mamif')
tuple2 = (('imaginary', 1), ('real', 1))
with open('/home/cdesjouy/Documents/dev/python/cpyvke/tests/univ.html', 'r') as fstring:
    string1 = fstring.readlines()
string2 = 'éô'
string3 = 'yop'
unicode1 = u'éô'
float1 = np.pi
wint1 = 1
wint2 = 1
wint3 = 1
wint4 = 1
wint5 = 1


print('DUMP')
output = []

def Dump(obj, nested_level=0, output=[]):
    ''' '''

    if nested_level == 0:
        output = []

    spacing = '   '
    if type(obj) == dict:
        output.append('%s{' % ((nested_level) * spacing))
        for k, v in obj.items():
            if hasattr(v, '__iter__'):
                output.append('%s%s:' % ((nested_level + 1) * spacing, k))
                Dump(v, nested_level + 1, output)
            else:
                output.append('%s%s: %s' % ((nested_level + 1) * spacing, k, v))
        output.append('%s}' % (nested_level * spacing))
    elif type(obj) in (list, tuple):
        output.append('%s[' % ((nested_level) * spacing))
        for v in obj:
            if hasattr(v, '__iter__'):
                Dump(v, nested_level + 1, output)
            else:
                output.append('%s%s' % ((nested_level + 1) * spacing, v))
        output.append('%s]' % ((nested_level) * spacing))
    else:
        output.append('%s%s' % (nested_level * spacing, obj))
    return output


###############################################################################
def dump(obj, nested_level=0, output=sys.stdout):
    spacing = '   '
    if type(obj) == dict:
        print >> output, '%s{' % ((nested_level) * spacing)
        for k, v in obj.items():
            if hasattr(v, '__iter__'):
                print >> output, '%s%s:' % ((nested_level + 1) * spacing, k)
                dump(v, nested_level + 1, output)
            else:
                print >> output, '%s%s: %s' % ((nested_level + 1) * spacing, k, v)
        print >> output, '%s}' % (nested_level * spacing)
    elif type(obj) == list:
        print >> output, '%s[' % ((nested_level) * spacing)
        for v in obj:
            if hasattr(v, '__iter__'):
                dump(v, nested_level + 1, output)
            else:
                print >> output, '%s%s' % ((nested_level + 1) * spacing, v)
        print >> output, '%s]' % ((nested_level) * spacing)
    else:
        print >> output, '%s%s' % (nested_level * spacing, obj)


def json_dump(obj):
    import json
    print(json.dumps(obj, indent=4))
