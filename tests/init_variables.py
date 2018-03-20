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
# Creation Date : Thu Nov 17 12:09:09 2016
# Last Modified : mar. 20 mars 2018 12:39:59 CET
"""
-----------

Initialize different variable type to test cpyvke variable explorer !

@author: Cyril Desjouy
"""


import numpy as np
from numpy import linspace
from mymod import MyClass2
from math import ceil


def myfct(x):
    """ A great function """
    return x


class MyClass1:
    a = "c1"
    b = "c2"               # class attributes

    def __init__(self, c, d):
        self.c = c
        self.d = d           # instance attributes

    @staticmethod
    def mystatic():        # static method
        return MyClass1.b

    @classmethod
    def classmethod(e):
        return e

    def myfunc(self):      # non-static method
        return self.a, self.b

    def print_instance_attributes(self):
        print('[instance attributes]')
        for attribute, value in self.__dict__.items():
            print(attribute, '=', value)

    def print_class_attributes(self):
        print('[class attributes]')
        for attribute in MyClass1.__dict__.keys():
            if attribute[:2] != '__':
                value = getattr(MyClass1, attribute)
                if not callable(value):
                    print(attribute, '=', value)


class_inst1 = MyClass1('i1', 'i2')
class_inst2 = MyClass2()

array1 = np.random.rand(50, 50)
array2 = np.sin(2*np.pi*100*linspace(0, 0.01, 1000))
range1 = range(10)
dict1 = {'air': {'c': 344., 'rho': 1.2}, 'water': {'c': 1000., 'rho': 1000}}
dict2 = {'cube': 6, 'penta': 8}
lst1 = ['january', 'february', 'march', '...']
lst2 = [('monday', 1), ('tuesday', 2), ('wednesday', 3), ('thursday', 4), ('friday', 5)]
list3 = [i for i in range(100)]
set1 = {i for i in range(100)}
set2 = {1, 2}
frozenset1 = frozenset((1, 2))
tuple1 = ('dolphin', 'mamif')
tuple2 = (('imaginary', 1), ('real', 1))
iter_tup1 = iter(tuple1)
iter_tup2 = iter(tuple2)
generator = (i for i in range(100))
string1 = 'yop'
string2 = 'éô'
unicode1 = u'éô'
bytes1 = b'eo'
bytearray1 = bytearray(bytes1)
memoryview1 = memoryview(bytes1)
float1 = np.pi
wint1 = 1
wint2 = 2**1024
complex1 = 1+1j
bool1 = True
bool2 = False
