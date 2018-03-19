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
# Creation Date : lun. 19 mars 2018 14:18:03 CET
# Last Modified : lun. 19 mars 2018 16:24:10 CET
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import os
import time
import logging

from cpyvke.utils.sockets import SocketManager
from cpyvke.utils.config import cfg_setup
from logging.handlers import RotatingFileHandler
from cpyvke.utils.comm import recv_msg
from cpyvke.utils.display import whos_to_dic

cfg = cfg_setup()
config = cfg.RunCfg()

logdir = os.path.expanduser('~') + '/.cpyvke/'
logfile = logdir + 'cpyvke.log'

# Logger
logger = logging.getLogger("cpyvke")
logger.setLevel(logging.DEBUG)

# create the logging file handler
handler = RotatingFileHandler(logfile, maxBytes=10*1024*1024,
                              backupCount=5)
logmsg = '%(asctime)s :: %(name)s :: %(threadName)s :: %(levelname)s :: %(message)s'
formatter = logging.Formatter(logmsg, datefmt='%Y-%m-%d - %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)


sock = SocketManager(config, logger)

while True:
    # Check Connection to daemon

    sock.check_main_socket()

    if not sock.connected:
        time.sleep(1)
        while not sock.connected:
            try:
                sock.init_sockets()
            except Exception:
                logger.error('Connection to stream socket failed : \n', exc_info=True)
            else:
                sock.connected = True

    else:
        try:
            tmp = recv_msg(sock.MainSock).decode('utf8')
        except BlockingIOError:     # If no message !
            pass
        except OSError:             # If user disconnect cpyvke from socket
            pass
        except AttributeError:      # If kd5 is stopped
            pass
        else:
            if tmp:
                lst = whos_to_dic(tmp)
                logger.info('Variable list updated')
                logger.debug('\n%s', tmp)
                try:
                    # remove temporary file used by daemon from the list
                    del lst['fcpyvke0']
                except KeyError:
                    pass
