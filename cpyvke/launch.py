#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Name :
Creation Date :
Last Modified : ven. 02 mars 2018 15:32:26 CET
Created By : Cyril Desjouy

Copyright © 2016-2018 Cyril Desjouy <ipselium@free.fr>
Distributed under terms of the BSD license.

-----------
DESCRIPTION

@author: Cyril Desjouy
"""


import os


def main():
    '''
    launch ipython console.
    '''
    logdir = os.path.expanduser('~') + '/.cpyvke/'
    lockfile = logdir + 'kd5.lock'

    if os.path.exists(lockfile):
        with open(lockfile, 'r') as f:
            kernel_id = f.readline()

        cmd = 'jupyter console --existing kernel-{}.json'.format(kernel_id)
        os.system(cmd)

    else:
        print('No associated kernel found !')


if __name__ == "__main__":
    main()
