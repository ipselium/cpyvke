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
# Creation Date : mer. 28 mars 2018 23:07:12 CEST
# Last Modified : jeu. 29 mars 2018 00:09:09 CEST
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import os
import sys
import psutil
import subprocess


def kd_status(pidfile):
    """ Check kd5 status """

    if os.path.exists(pidfile):
        if is_kd_running(pidfile):
            return read_pid(pidfile)
        else:
            os.remove(pidfile)
            return None
    else:
        pids = find_lost_pid()
        if len(pids) == 1:
            with open(pidfile, 'w') as f:
                f.write(pids[0])
            return pids[0]
        else:
            return None


def find_lost_pid():
    cur_pid = os.getpid()
    pids = []
    for proc in psutil.process_iter():
        pinfo = proc.as_dict(attrs=['pid', 'name'])
        if pinfo['name'] == 'kd5' and pinfo['pid'] != cur_pid:
            pids.append(pinfo['pid'])
    return pids


def read_pid(pidfile):
    """ Read the pid in pidfile """

    with open(pidfile, 'r') as f:
        pid = int(f.read())
    return pid


def kdread(cfile):
    """ read lockfile | pidfile """

    if os.path.exists(cfile):
        with open(cfile, "r") as f:
            return f.readline().replace('\n', '')
    else:
        message = 'Error :\tCannot find {} !\n\tExiting\n'
        sys.stderr.write(message.format(cfile))
        return None


def kdwrite(cfile, content):
    """ write lockfile | pidfile """

    with open(cfile, "w") as f:
        f.write(content)


def is_kd_running(pidfile):
    """ Check if process with pid (in pidfile) is actually running"""

    pid = read_pid(pidfile)
    if psutil.pid_exists(pid):
        return True
    else:
        return False


def restart_daemon():
    """ Restart kd5 """

    subprocess.Popen(["kd5", "restart"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
