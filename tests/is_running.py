#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright © 2016-2018 Cyril Desjouy <ipselium@free.fr>
#
# This file is part of {name}
#
# {name} is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# {name} is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with {name}. If not, see <http://www.gnu.org/licenses/>.
#
#
# Creation Date :
# Last Modified :
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

from cpyvke.utils.kernel import check_server, isOpen
import time

print(80*'-')
print("Dead kernel")

ti = time.time()
print(check_server(36351))
print("{}".format(time.time() - ti))


ti = time.time()
print(isOpen("127.0.0.1", 36351))
print("{}".format(time.time() - ti))

print(80*'-')
print("Alive kernel")

ti = time.time()
print(check_server(36352))
print("{}".format(time.time() - ti))


ti = time.time()
print(isOpen("127.0.0.1", 36352))
print("{}".format(time.time() - ti))