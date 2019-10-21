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
# Last Modified : mer. 11 avril 2018 00:15:49 CEST
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

from setuptools import setup, find_packages
import sys
import cpyvke

if sys.version_info < (2,7):
    raise NotImplementedError(
        "Sorry, you need at least Python 2.7 to use cpyvke.")

setup(
    name='cpyvke',
    description='A Kernel and variable explorer in Curses',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    version=cpyvke.__version__,
    license='GPL',
    url='https://github.com/ipselium/cpyvke',
    author='Cyril Desjouy',
    author_email='ipselium@free.fr',
    packages=find_packages(),
    include_package_data=True,
    install_requires=["jupyter_client", "ipykernel", "psutil", "numpy", "matplotlib"],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.5',
        'Operating System :: POSIX :: Linux',
        'Topic :: Software Development :: Debuggers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
    ],
    entry_points={
        'console_scripts': [
            'kd5 = cpyvke.kd5:main',
            'cpyvke = cpyvke.cpyvke:main',
            'cpyvke-launch-ipython = cpyvke.launch:main',
        ],
    }
)
