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

import firmwaretools.plugins as plugins
import firmware_addon_dell.extract_common as common

plugin_type = (plugins.TYPE_INVENTORY)
requires_api_version = "2.0"

base = None
decorate(traceLog())
def config_hook(conduit, *args, **kargs):
    global base
    base = conduit.getBase()
    base.registerInventoryFunction("inventory_dup", InventoryFromDup)

class DUP(package.RepositoryPackage):
    def __init__(self, *args, **kargs):
        super(DUP, self).__init__(*args, **kargs)
        self.capabilities['can_downgrade'] = False
        self.capabilities['can_reflash'] = False

def getPieConfig(pkg):
    for pieConfig in ("PIEConfig.sh", "framework/PIEConfig.sh"):
        if os.path.exists( os.path.join(pkg.path, pieConfig )):
            return os.path.join(pkg.path, pieConfig)
    raise IOError, "PIEConfig.sh not found in package: %s" % pkg.path

vars = ["sInventoryCliBin", "sInventoryCliArgs", "sInventoryCliTimeout",
        "sExecutionCliBin", "sExecutionCliArgs", "sExecutionCliTimeout", "sExecutionCliForceArgs" ]

def getDupPIE(pkg):
    fd = open( getPieConfig(pkg), "r" )
    pie = {}
    while True:
        line = fd.readline()
        if line == "": break
        if line[-1:] == "\n": line = line[:-1]
        for i in vars:
            if line.startswith( i + "=" ):
                pie[i] = line.replace( i + "=", "" )
                pie[i] = pie[i].replace('"', '')

    return pie

decorate(traceLog())
def InventoryFromDup(*args, **kargs):
    for pkg in base.repo.iterPackages():
        if not isinstance(pkg, DUP): continue
        savePath = os.environ["PATH"]
        try:
            pie = getDupPIE(pkg)
            os.environ["PATH"] = os.path.pathsep.join([os.environ.get('PATH',''), pkg.path])
            out = common.loggedCmd( pie["sInventoryCliBin"] + " " + pie["sInventoryCliArgs"], shell=True, returnOutput=True, cwd=pkg.path, timeout=int(pie["sInventoryCliTimeout"]), logger=getLog())

            for pkg in svm.genPackagesFromSvmXml(out):
                yield pkg
        except IOError:
            pass

        os.environ["PATH"] = savePath
