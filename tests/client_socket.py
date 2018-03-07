#!/usr/bin/env python
# coding: utf-8

import socket
from time import sleep
import struct



def recv_msg(sock):
    ''' Read message length and unpack it into an integer '''
    raw_msglen = recv_all(sock, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    return recv_all(sock, msglen)


def recv_all(sock, n):
    ''' Helper function to recv n bytes or return None if EOF is hit '''
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data


def WhoToDict(string):
    ''' Format output of daemon to a dictionnary '''

    variables = {}
    for item in string.split('\n')[2:-1]:
        tmp = [j for j in item.split(' ') if j is not '']
        var_name = tmp[0]
        var_typ = tmp[1]
        var_val = ' '.join(tmp[2:])
        if var_typ != 'function':
            variables[var_name] = {'value': var_val, 'type': var_typ}
    return variables


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
        msg = recv_msg(s1).decode('utf8')
#        msg = s1.recv(4)
    except BlockingIOError:
        pass
    else:
        print('Received from daemon : \n')
        print(msg)
        var = WhoToDict(msg)
        print("variables =")
        print(var)

    sleep(1)

print("Close")
socket.close()
