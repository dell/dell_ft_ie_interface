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
import dell_ft_ie_interface

plugin_type = (plugins.TYPE_INVENTORY)
requires_api_version = "2.0"

import logging
moduleLog = getLog()
moduleVerboseLog = getLog(prefix="verbose.")

# TODO:
#   1) create _vars.py and create makefile rule to generate
#   2) create a module dir variable we can use here instead of hardcoding
ie_submodule_dir = dell_ft_ie_interface.PKGLIBEXECDIR

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
        super(IEInterface, self).__init__(*args, **kargs)
        self.capabilities['can_downgrade'] = True
        self.capabilities['can_reflash'] = True
        moduleLog.info("Setting compare function")
        if self.version.isdigit():
            moduleLog.info("\tnumericOnly")
            self.compareStrategy = numericOnlyCompareStrategy
        elif "." in self.version:
            moduleLog.info("\tdefault")
            self.compareStrategy = package.defaultCompareStrategy
        else:
            moduleLog.info("\ttext")
            self.compareStrategy = textCompareStrategy

        self.pieconffile = os.path.join(ie_submodule_dir, self.conf.get("package", "ie_type"), "PIEConfig.xml")
        moduleLog.info("loading xml from: %s" % self.pieconffile)
        self.pieconfigdom = xml.dom.minidom.parse(self.pieconffile)
        moduleLog.info("loaded.")

    decorate(traceLog())
    def install(self):
        self.status = "in_progress"
        moduleLog.info("hey, we are supposed to be installing now... :)")
        #self.status = "failed"
        #self.status = "warm_reboot_needed"

        # TODO: the following code is duplicated and should be pushed into its own function
        updElem = xmlHelp.getNodeElement(self.pieconfigdom, "PIEConfig", "Plugins", ("Plugin", {"description":"Execution"}))
        timeout = xmlHelp.getNodeAttribute(updElem, "timeout")
        invCmd = xmlHelp.getNodeText(updElem, "CliforceToStdout", "Command")

        moduleLog.info("\tPlugin command is %s" % invCmd)
        moduleLog.info("\tPlugin timeout is %s" % timeout)

        subproc = invCmd.split(" ")
        ie_module_path = os.path.join(ie_submodule_dir, self.conf.get("package", "ie_type"))
        subproc[0] = os.path.realpath(os.path.join(ie_module_path, subproc[0]))
        moduleLog.info("\tRunning plugin: %s", subproc)

        pobj = subprocess.Popen( subproc, cwd=ie_module_path, stdout=subprocess.PIPE )
        (stdout, stderr) = pobj.communicate(None)
        # TODO: need to implement timeout (little bit harder...)

        # TODO: parse stdout to see if it succeeded or failed (its xml, yay! <-- (sarcasm))
        self.status = "success"

        moduleLog.info("output from the execution module was: \n%s" % stdout)


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

            for device in svm.genPackagesFromSvmXml(stdout):
                inventory.addDevice(device)
                moduleLog.info("Added DEVICE: %s" % device.name)





