#!/usr/bin/python
# vim:expandtab:autoindent:tabstop=4:shiftwidth=4:filetype=python:textwidth=0:

  #############################################################################
  #
  # Copyright (c) 2005 Dell Computer Corporation
  # Dual Licenced under GNU GPL and OSL
  #
  #############################################################################
"""extract_dup:  not executable
"""

from __future__ import generators

# import arranged alphabetically
import ConfigParser
import glob
import os
import shutil
import sys
import xml.dom.minidom

import dell_dup
from firmwaretools.trace_decorator import decorate, traceLog, getLog
import firmwaretools.plugins as plugins
import firmware_addon_dell.HelperXml as HelperXml
import firmware_addon_dell.extract_common as common
try:
    import firmware_extract as fte
    import firmware_extract.buildrpm as br
    import extract_cmd
except ImportError, e:
    # disable this plugin if firmware_extract not installed
    raise plugins.DisablePlugin

# required by the Firmware-Tools plugin API
__VERSION__ = dell_dup.__VERSION__
plugin_type = (plugins.TYPE_CORE,)
requires_api_version = "2.0"
# end: api reqs

DELL_VEN_ID = 0x1028
moduleLog = getLog()
conf = None

#####################
# Extract hooks
#####################

decorate(traceLog())
def extract_doCheck_hook(conduit, *args, **kargs):
    global conf
    conf = checkConf(conduit.getConf(), conduit.getBase().opts)
    extract_cmd.registerPlugin(genericLinuxDup, __VERSION__)

decorate(traceLog())
def extract_addSubOptions_hook(conduit, *args, **kargs):
    pass

true_vals = ("1", "true", "yes", "on")
decorate(traceLog())
def checkConf(conf, opts):
    return conf

#####################
# END Extract hooks
#####################


decorate(traceLog())
def getSystemDependencies(dom):
    ''' returns list of supported systems from package xml '''
    for systemId in HelperXml.iterNodeAttribute(dom, "systemID", "SoftwareComponent", "SupportedSystems", "Brand", "Model"):
        yield int(systemId, 16)

decorate(traceLog())
def getPciDevices(dom):
    ''' returns list of supported systems from package xml '''
#      <PCIInfo deviceID="0060" vendorID="1000" subDeviceID="1F0A" subVendorID="1028" />^M

    for pci in HelperXml.iterNodeElement(dom, "SoftwareComponent", "SupportedDevices", "Device", "PCIInfo"):
        ven = int(HelperXml.getNodeAttribute(pci, "vendorID"),16)
        dev = int(HelperXml.getNodeAttribute(pci, "deviceID"),16)
        subven = int(HelperXml.getNodeAttribute(pci, "subVendorID"),16)
        subdev = int(HelperXml.getNodeAttribute(pci, "subDeviceID"),16)
        yield (ven, dev, subven, subdev)

decorate(traceLog())
def minDupVersion(extractDir, maj, min, mtv):
    dmaj = dmin = dmtv = 0
    try:
        fd = open(os.path.join(extractDir, "build_variables.txt"),"r")
    except IOError:
        raise common.skip, "no build_variables.txt found"

    while not fd.closed:
        line = fd.readline()
        if line == "": fd.close()
        line = common.chomp(line)
        if line.startswith("BLD_RPL_MJV="): dmaj = int(line.replace("BLD_RPL_MJV=",""))
        if line.startswith("BLD_RPL_MNV="): dmin = int(line.replace("BLD_RPL_MNV=",""))
        if line.startswith("BLD_RPL_MTV="): dmtv = int(line.replace("BLD_RPL_MTV=",""))

    for di, i in ((dmaj, maj), (dmin, min), (dmtv, mtv)):
        if di < i:
            return False
        elif di > i:
            return True

    return True

decorate(traceLog())
def genericLinuxDup(statusObj, outputTopdir, logger, *args, **kargs):
    common.assertFileExt(statusObj.file, '.bin')
    common.copyToTmp(statusObj)
    common.doOnce( statusObj, common.dupExtract, statusObj.tmpfile, statusObj.tmpdir, logger )

    files = [ f.lower() for f in os.listdir(statusObj.tmpdir) ]

    if not 'package.xml' in files:
        raise common.skip, "not a dup, no package.xml present"

    dom = xml.dom.minidom.parse(os.path.join(statusObj.tmpdir, "package.xml"))

    if not minDupVersion(statusObj.tmpdir, 5, 0, 0):
        return False

    extracted = False
    dellVersion   = HelperXml.getNodeAttribute(dom, "dellVersion", "SoftwareComponent").lower()
    name   = HelperXml.getNodeText(dom, "SoftwareComponent", "Name", "Display")
    compId = HelperXml.getNodeAttribute(dom, "componentID", "SoftwareComponent", "SupportedDevices", "Device")
    emb    = HelperXml.getNodeAttribute(dom, "embedded",    "SoftwareComponent", "SupportedDevices", "Device")
    disp   = HelperXml.getNodeText(dom, "SoftwareComponent", "SupportedDevices", "Device", "Display")
    moduleLog.info("%s CompID(%s): %s  : %s" % (os.path.basename(statusObj.tmpfile), emb, compId, disp))
    for pciTuple in getPciDevices(dom):
        moduleLog.info("  Supports PCI: 0x%04x 0x%04x 0x%04x 0x%04x" % pciTuple)
        fwShortName = "pci_firmware_ven_0x%04x_dev_0x%04x_subven_0x%04x_subdev_0x%04x" % pciTuple
        fwFullName = ("%s_version_%s" % (fwShortName,dellVersion)).lower()

        extractPaths = []
        for sys in getSystemDependencies(dom):
            moduleLog.info("  Supports System: 0x%04x" % sys)
            extractPaths.append( os.path.join(outputTopdir, "dup", "system_ven_%s_dev_%s" % (DELL_VEN_ID, "0x%04x" % sys, fwFullName))
            
        if len(extractPaths) == 0:
            extractPaths.append(os.path.join(outputTopdir, "dup", fwFullName))
            
        for outdir in extractPaths:
            os.makedirs( outdir )
            common.dupExtract(statusObj.file, outdir, logger) 
            extracted = True

    if extracted:
        return extracted



