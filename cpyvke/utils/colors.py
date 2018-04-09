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
# Creation Date : mar. 13 mars 2018 14:48:27 CET
# Last Modified : lun. 09 avril 2018 22:51:01 CEST
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""


import curses
import logging

logger = logging.getLogger("cpyvke")


class Colors:

    def __init__(self, config):
        """ Colors class constructor """

        self.config = config
        curses.start_color()        #
        curses.setupterm()

        self.warning_colors()
        self.main_and_bar_colors()
        self.explorer_colors()
        self.kernel_colors()

    def check_color(self, color):
        """ Check if a color is set to transparent. """

        if color == 'transparent':
            curses.use_default_colors()
            return -1
        elif color.isdigit():
            if curses.COLORS > 8:
                return int(color)
            else:
                logger.error('TERM accept only 8 colors')
                return eval('curses.COLOR_UNDEFINED')
        else:
            return eval('curses.COLOR_' + color.upper())

    def warning_colors(self):
        """ Define warning colors """

        wgtxt = self.config['wg']['txt'].replace(' ', '').split(',')
        wgbdr = self.config['wg']['bdr'].replace(' ', '').split(',')
        try:
            wgtxt_fg = self.check_color(wgtxt[0])
            wgtxt_bg = self.check_color(wgtxt[1])
            wgbdr_fg = self.check_color(wgbdr[0])
            wgbdr_bg = self.check_color(wgbdr[1])
        except Exception as err:
            wgtxt_fg = curses.COLOR_RED
            wgtxt_bg = -1
            wgbdr_fg = curses.COLOR_RED
            wgbdr_bg = -1
            logger.error('%s', err)

        # Define pairs :
        curses.init_pair(1, wgtxt_fg, wgtxt_bg)
        curses.init_pair(2, wgbdr_fg, wgbdr_bg)

    def main_and_bar_colors(self):
        """ Define Main & Bar colors """

        mntxt = self.config['mn']['txt'].replace(' ', '').split(',')
        mnbdr = self.config['mn']['bdr'].replace(' ', '').split(',')
        mnttl = self.config['mn']['ttl'].replace(' ', '').split(',')
        mnhh = self.config['mn']['hh'].replace(' ', '').split(',')
        mnasc = self.config['mn']['asc'].replace(' ', '').split(',')
        try:
            mntxt_fg = self.check_color(mntxt[0])
            mntxt_bg = self.check_color(mntxt[1])
            mnbdr_fg = self.check_color(mnbdr[0])
            mnbdr_bg = self.check_color(mnbdr[1])
            mnttl_fg = self.check_color(mnttl[0])
            mnttl_bg = self.check_color(mnttl[1])
            mnhh_fg = self.check_color(mnhh[0])
            mnhh_bg = self.check_color(mnhh[1])
            mnasc_fg = self.check_color(mnasc[0])
            mnasc_bg = self.check_color(mnasc[1])

        except Exception as err:
            mntxt_fg = curses.COLOR_WHITE
            mntxt_bg = -1
            mnbdr_fg = curses.COLOR_WHITE
            mnbdr_bg = -1
            mnttl_fg = curses.COLOR_WHITE
            mnttl_bg = -1
            mnhh_fg = curses.COLOR_BLACK
            mnhh_bg = curses.COLOR_WHITE
            mnasc_fg = curses.COLOR_RED
            mnasc_bg = -1
            logger.error('%s', err)

        brkn = self.config['br']['kn'].replace(' ', '').split(',')
        brhlp = self.config['br']['hlp'].replace(' ', '').split(',')
        brco = self.config['br']['co'].replace(' ', '').split(',')
        brdco = self.config['br']['dco'].replace(' ', '').split(',')
        try:
            brkn_fg = self.check_color(brkn[0])
            brkn_bg = self.check_color(brkn[1])
            brhlp_fg = self.check_color(brhlp[0])
            brhlp_bg = self.check_color(brhlp[1])
            brco_fg = self.check_color(brco[0])
            brco_bg = self.check_color(brco[1])
            brdco_fg = self.check_color(brdco[0])
            brdco_bg = self.check_color(brdco[1])
        except Exception as err:
            brkn_fg = curses.COLOR_WHITE
            brkn_bg = -1
            brhlp_fg = curses.COLOR_WHITE
            brhlp_bg = -1
            brco_fg = curses.COLOR_GREEN
            brco_bg = -1
            brdco_fg = curses.COLOR_RED
            brdco_bg = -1
            logger.error('%s', err)

        # Define Pairs
        curses.init_pair(11, mntxt_fg, mntxt_bg)
        curses.init_pair(12, mnbdr_fg, mnbdr_bg)
        curses.init_pair(13, mnttl_fg, mnttl_bg)
        curses.init_pair(14, mnhh_fg, mnhh_bg)
        curses.init_pair(16, mnasc_fg, mnasc_bg)
        if mnttl_bg != -1:
            curses.init_pair(15, mnttl_bg, mnbdr_bg)
        else:
            curses.init_pair(15, mnbdr_fg, mnbdr_bg)

        curses.init_pair(41, brkn_fg, brkn_bg)
        curses.init_pair(42, brhlp_fg, brhlp_bg)
        curses.init_pair(43, brco_fg, brco_bg)
        curses.init_pair(44, brdco_fg, brdco_bg)
        curses.init_pair(47, mnbdr_fg, brkn_bg)

        if brdco_bg != -1:
            curses.init_pair(40, brdco_bg, mnbdr_bg)
        else:
            curses.init_pair(40, mnbdr_fg, mnbdr_bg)

        if brco_bg != -1:
            curses.init_pair(49, brco_bg, brkn_bg)
        else:
            curses.init_pair(49, mnbdr_fg, brkn_bg)

        if brkn_bg != -1:
            curses.init_pair(45, brkn_bg, mnbdr_bg)
            curses.init_pair(48, brkn_bg, brco_bg)
        else:
            curses.init_pair(45, mnbdr_fg, mnbdr_bg)
            curses.init_pair(48, mnbdr_fg, brco_bg)

        if brhlp_bg != -1:
            curses.init_pair(46, brhlp_bg, mnbdr_bg)
        else:
            curses.init_pair(46, mnbdr_fg, mnbdr_bg)

    def explorer_colors(self):
        """ Define explorer window colors """

        xptxt = self.config['xp']['txt'].replace(' ', '').split(',')
        xpbdr = self.config['xp']['bdr'].replace(' ', '').split(',')
        xpttl = self.config['xp']['ttl'].replace(' ', '').split(',')
        xphh = self.config['xp']['hh'].replace(' ', '').split(',')
        try:
            xptxt_fg = self.check_color(xptxt[0])
            xptxt_bg = self.check_color(xptxt[1])
            xpbdr_fg = self.check_color(xpbdr[0])
            xpbdr_bg = self.check_color(xpbdr[1])
            xpttl_fg = self.check_color(xpttl[0])
            xpttl_bg = self.check_color(xpttl[1])
            xphh_fg = self.check_color(xphh[0])
            xphh_bg = self.check_color(xphh[1])
        except Exception as err:
            xptxt_fg = curses.COLOR_WHITE
            xptxt_bg = -1
            xpbdr_fg = curses.COLOR_CYAN
            xpbdr_bg = -1
            xpttl_fg = curses.COLOR_CYAN
            xpttl_bg = -1
            xphh_fg = curses.COLOR_BLACK
            xphh_bg = curses.COLOR_CYAN
            logger.error('%s', err)

        # Define pairs
        curses.init_pair(21, xptxt_fg, xptxt_bg)
        curses.init_pair(22, xpbdr_fg, xpbdr_bg)
        curses.init_pair(23, xpttl_fg, xpttl_bg)
        curses.init_pair(24, xphh_fg, xphh_bg)
        if xpttl_bg != -1:
            curses.init_pair(25, xpttl_bg, xpbdr_bg)
        else:
            curses.init_pair(25, xpbdr_fg, xpbdr_bg)

    def kernel_colors(self):
        """ Define kernel window colors """
        kntxt = self.config['kn']['txt'].replace(' ', '').split(',')
        knbdr = self.config['kn']['bdr'].replace(' ', '').split(',')
        knttl = self.config['kn']['ttl'].replace(' ', '').split(',')
        knhh = self.config['kn']['hh'].replace(' ', '').split(',')
        knco = self.config['kn']['co'].replace(' ', '').split(',')
        kndi = self.config['kn']['di'].replace(' ', '').split(',')
        knal = self.config['kn']['al'].replace(' ', '').split(',')
        try:
            kntxt_fg = self.check_color(kntxt[0])
            kntxt_bg = self.check_color(kntxt[1])
            knbdr_fg = self.check_color(knbdr[0])
            knbdr_bg = self.check_color(knbdr[1])
            knttl_fg = self.check_color(knttl[0])
            knttl_bg = self.check_color(knttl[1])
            knhh_fg = self.check_color(knhh[0])
            knhh_bg = self.check_color(knhh[1])
            knco_fg = self.check_color(knco[0])
            knco_bg = self.check_color(knco[1])
            kndi_fg = self.check_color(kndi[0])
            kndi_bg = self.check_color(kndi[1])
            knal_fg = self.check_color(knal[0])
            knal_bg = self.check_color(knal[1])
        except Exception as err:
            kntxt_fg = curses.COLOR_RED
            kntxt_bg = -1
            knbdr_fg = curses.COLOR_RED
            knbdr_bg = -1
            knttl_fg = curses.COLOR_RED
            knttl_bg = -1
            knhh_fg = curses.COLOR_WHITE
            knhh_bg = -1
            knco_fg = curses.COLOR_GREEN
            knco_bg = -1
            knal_fg = curses.COLOR_CYAN
            knal_bg = -1
            kndi_fg = curses.COLOR_RED
            kndi_bg = -1
            logger.error('%s', err)

        # Define pairs
        curses.init_pair(31, kntxt_fg, kntxt_bg)
        curses.init_pair(32, knbdr_fg, knbdr_bg)
        curses.init_pair(33, knttl_fg, knttl_bg)
        curses.init_pair(34, knhh_fg, knhh_bg)
        curses.init_pair(35, knco_fg, knco_bg)
        curses.init_pair(36, knal_fg, knal_bg)
        curses.init_pair(37, kndi_fg, kndi_bg)
        if knttl_bg != -1:
            curses.init_pair(38, knttl_bg, knbdr_bg)
        else:
            curses.init_pair(38, knbdr_fg, knbdr_bg)
