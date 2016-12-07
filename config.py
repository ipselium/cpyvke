#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : cfg_test.py
# Creation Date : mar. 29 nov. 2016 23:18:27 CET
# Last Modified : mer. 07 déc. 2016 13:17:41 CET
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
import time


def CheckDir(dir):
    ''' Check if dir exists. If not, create it.'''

    if os.path.isdir(dir) is False:
        os.makedirs(dir)
        print("Create directory : " + str(dir))
        time.sleep(0.5)


class cfg_setup(object):
    ''' Handle configuration file. '''

    def __init__(self):

        self.cfg = ConfigParser.RawConfigParser()
        self.home = os.path.expanduser("~")
        self.path = self.home + '/.cpyvke/'
        # Check if config dir exists. If not create it.
        if os.path.exists(self.path) is False:
            os.makedirs(self.path)
            print("Create configuration directory : " + str(self.path))
            time.sleep(0.5)

    def InitCfg(self):
        ''' Check if cpyvke.conf exists. If not create it. '''

        if os.path.exists(self.path + 'cpyvke.conf') is False:
            open(self.path + 'cpyvke.conf', 'a').close()
            print("Create configuration file : " + str(self.path + 'cpyvke.conf'))
            time.sleep(0.5)
            self.WriteConfig()

    def WriteConfig(self):
        ''' Write configuration file. '''

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

        with open(self.path + 'cpyvke.conf', 'wb') as configfile:
            self.cfg.write(configfile)

    def InitSaveDir(self):
        ''' Check|create configuration directories. '''

        if os.path.exists(self.SaveDir) is False:
            os.makedirs(self.SaveDir)
            print("Create save directory : " + str(self.SaveDir))
            time.sleep(0.5)

    def RunCfg(self):
        ''' Run configuration. '''

        try:
            # Check if config file exist. If not create it
            self.InitCfg()
            # Read config file
            self.cfg.read(self.path + 'cpyvke.conf')

            # PATH
            if self.cfg.has_section('path'):
                # SaveDir
                if self.cfg.has_option('path', 'save-dir'):
                    self.SaveDir = self.cfg.get('path', 'save-dir')
                    self.SaveDir = self.SaveDir.replace('$HOME', self.home)
                    if self.SaveDir[-1] != '/':
                        self.SaveDir = self.SaveDir + '/'
                else:
                    self.SaveDir = self.path + 'save/'
            else:
                self.SaveDir = self.path + 'save/'

            # FONT
            if self.cfg.has_section('font'):
                # SaveDir
                if self.cfg.has_option('font', 'powerline-font'):
                    pwf = self.cfg.get('font', 'powerline-font')
                else:
                    pwf = 'False'
            else:
                pwf = 'False'

            # WARNING COLORS
            if self.cfg.has_section('warning colors'):
                if self.cfg.has_option('warning colors', 'text'):
                    wg_txt = self.cfg.get('warning colors', 'text')
                else:
                    wg_txt = "red, transparent"

                if self.cfg.has_option('warning colors', 'border'):
                    wg_bdr = self.cfg.get('warning colors', 'border')
                else:
                    wg_bdr = "red, transparent"
            else:
                wg_txt = "red, transparent"
                wg_bdr = "red, transparent"

            # BAR COLORS
            if self.cfg.has_section('bar colors'):
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

            else:
                br_kn = "white, transparent"
                br_hlp = "white, transparent"
                br_co = "green, transparent"
                br_dco = "red, transparent"

            # MAIN COLORS
            if self.cfg.has_section('main colors'):
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

            else:
                main_txt = "white, transparent"
                main_bdr = "white, transparent"
                main_ttl = "white, transparent"
                main_hh = "black, cyan"

            # EXPLORER COLORS
            if self.cfg.has_section('explorer colors'):
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

            else:
                exp_txt = "white, transparent"
                exp_bdr = "cyan transparent"
                exp_ttl = "cyan, transparent"
                exp_hh = "black, cyan"

            # KERNEL COLORS
            if self.cfg.has_section('kernel colors'):
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

            else:
                kn_txt = "white, transparent"
                kn_bdr = "red, transparent"
                kn_ttl = "red, transparent"
                kn_hh = "black, red"
                kn_al = "cyan, transparent"
                kn_co = "green, transparent"
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
                           'font': {'pw-font': pwf}}

            # Init save Directory
            self.InitSaveDir()

            return self.Config

        except ConfigParser.Error as err:
            print('Bad cfg file : ', err)
            sys.exit(1)

