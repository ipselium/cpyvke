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
# Creation Date : mar. 29 nov. 2016 23:18:27 CET
# Last Modified : sam. 10 mars 2018 20:17:28 CET
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""


import sys
import os
from time import sleep
try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser


def CheckDir(directory):
    """ Check if dir exists. If not, create it."""

    if os.path.isdir(directory) is False:
        os.makedirs(directory)
        print("Create directory : " + str(directory))
        sleep(0.5)


class cfg_setup:
    """ Handle configuration file. """

    def __init__(self):

        self.cfg = ConfigParser.RawConfigParser()
        self.home = os.path.expanduser("~")
        self.path = self.home + '/.cpyvke/'
        # Check if config dir exists. If not create it.
        if not os.path.exists(self.path):
            os.makedirs(self.path)
            print("Create configuration directory : " + str(self.path))
            sleep(0.5)

    def InitCfg(self):
        """ Check if cpyvke.conf exists. If not create it. """

        if os.path.exists(self.path + 'cpyvke.conf') is False:
            open(self.path + 'cpyvke.conf', 'a').close()
            print("Create configuration file : " + str(self.path + 'cpyvke.conf'))
            sleep(0.5)
            self.WriteConfig()

    def WriteConfig(self):
        """ Write configuration file. """

        self.cfg.add_section('main colors')
        self.cfg.set('main colors', 'title', 'white, transparent')
        self.cfg.set('main colors', 'text', 'white, transparent')
        self.cfg.set('main colors', 'highlight', 'black, cyan')
        self.cfg.set('main colors', 'border', 'white, transparent')

        self.cfg.add_section('explorer colors')
        self.cfg.set('explorer colors', 'title', 'cyan, transparent')
        self.cfg.set('explorer colors', 'text', 'white, transparent')
        self.cfg.set('explorer colors', 'highlight', 'black, cyan')
        self.cfg.set('explorer colors', 'border', 'cyan, transparent')

        self.cfg.add_section('kernel colors')
        self.cfg.set('kernel colors', 'title', 'red, transparent')
        self.cfg.set('kernel colors', 'text', 'white, transparent')
        self.cfg.set('kernel colors', 'highlight', 'white, transparent')
        self.cfg.set('kernel colors', 'border', 'red, transparent')
        self.cfg.set('kernel colors', 'connected', 'green, transparent')
        self.cfg.set('kernel colors', 'died', 'red, transparent')
        self.cfg.set('kernel colors', 'alive', 'cyan, transparent')

        self.cfg.add_section('bar colors')
        self.cfg.set('bar colors', 'kernel', 'white, transparent')
        self.cfg.set('bar colors', 'connected', 'green, transparent')
        self.cfg.set('bar colors', 'disconnected', 'red, transparent')
        self.cfg.set('bar colors', 'help', 'white, transparent')

        self.cfg.add_section('warning colors')
        self.cfg.set('warning colors', 'text', 'red, transparent')
        self.cfg.set('warning colors', 'border', 'red, transparent')

        self.cfg.add_section('path')
        self.cfg.set('path', 'save-dir', '$HOME/.cpyvke/save/')

        self.cfg.add_section('font')
        self.cfg.set('font', 'powerline-font', 'False')

        self.cfg.add_section('comm')
        self.cfg.set('comm', 's-port', 15555)
        self.cfg.set('comm', 'r-port', 15556)

        self.cfg.add_section('daemon')
        self.cfg.set('daemon', 'refresh', 0.1)

        self.cfg.add_section('kernel version')
        self.cfg.set('kernel version', 'version', '3')

        with open(self.path + 'cpyvke.conf', 'w') as configfile:
            self.cfg.write(configfile)

    def InitSaveDir(self):
        """ Check|create configuration directories. """

        if os.path.exists(self.SaveDir) is False:
            os.makedirs(self.SaveDir)
            print("Create save directory : " + str(self.SaveDir))
            sleep(0.5)

    def RunCfg(self):
        """ Run configuration. """

        try:
            # Check if config file exist. If not create it
            self.InitCfg()
            # Read config file
            self.cfg.read(self.path + 'cpyvke.conf')

            # SaveDir
            if self.cfg.has_option('path', 'save-dir'):
                self.SaveDir = self.cfg.get('path', 'save-dir')
                self.SaveDir = self.SaveDir.replace('$HOME', self.home)
                if self.SaveDir[-1] != '/':
                    self.SaveDir = self.SaveDir + '/'
            else:
                self.SaveDir = self.path + 'save/'

            # FONT
            if self.cfg.has_option('font', 'powerline-font'):
                pwf = self.cfg.get('font', 'powerline-font')
            else:
                pwf = 'False'

            # KERNEL VERSION
            if self.cfg.has_option('kernel version', 'version'):
                kver = self.cfg.get('kernel version', 'version')
            else:
                kver = 3

            # Refresh delay
            if self.cfg.has_option('daemon', 'refresh'):
                delay = self.cfg.get('daemon', 'refresh')
            else:
                delay = 0.1

            # COMM
            if self.cfg.has_option('comm', 'r-port'):
                rport = self.cfg.get('comm', 'r-port')
            else:
                rport = 15556

            if self.cfg.has_option('comm', 's-port'):
                sport = self.cfg.get('comm', 's-port')
            else:
                sport = 15555

            # WARNING COLORS
            if self.cfg.has_option('warning colors', 'text'):
                wg_txt = self.cfg.get('warning colors', 'text')
            else:
                wg_txt = "red, transparent"

            if self.cfg.has_option('warning colors', 'border'):
                wg_bdr = self.cfg.get('warning colors', 'border')
            else:
                wg_bdr = "red, transparent"

            # BAR COLORS
            if self.cfg.has_option('bar colors', 'kernel'):
                br_kn = self.cfg.get('bar colors', 'kernel')
            else:
                br_kn = "white, transparent"

            if self.cfg.has_option('bar colors', 'help'):
                br_hlp = self.cfg.get('bar colors', 'help')
            else:
                br_hlp = "white, transparent"

            if self.cfg.has_option('bar colors', 'connected'):
                br_co = self.cfg.get('bar colors', 'connected')
            else:
                br_co = "green, transparent"

            if self.cfg.has_option('bar colors', 'disconnected'):
                br_dco = self.cfg.get('bar colors', 'disconnected')
            else:
                br_dco = "red, transparent"

            # MAIN COLORS
            if self.cfg.has_option('main colors', 'text'):
                main_txt = self.cfg.get('main colors', 'text')
            else:
                main_txt = "white, transparent"

            if self.cfg.has_option('main colors', 'border'):
                main_bdr = self.cfg.get('main colors', 'border')
            else:
                main_bdr = "white, transparent"

            if self.cfg.has_option('main colors', 'title'):
                main_ttl = self.cfg.get('main colors', 'title')
            else:
                main_ttl = "white, transparent"

            if self.cfg.has_option('main colors', 'highlight'):
                main_hh = self.cfg.get('main colors', 'highlight')
            else:
                main_hh = "black, cyan"

            # EXPLORER COLORS
            if self.cfg.has_option('explorer colors', 'text'):
                exp_txt = self.cfg.get('explorer colors', 'text')
            else:
                exp_txt = "white, transparent"

            if self.cfg.has_option('explorer colors', 'border'):
                exp_bdr = self.cfg.get('explorer colors', 'border')
            else:
                exp_bdr = "white, transparent"

            if self.cfg.has_option('explorer colors', 'title'):
                exp_ttl = self.cfg.get('explorer colors', 'title')
            else:
                exp_ttl = "white, transparent"

            if self.cfg.has_option('explorer colors', 'highlight'):
                exp_hh = self.cfg.get('explorer colors', 'highlight')
            else:
                exp_hh = "black, cyan"

            # KERNEL COLORS
            if self.cfg.has_option('kernel colors', 'text'):
                kn_txt = self.cfg.get('kernel colors', 'text')
            else:
                kn_txt = "white, transparent"

            if self.cfg.has_option('kernel colors', 'border'):
                kn_bdr = self.cfg.get('kernel colors', 'border')
            else:
                kn_bdr = "white, transparent"

            if self.cfg.has_option('kernel colors', 'title'):
                kn_ttl = self.cfg.get('kernel colors', 'title')
            else:
                kn_ttl = "white, transparent"

            if self.cfg.has_option('kernel colors', 'highlight'):
                kn_hh = self.cfg.get('kernel colors', 'highlight')
            else:
                kn_hh = "black, red"

            if self.cfg.has_option('kernel colors', 'connected'):
                kn_co = self.cfg.get('kernel colors', 'connected')
            else:
                kn_co = "green, transparent"

            if self.cfg.has_option('kernel colors', 'alive'):
                kn_al = self.cfg.get('kernel colors', 'alive')
            else:
                kn_al = "cyan, transparent"

            if self.cfg.has_option('kernel colors', 'died'):
                kn_di = self.cfg.get('kernel colors', 'died')
            else:
                kn_di = "red, transparent"

            # Colors :
            self.Config = {'mn': {'txt': main_txt,
                                  'bdr': main_bdr,
                                  'ttl': main_ttl,
                                  'hh': main_hh},
                           'xp': {'txt': exp_txt,
                                  'bdr': exp_bdr,
                                  'ttl': exp_ttl,
                                  'hh': exp_hh},
                           'kn': {'txt': kn_txt,
                                  'bdr': kn_bdr,
                                  'ttl': kn_ttl,
                                  'hh': kn_hh,
                                  'co': kn_co,
                                  'di': kn_di,
                                  'al': kn_al},
                           'wg': {'txt': wg_txt,
                                  'bdr': wg_bdr},
                           'br': {'kn': br_kn,
                                  'hlp': br_hlp,
                                  'co': br_co,
                                  'dco': br_dco},
                           'path': {'save-dir': self.SaveDir},
                           'font': {'pw-font': pwf},
                           'kernel version': {'version': kver},
                           'comm': {'s-port': sport,
                                    'r-port': rport},
                           'daemon': {'refresh': delay}}

            # Init save Directory
            self.InitSaveDir()

            return self.Config

        except ConfigParser.Error as err:
            print('Bad cfg file : ', err)
            sys.exit(1)
