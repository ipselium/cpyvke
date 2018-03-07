# -*- coding: utf-8 -*-
"""
Created on Wed Nov 16 18:12:40 2016

@author: cdesjouy
"""

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-n", "--new", help="Start up with a new kernel", action="store_true")
parser.add_argument("-e", "--existing", help="Start up with existing kernel")
parser.add_argument("-d", "--only_daemon", help="Only start up daemon", action="store_true")
parser.add_argument("-c", "--only_cui", help="Only start up curse user interface", action="store_true")
parser.add_argument("-r", "--refresh_delay", help="Refresh delay of the interface [in ms]", nargs='?', const=0.5, type=float, default=0.5)
args = parser.parse_args()


print('Arg existing ? :' + str(args.existing))
print('new   : ' + str(args.new))
print('daemon: ' + str(args.only_daemon))
print('cui   : ' + str(args.only_cui))

print('Delay : ' + str(args.refresh_delay))
print('Type delay : ' + str(type(args.refresh_delay)))

