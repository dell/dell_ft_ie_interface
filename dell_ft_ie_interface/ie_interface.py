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
import glob
import os
import shutil
import stat
try:
    import subprocess
except ImportError:
    import firmwaretools.compat_subprocess as subprocess
import sys
import tempfile
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
moduleUpdateLog = getLog(prefix="ftupdates.")

# TODO:
#   1) create _vars.py and create makefile rule to generate
#   2) create a module dir variable we can use here instead of hardcoding
ie_submodule_dir = dell_ft_ie_interface.PKGLIBEXECDIR
if not os.path.exists(ie_submodule_dir):
    ie_submodule_dir = "/usr/libexec/dell_dup/"

class ExecutionError(package.InstallError,): pass

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
        moduleVerboseLog.debug("Setting compare function")
        if self.version.isdigit():
            moduleVerboseLog.debug("\tnumericOnly")
            self.compareStrategy = numericOnlyCompareStrategy
        elif "." in self.version:
            moduleVerboseLog.debug("\tdefault")
            self.compareStrategy = package.defaultCompareStrategy
        else:
            moduleVerboseLog.debug("\ttext")
            self.compareStrategy = textCompareStrategy

        # test harness sets this to None. No real use has this set to None
        if self.conf is not None:
            self.ie_module_path = os.path.join(ie_submodule_dir, self.conf.get("package", "ie_type"))
            self.pieconffile = os.path.join(ie_submodule_dir, self.conf.get("package", "ie_type"), "PIEConfig.xml")
            moduleVerboseLog.info("loading xml from: %s" % self.pieconffile)
            self.pieconfigdom = xml.dom.minidom.parse(self.pieconffile)
            moduleVerboseLog.info("loaded.")

    decorate(traceLog())
    def install(self):
        self.status = "in_progress"
        moduleVerboseLog.info("hey, we are supposed to be installing now... :)")
        moduleUpdateLog.debug("Attempting Firmware Update")
        try:
            user = os.environ['USER']
            moduleUpdateLog.debug("Attempted by user: %s" % user)
        except KeyError:
            pass
        try:
            user = os.environ['SUDO_USER']
            moduleUpdateLog.debug("Attempted by sudo user: %s" % user)
        except KeyError:
            pass        
        moduleUpdateLog.debug("Package name: %s" % self.name)
        moduleUpdateLog.debug("Package display name: %s" % str(self))
        moduleUpdateLog.debug("Package version: %s" % self.version)
        moduleUpdateLog.debug("Devices:")
        for device in self.deviceList:
            moduleUpdateLog.debug("Device name: %s" % device.name)
            moduleUpdateLog.debug("Device display name: %s" % str(device))
            moduleUpdateLog.debug("Device version: %s" % device.version)
            

        tempdir = tempfile.mkdtemp(prefix="firmware_install")
        try:
            shutil.copytree(self.ie_module_path, os.path.join(tempdir, "ie"))
            if os.path.exists(os.path.join(tempdir, "ie", "donotmovepayload")):
                payloadDest = os.path.join(tempdir, "ie", "payload")
                os.mkdir(payloadDest, 0755)
            else:
                payloadDest = os.path.join(tempdir, "ie")
            for fname in glob.glob(os.path.join(self.path, "*")):
                if os.path.isdir(fname):
                    shutil.copytree(fname, os.path.join(payloadDest, os.path.basename(fname)))
                else:
                    shutil.copy(fname, payloadDest)

            if os.path.exists(os.path.join(tempdir, "ie", "payload")):
                for file in ["dell-std-license.txt", "package.ini", "package.xml", ]:
                    fullFile = os.path.join(tempdir, "ie", "payload", file)
                    if os.path.exists(fullFile):
                        shutil.move(fullFile, os.path.join(tempdir, "ie", file))

            stdout = runCmdFromPIEConfig(self.pieconfigdom, "Execution", "CliforceToFile", os.path.join(tempdir, "ie"))

            svmexecution = xml.dom.minidom.parseString(stdout)
            spstatus = xmlHelp.getNodeElement(svmexecution, "SVMExecution", "SPStatus")
            if not spstatus:
                spstatus = xmlHelp.getNodeElement(svmexecution, "SVMExecution", "Device", "Application", "SPStatus")
            if not spstatus:
                message="Could not determine status"
                self.status = "failed"
                raise ExecutionError(message)
                
            res = xmlHelp.getNodeAttribute(spstatus, "result")

            self.status = "failed"
            if res.lower() == "true":
                self.status = "success"

            message="Firmware update failed."
            try:
                message = xmlHelp.getNodeText(spstatus, "Message").strip()
                self.status = "custom_msg_%s" % self.name
                package.packageStatusEnum[ self.status ] = message
            except Exception:
                pass

            if res.lower() != "true":
                raise ExecutionError(message)

        finally:
            moduleUpdateLog.debug("Update result: %s" % self.getStatusStr())
            shutil.rmtree(tempdir)


def runCmdFromPIEConfig(dom, which, cmd, path):
    updElem = xmlHelp.getNodeElement(dom, "PIEConfig", "Plugins", ("Plugin", {"description": which}))
    timeout = xmlHelp.getNodeAttribute(updElem, "timeout")
    cmdToRun = xmlHelp.getNodeText(updElem, cmd, "Command")
    outFile = xmlHelp.getNodeText(updElem, cmd, "Output")

    moduleVerboseLog.info("\tPlugin command is %s" % cmdToRun)
    moduleVerboseLog.info("\tOutput file is %s" % outFile)
    moduleVerboseLog.info("\tPlugin timeout is %s" % timeout)
    cmdToRun = "./" + cmdToRun

    nullfd_r = open("/dev/null", "r")
    nullfd_w = open("/dev/null", "w")

    pobj = subprocess.Popen(cmdToRun, cwd=path, stdout=nullfd_w, stderr=nullfd_w, stdin=nullfd_r, close_fds=1, shell=True)
    pobj.wait()

    xmlout = open(os.path.join(path, outFile), "r")
    output = xmlout.read()
    # TODO: need to implement timeout (little bit harder...)

    moduleVerboseLog.info("output from the cmd was: \n%s" % output)
    return output


DELL_VEN_ID = 0x1028

decorate(traceLog())
def inventory_hook(conduit, inventory=None, *args, **kargs):
    base = conduit.getBase()
    cb = base.cb

    moduleVerboseLog.info("not verbose --> INFO: hi there")
    moduleVerboseLog.info("verobse INFO: hi there")
    moduleVerboseLog.debug("verobse DEBUG: hi there")

    # Here we will run each installed IE module and collect the results
    # TODO: need to cache results.
    for (path, dirs, files) in pycompat.walkPath(ie_submodule_dir):
        if "PIEConfig.xml" in files:
            moduleVerboseLog.info("Running IE Submodule for %s" % path)
            try:
                pieconfigdom = xml.dom.minidom.parse(os.path.join(path,"PIEConfig.xml"))
            except (xml.parsers.expat.ExpatError,), e:
                moduleVerboseLog.info("\tcould not parse module PIEConfig.xml, disabling module.")
                continue
            
            venId, sysId = base.getSystemId()
            supportedSysIds = []
            for modelNode in xmlHelp.iterNodeElement(pieconfigdom, "PIEConfig", "SupportedSystems", "Brand", "Model" ):
                supportedSysIds.append(int(xmlHelp.getNodeAttribute(modelNode, "systemID"), 16))
            if len(supportedSysIds) > 0 and sysId not in supportedSysIds:
                moduleVerboseLog.info("\tModule not for this system, disabling module.")
                continue                

            stdout = runCmdFromPIEConfig(pieconfigdom, "Inventory", "CliToFile", path)

            for device in svm.genPackagesFromSvmXml(stdout):
                inventory.addDevice(device)
                moduleVerboseLog.info("Added DEVICE: %s" % device.name)





