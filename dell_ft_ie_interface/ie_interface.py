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
import subprocess
import sys
import time
import xml.dom.minidom

# local modules
import firmwaretools as ft
import firmwaretools.plugins as plugins
import firmwaretools.package as package
from firmwaretools.trace_decorator import decorate, traceLog, getLog
import firmwaretools.pycompat as pycompat

import svm
import firmware_addon_dell.extract_common as common
import firmware_addon_dell.HelperXml as xmlHelp
import firmware_addon_dell.biosHdr as biosHdr

plugin_type = (plugins.TYPE_INVENTORY)
requires_api_version = "2.0"

import logging
moduleLog = getLog()
moduleVerboseLog = getLog(prefix="verbose.")

# TODO:
#   1) create _vars.py and create makefile rule to generate
#   2) create a module dir variable we can use here instead of hardcoding
ie_submodule_dir = "./test/ie_test/"

decorate(traceLog())
def numericOnlyCompareStrategy(ver1, ver2):
    ver1 = int(ver1)
    ver2 = int(ver2)
    if ver1 == ver2:
        return 0
    if ver1 > ver2:
        return 1
    return -1

decorate(traceLog())
def textCompareStrategy(ver1, ver2):
    if ver1 == ver2:
        return 0
    if ver1 > ver2:
        return 1
    return -1

class IEInterface(package.RepositoryPackage):
    def __init__(self, *args, **kargs):
        super(DUP, self).__init__(*args, **kargs)
        self.capabilities['can_downgrade'] = False
        self.capabilities['can_reflash'] = False
        if self.version.isdigit():
            self.compareStrategy = numericOnlyCompareStrategy
        elif "." in self.version:
            self.compareStrategy = package.defaultCompareStrategy
        else:
            self.compareStrategy = textCompareStrategy


DELL_VEN_ID = 0x1028

decorate(traceLog())
def inventory_hook(conduit, inventory=None, *args, **kargs):
    base = conduit.getBase()
    cb = base.cb

    moduleLog.info("not verbose --> INFO: hi there")
    moduleVerboseLog.info("verobse INFO: hi there")
    moduleVerboseLog.debug("verobse DEBUG: hi there")

    # Here we will run each installed IE module and collect the results
    # TODO: need to cache results.
    for (path, dirs, files) in pycompat.walkPath(ie_submodule_dir):
        if "PIEConfig.xml" in files:
            moduleLog.info("Running IE Submodule for %s" % path)
            try:
                pieconfigdom = xml.dom.minidom.parse(os.path.join(path,"PIEConfig.xml"))
            except (xml.parsers.expat.ExpatError,), e:
                moduleLog.info("\tcould not parse module PIEConfig.xml, disabling module.")
                continue

            invElem = xmlHelp.getNodeElement(pieconfigdom, "PIEConfig", "Plugins", ("Plugin", {"description":"Inventory"}))
            timeout = xmlHelp.getNodeAttribute(invElem, "timeout")
            invCmd = xmlHelp.getNodeText(invElem, "CliToStdout", "Command")

            moduleLog.info("\tPlugin command is %s" % invCmd)
            moduleLog.info("\tPlugin timeout is %s" % timeout)

            subproc = invCmd.split(" ")
            subproc[0] = os.path.realpath(os.path.join(path, subproc[0]))
            moduleLog.info("\tRunning plugin: %s", subproc)

            pobj = subprocess.Popen( subproc, cwd=path, stdout=subprocess.PIPE )
            (stdout, stderr) = pobj.communicate(None)
            # TODO: need to implement timeout (little bit harder...)

            moduleLog.info("\tGOT INVENTORY: %s" % stdout)






