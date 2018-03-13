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
# Last Modified : mar. 13 mars 2018 12:15:25 CET
"""
-----------
DOCSTRING

@author: Cyril Desjouy
"""


import struct


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


def disp_id(data):
    """ Display first seq of message id only """
    return data['parent_header']['msg_id'].split('-')[0]


def disp_data(data):
    if data['msg_type'] == 'status':
        dbg = '{} | status : {}'.format(disp_id(data), data['content']['execution_state'])
    elif data['msg_type'] == 'execute_input':
        dbg = '{} | code : {}'.format(disp_id(data), data['content']['code'])
    elif data['msg_type'] == 'stream':
        dbg = '{} | stream'.format(disp_id(data))
    elif data['msg_type'] == 'error':
        dbg = '{} | error : {}'.format(disp_id(data), data['content']['ename'])
    else:
        dbg = '{} {}'.format(disp_id(data), data['msg_type'])
    return dbg
