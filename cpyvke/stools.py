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
# Creation Date : jeu. 01 mars 2018 15:09:06 CET
# Last Modified : sam. 10 mars 2018 20:19:21 CET
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""


import struct


def WhoToDict(string):
    """ Format output of daemon to a dictionnary """

    variables = {}
    for item in string.split('\n')[2:]:
        tmp = [j for j in item.split(' ') if j is not '']
        if tmp:
            var_name = tmp[0]
            var_typ = tmp[1]
            var_val = ' '.join(tmp[2:])
            variables[var_name] = {'value': var_val, 'type': var_typ}
    return variables


def send_msg(sock, msg):
    """ Prefix each message with a 4-byte length (network byte order) """
    msg = struct.pack('>I', len(msg)) + msg.encode('utf8')
    sock.sendall(msg)


def recv_msg(sock):
    """ Read message length and unpack it into an integer """
    raw_msglen = recv_all(sock, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    return recv_all(sock, msglen)


def recv_all(sock, n):
    """ Helper function to recv n bytes or return None if EOF is hit """
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data
