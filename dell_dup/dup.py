#!/usr/bin/python
# vim:expandtab:textwidth=0:autoindent:tabstop=4:shiftwidth=4:filetype=python:

  #############################################################################
  #
  # Copyright (c) 2005 Dell Computer Corporation
  # Dual Licenced under GNU GPL and OSL
  #
  #############################################################################
"""module

some docs here eventually.
"""

from __future__ import generators

# import arranged alphabetically
import commands
import os
import stat
import sys

# local modules
import firmwaretools.package as package
import firmware_addon_dell.svm as svm
from firmwaretools.trace_decorator import decorate, traceLog, getLog
import lsi_raid_inventory

import firmwaretools.plugins as plugins

plugin_type = (plugins.TYPE_INVENTORY)
requires_api_version = "2.0"

decorate(traceLog())
def config_hook(conduit, *args, **kargs):
    pass
    conduit.getBase().registerInventoryFunction("inventory_dup", InventoryFromDup)

# not optimal. Need to internalize this at some point in future.
decorate(traceLog())
def InventoryFromDup():
    for cmd in cmds:
        (status, inventoryXml) = commands.getstatusoutput(cmdstr % cmd)
        for pkg in svm.genPackagesFromSvmXml(inventoryXml):
            yield pkg



