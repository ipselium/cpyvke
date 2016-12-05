#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name : cfg_test.py
# Creation Date : mar. 29 nov. 2016 23:18:27 CET
# Last Modified : mar. 06 déc. 2016 00:32:34 CET
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
        self.cfg.set('main colors', 'title-color', 'white, transparent')
        self.cfg.set('main colors', 'text-color', 'white, transparent')
        self.cfg.set('main colors', 'highlight-color', 'black, cyan')
        self.cfg.set('main colors', 'border-color', 'white, transparent')

        self.cfg.add_section('explorer colors')
        self.cfg.set('explorer colors', 'title-color', 'cyan, transparent')
        self.cfg.set('explorer colors', 'text-color', 'white, transparent')
        self.cfg.set('explorer colors', 'highlight-color', 'black, cyan')
        self.cfg.set('explorer colors', 'border-color', 'cyan, transparent')

        self.cfg.add_section('kernel colors')
        self.cfg.set('kernel colors', 'title-color', 'red, transparent')
        self.cfg.set('kernel colors', 'text-color', 'white, transparent')
        self.cfg.set('kernel colors', 'highlight-color', 'white, transparent')
        self.cfg.set('kernel colors', 'border-color', 'red, transparent')
        self.cfg.set('kernel colors', 'connected-color', 'green, transparent')
        self.cfg.set('kernel colors', 'died-color', 'red, transparent')
        self.cfg.set('kernel colors', 'alive-color', 'cyan, transparent')

        self.cfg.add_section('warning colors')
        self.cfg.set('warning colors', 'text-color', 'red, transparent')
        self.cfg.set('warning colors', 'border-color', 'red, transparent')

        self.cfg.add_section('path')
        self.cfg.set('path', 'save-dir', '$HOME/.cpyvke/save/')
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

            # WARNING COLORS
            if self.cfg.has_section('warning colors'):
                if self.cfg.has_option('warning colors', 'text-color'):
                    wg_txt = self.cfg.get('warning colors', 'text-color')
                else:
                    wg_txt = "red, transparent"

                if self.cfg.has_option('warning colors', 'border-color'):
                    wg_bdr = self.cfg.get('warning colors', 'border-color')
                else:
                    wg_bdr = "red, transparent"
            else:
                wg_txt = "red, transparent"
                wg_bdr = "red, transparent"


            # MAIN COLORS
            if self.cfg.has_section('main colors'):
                if self.cfg.has_option('main colors', 'text-color'):
                    main_txt = self.cfg.get('main colors', 'text-color')
                else:
                    main_txt = "white, transparent"

                if self.cfg.has_option('main colors', 'border-color'):
                    main_bdr = self.cfg.get('main colors', 'border-color')
                else:
                    main_bdr = "white, transparent"

                if self.cfg.has_option('main colors', 'title-color'):
                    main_ttl = self.cfg.get('main colors', 'title-color')
                else:
                    main_ttl = "white, transparent"

                if self.cfg.has_option('main colors', 'highlight-color'):
                    main_hh = self.cfg.get('main colors', 'highlight-color')
                else:
                    main_hh = "black, cyan"

            else:
                main_txt = "white, transparent"
                main_bdr = "white, transparent"
                main_ttl = "white, transparent"
                main_hh = "black, cyan"

            # EXPLORER COLORS
            if self.cfg.has_section('explorer colors'):
                if self.cfg.has_option('explorer colors', 'text-color'):
                    exp_txt = self.cfg.get('explorer colors', 'text-color')
                else:
                    exp_txt = "white, transparent"

                if self.cfg.has_option('explorer colors', 'border-color'):
                    exp_bdr = self.cfg.get('explorer colors', 'border-color')
                else:
                    exp_bdr = "white, transparent"

                if self.cfg.has_option('explorer colors', 'title-color'):
                    exp_ttl = self.cfg.get('explorer colors', 'title-color')
                else:
                    exp_ttl = "white, transparent"

                if self.cfg.has_option('explorer colors', 'highlight-color'):
                    exp_hh = self.cfg.get('explorer colors', 'highlight-color')
                else:
                    exp_hh = "black, cyan"

            else:
                exp_txt = "white, transparent"
                exp_bdr = "cyan transparent"
                exp_ttl = "cyan, transparent"
                exp_hh = "black, cyan"

            # KERNEL COLORS
            if self.cfg.has_section('kernel colors'):
                if self.cfg.has_option('kernel colors', 'text-color'):
                    kn_txt = self.cfg.get('kernel colors', 'text-color')
                else:
                    kn_txt = "white, transparent"

                if self.cfg.has_option('kernel colors', 'border-color'):
                    kn_bdr = self.cfg.get('kernel colors', 'border-color')
                else:
                    kn_bdr = "white, transparent"

                if self.cfg.has_option('kernel colors', 'title-color'):
                    kn_ttl = self.cfg.get('kernel colors', 'title-color')
                else:
                    kn_ttl = "white, transparent"

                if self.cfg.has_option('kernel colors', 'highlight-color'):
                    kn_hh = self.cfg.get('kernel colors', 'highlight-color')
                else:
                    kn_hh = "black, red"

                if self.cfg.has_option('kernel colors', 'connected-color'):
                    kn_co = self.cfg.get('kernel colors', 'connected-color')
                else:
                    kn_co = "green, transparent"

                if self.cfg.has_option('kernel colors', 'alive-color'):
                    kn_al = self.cfg.get('kernel colors', 'alive-color')
                else:
                    kn_al = "cyan, transparent"

                if self.cfg.has_option('kernel colors', 'died-color'):
                    kn_di = self.cfg.get('kernel colors', 'died-color')
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
            self.Config = {'mn': {'txt' : main_txt,
                                           'bdr' : main_bdr,
                                           'ttl' : main_ttl,
                                           'hh' : main_hh},
                           'xp': {'txt' : exp_txt,
                                               'bdr' : exp_bdr,
                                               'ttl' : exp_ttl,
                                               'hh' : exp_hh},
                           'kn': {'txt' : kn_txt,
                                             'bdr' : kn_bdr,
                                             'ttl' : kn_ttl,
                                             'hh' : kn_hh,
                                             'co' : kn_co,
                                             'di' : kn_di,
                                             'al' : kn_al},
                           'wg': {'txt' : wg_txt,
                                              'bdr' : wg_bdr},
                           'path': {'save-dir' : self.SaveDir}}
            # Init save Directory
            self.InitSaveDir()

            return self.Config

        except ConfigParser.Error, err:
            print('Bad cfg file : ', err)
            sys.exit(1)

