#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Name : test_sock.py
Creation Date : mar. 27 févr. 2018 12:58:06 CET
Last Modified : mar. 27 févr. 2018 23:22:44 CET
Created By : Cyril Desjouy

Copyright © 2016-2018 Cyril Desjouy <ipselium@free.fr>
Distributed under terms of the BSD license.

-----------
DESCRIPTION

@author: Cyril Desjouy
"""


import socket
from threading import *
import time


sport = 8000

MainSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
MainSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
MainSock.bind(('', sport))
MainSock.listen(5)
MainSock.setblocking(0)

client = False

while not client:
    try:
        client_main, address = MainSock.accept()
    except BlockingIOError:
        print('not connected')
        time.sleep(1)
    else:
        client = True
        print("Connection from", address)


while True:
    time.sleep(1)
    msg = client_main.recv(1024)
    print("{} received ".format(msg.decode()))


