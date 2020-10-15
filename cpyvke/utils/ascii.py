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
# Creation Date : sam. 17 mars 2018 11:22:56 CET
# Last Modified : lun. 09 avril 2018 22:37:36 CEST
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""


def ascii_cpyvke(font='small'):
    """ figlet -f font "Cpyvke" """

    if font == 'small':
        return ["  ___               _       ",
                " / __|_ __ _  ___ _| |_____ ",
                "| (__| '_ \ || \ V / / / -_)",
                " \___| .__/\_, |\_/|_\_\___|  v1.2.9",
                "     |_|   |__/             "]
    elif font == 'smshadow':
        return ["   __|              |        ",
                "  (    _ \ |  |\ \ /| /  -_) ",
                " \___|.__/\_, | \_/_\_\\___|  v1.2.9",
                "     _|   ___/               "]
    elif font == 'pagga':
        return ["░█▀▀░█▀█░█░█░█░█░█░█░█▀▀",
                "░█░░░█▀▀░░█░░▀▄▀░█▀▄░█▀▀",
                "░▀▀▀░▀░░░░▀░░░▀░░▀░▀░▀▀▀  v1.2.9"]
    else:
        return ["Ascii font not found !"]

