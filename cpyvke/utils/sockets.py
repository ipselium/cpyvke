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
# Creation Date : jeu. 15 mars 2018 18:07:10 CET
# Last Modified : dim. 25 mars 2018 21:21:36 CEST
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""

import socket
from cpyvke.utils.comm import send_msg


class SocketManager:

    def __init__(self, config, logger):

        self.config = config
        self.logger = logger
        self.connected = False
        self.init_sockets()

    def init_main_socket(self):
        """ Init Main Socket. """

        try:
            hote = "localhost"
            sport = int(self.config['comm']['s-port'])
            self.MainSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.MainSock.connect((hote, sport))
            self.MainSock.setblocking(0)
            self.logger.debug('Connected to main socket')
        except ConnectionRefusedError:
            self.logger.error('Connection to stream socket failed ')

    def init_request_socket(self):
        """ Init Request Socket. """

        try:
            hote = "localhost"
            rport = int(self.config['comm']['r-port'])
            self.RequestSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.RequestSock.connect((hote, rport))
            self.RequestSock.setblocking(0)
            self.logger.debug('Connected to request socket')
        except Exception:
            self.logger.error('Connection to stream socket failed : \n', exc_info=True)

    def init_sockets(self):
        """ Init all sockets """

        self.init_main_socket()
        self.init_request_socket()

    def close_main_socket(self):
        """ Close Main socket. """

        try:
            self.MainSock.close()
            self.logger.debug('Main socket closed')
        except Exception:
            self.logger.error('Unable to close socket : ', exc_info=True)
            pass

    def close_request_socket(self):
        """ Close Request socket. """

        try:
            self.RequestSock.close()
            self.logger.debug('Request socket closed')
        except Exception:
            self.logger.error('Unable to close socket : ', exc_info=True)
            pass

    def close_sockets(self):
        """ Close all sockets """

        self.close_main_socket()
        self.close_request_socket()

    def restart_sockets(self):
        """ Stop then start connection to sockets. """

        self.close_sockets()
        self.init_sockets()

    def check_main_socket(self):
        """ Test if connection to daemon is alive. """

        try:
            send_msg(self.MainSock, '<TEST>')
            self.connected = True
        except BlockingIOError:
            self.connected = True
        except OSError:
            self.connected = False

    def warning_socket(self, wng):
        """ Check connection and display warning. """

        self.check_main_socket()
        if self.connected:
            wng.display('  Connected to socket  ')
        else:
            wng.display(' Disconnected from socket ')

    def force_update(self, wng):
        """ Force update of variable list sending fake code to Daemon """

        send_msg(self.RequestSock, '<code> ')
        wng.display('Reloading Variable List...')

    def del_var(self, varname, wng):
        """ Delete a variable from kernel. """

        code = 'del {}'.format(varname)
        try:
            send_msg(self.RequestSock, '<code>' + code)
            self.logger.debug("Send delete signal for variable {}".format(varname))
        except Exception:
            self.logger.error('Delete variable :', exc_info=True)
            wng.display('Kernel Busy ! Try again...')
        else:
            wng.display('Variable {} deleted'.format(varname))
