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
# Creation Date :
# Last Modified : mar. 20 mars 2018 11:08:03 CET
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

from setuptools import setup, find_packages
import sys


if sys.version_info < (2,7):
    raise NotImplementedError(
        "Sorry, you need at least Python 2.7 to use cpyvke.")

VERSION = '1.1.1'

__doc__ = """\
A Curses PYthon Variable and Kernel Explorer
"""


setup(
    name='cpyvke',
    version=VERSION,
    url='https://github.com/ipselium/cpyvke',
    author='Cyril Desjouy',
    author_email='ipselium@free.fr',
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'kd5 = cpyvke.kd5:main',
            'cpyvke = cpyvke.cpyvke:main',
            'cpyvke-launch-ipython = cpyvke.launch:main',
        ],
    },
    install_requires=["jupyter_client", "ipykernel", "psutil", "numpy", "matplotlib"],
    license='BSD',
    description='A Kernel and variable explorer in Curses',
    long_description=__doc__,
    classifiers=[
        'Development Status :: Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
    ]
)
