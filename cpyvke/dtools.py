#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Name : dtools.py
Creation Date : ven. 09 mars 2018 14:50:19 CET
Last Modified : ven. 09 mars 2018 14:51:12 CET
Created By : Cyril Desjouy

Copyright © 2016-2018 Cyril Desjouy <ipselium@free.fr>
Distributed under terms of the BSD license.

-----------
DESCRIPTION

@author: Cyril Desjouy
"""


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
