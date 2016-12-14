# -*- coding: utf-8 -*-
"""
Created on Fri Nov  4 21:49:15 2016

from jupyter_client import manager
kernel_manager, kernel_client = manager.start_new_kernel(extra_arguments=["--matplotlib='inline'"])


note : erase kernel : km.shutdow_kernel()
        restart a dead kernel : km.restart_kernel()

@author: cdesjouy
"""
import jupyter_client
from queue import Empty
from time import sleep
from jupyter_client import BlockingKernelClient, find_connection_file
###############################################################################


def is_runing(cf):
    kc = BlockingKernelClient()
    kc.load_connection_file(cf)
    kc.execute('whos')
    try:
        kc.get_iopub_msg(timeout=0)
    except Empty:
        return False
    else:
        return True
###############################################################################
###############################################################################
###############################################################################
kernel_path = "/run/user/1000/jupyter/"
kernel_id = '31960'

# Connection file
cf = find_connection_file(kernel_id)

# Kernel client
kc = BlockingKernelClient(connection_file=cf)
kc.load_connection_file()

###########################################################################
# load connection info and init communication
###########################################################################
#while True:
#
#    while kc.iopub_channel.msg_ready():
#        data = kc.get_iopub_msg(timeout=0.1)
#        print 'io_pub'
#        print data
#        print '\n'
#
#    while kc.shell_channel.msg_ready():
#        data = kc.get_shell_msg(timeout=0.1)
#        print 'shell'
#        print data
#        print '\n'
#
#    while kc.stdin_channel.msg_ready():
#        data = kc.get_stdin_msg(timeout=0.1)
#        print 'stdin'
#        print data
#        print '\n'
#
#    sleep(1)

