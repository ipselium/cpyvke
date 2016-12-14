#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# File Name :
# Creation Date : mar. 06 déc. 2016 11:49:29 CET
# Last Modified : mar. 06 déc. 2016 11:52:48 CET
# Created By : Cyril Desjouy
#
# Copyright © 2016-2017 Cyril Desjouy <cyril.desjouy@free.fr>
# Distributed under terms of the BSD license.
"""

DESCRIPTION

@author: Cyril Desjouy
"""


###############################################################################
# IMPORTS
###############################################################################
from jupyter_client import find_connection_file, BlockingKernelClient


###############################################################################
#
###############################################################################
cf = find_connection_file("9103")
kc = BlockingKernelClient(connection_file=cf)
kc.load_connection_file(cf)
km = None


# init communication
kc.execute("import numpy as np", store_history=False)
kc.execute("np.set_printoptions(threshold='nan')", store_history=False)


