#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : cfg_test.py
# Creation Date : mar. 29 nov. 2016 23:18:27 CET
# Last Modified : mer. 30 nov. 2016 12:04:32 CET
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
import ConfigParser
import sys
import os

cfg = ConfigParser.RawConfigParser()

try:
    # Read cfg
    cfg.read('conf.rc')

    if cfg.has_section('path'):
        # LogDir
        if cfg.has_option('path', 'LogDir'):
            LogDir = cfg.get('path', 'LogDir')
            LogDir = LogDir.replace('$HOME', os.path.expanduser("~"))
        else:
            LogDir = os.path.expanduser("~") + "/.cpyvke/"

        # SaveDir
        if cfg.has_option('path', 'SaveDir'):
            SaveDir = cfg.get('path', 'SaveDir')
            SaveDir = SaveDir.replace('$HOME', os.path.expanduser("~"))
        else:
            SaveDir = os.path.expanduser("~") + "/.cpyvke/save"
    else:
        SaveDir = os.path.expanduser("~") + "/.cpyvke/save"
        LogDir = os.path.expanduser("~") + "/.cpyvke/"

    if cfg.has_section('colors'):
        print("has colors")
        # Warning color
        if cfg.has_option('colors', 'warning-color'):
            wcol = cfg.get('colors', 'warning-color')
        else:
            wcol = "red"

        # Background color
        if cfg.has_option('colors', 'background-color'):
            bcol = cfg.get('colors', 'background-color')
        else:
            bcol = "transparent"

        # Foreground color
        if cfg.has_option('colors', 'foreground-color'):
            fcol = cfg.get('colors', 'foreground-color')
        else:
            fcol = "cyan"

    else:
        print("nocolors")
        fcol = "cyan"
        bcol = "transparent"
        wcol = "red"

except ConfigParser.Error, err:
    print('Bad cfg file : ', err)
    sys.exit(1)

print("LogPath : " + LogDir)
print("SavePath : " + SaveDir)
print("fg : " + fcol)
print("bg : " + bcol)
print("wg : " + wcol)
###############################################################################
#
###############################################################################
