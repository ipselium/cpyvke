#!/usr/bin/env python
# coding: utf-8

import socket
from time import sleep
from kd5sock import send_msg, recv_msg

# Init connection to daemon
hote = "localhost"
port = 15555

s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s1.connect((hote, port))
s1.setblocking(0)

s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s2.connect((hote, 15556))
s2.setblocking(0)

print("Connection on {}".format(port))

while True:

    try:
        msg = recv_msg(s1)
    except:
        pass
    else:
        print('Received from daemon : \n' + msg)

    sleep(1)

print("Close")
socket.close()
