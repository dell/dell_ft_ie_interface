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
try:
    import firmware_addon_dell.extract_common as common
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
def getDupVersion(extractDir):
    dmaj = dmin = dmtv = 0
    try:
        fd = open(os.path.join(extractDir, "build_variables.txt"),"r")
        while not fd.closed:
            line = fd.readline()
            if line == "": fd.close()
            line = common.chomp(line)
            if line.startswith("BLD_RPL_MJV="): dmaj = int(line.replace("BLD_RPL_MJV=",""))
            if line.startswith("BLD_RPL_MNV="): dmin = int(line.replace("BLD_RPL_MNV=",""))
            if line.startswith("BLD_RPL_MTV="): dmtv = int(line.replace("BLD_RPL_MTV=",""))
    except IOError:
        pass

    return dmaj, dmin, dmtv

def compareVersions(i, j):
    for i, j in zip(i,j):
        if i < j:
            return -1
        elif i > j:
            return 1
    return 0

decorate(traceLog())
def genericLinuxDup(statusObj, outputTopdir, logger, *args, **kargs):
    common.assertFileExt(statusObj.file, '.bin')
    common.copyToTmp(statusObj)
    common.doOnce( statusObj, common.dupExtract, statusObj.tmpfile, statusObj.tmpdir, logger )

    files = [ f.lower() for f in os.listdir(statusObj.tmpdir) ]

    if not 'package.xml' in files:
        raise common.skip, "not a dup, no package.xml present"

    if not os.path.exists(os.path.join(statusObj.tmpdir, "PIEConfig.sh")) and not os.path.exists(os.path.join(statusObj.tmpdir, "framework", "PIEConfig.sh")):
        raise common.skip, "No PIEConfig.sh, cannot use with this DUP framework."

    dom = xml.dom.minidom.parse(os.path.join(statusObj.tmpdir, "package.xml"))

    #logDupInfo(dom, statusObj, logger)

    extracted = False
    for packageIni, outdir in getOutputDirs( dom, statusObj, outputTopdir, logger ):
        thisVer = getDupVersion(statusObj.tmpdir)
        existVer = getDupVersion(outdir)
        # skip if thisVer ties already existing or is older AND existingver valid
        if existVer != (0,0,0) and compareVersions(existVer, thisVer) >= 0:
            continue

        shutil.rmtree(outdir, ignore_errors=1)
        os.makedirs( outdir )
        common.dupExtract(statusObj.file, outdir, logger) 

        fd = None
        try:
            fd = open( os.path.join(outdir, "package.ini"), "w+")
            packageIni.write( fd )
        finally:
            if fd is not None:
                fd.close()

        extracted = True

    return extracted

def getComponentId(dom):
    return int(HelperXml.getNodeAttribute(dom, "componentID", "SoftwareComponent", "SupportedDevices", "Device"))

def getDellVersion(dom):
    return HelperXml.getNodeAttribute(dom, "dellVersion", "SoftwareComponent").lower()

def logDupInfo(dom, statusObj, logger):
    dellVersion   = getDellVersion(dom)
    compId = getComponentId(dom)
    emb    = HelperXml.getNodeAttribute(dom, "embedded",    "SoftwareComponent", "SupportedDevices", "Device")
    disp   = HelperXml.getNodeText(dom, "SoftwareComponent", "Name", "Display")
    hasPci = False
    for pciTuple in getPciDevices(dom):
        hasPci = True
        break
    hasSys = False
    for sys in getSystemDependencies(dom):
        hasSys = True
        break
    moduleLog.info("ID %05d (%s): %s" % (compId, emb, disp))
    for pciTuple in getPciDevices(dom):
        moduleLog.info("\tSupports PCI: 0x%04x 0x%04x 0x%04x 0x%04x" % pciTuple)
    for sys in getSystemDependencies(dom):
        moduleLog.info("\tSupports System: 0x%04x" % sys)

def getOutputDirs(dom, statusObj, outputTopdir, logger):
    for output in getOutputDirsForPciDev(dom, statusObj, outputTopdir, logger):
        yield output

def getOutputDirsForPciDev(dom, statusObj, outputTopdir, logger):
    deps = []
    for sysId in getSystemDependencies(dom):
        deps.append(sysId)

    dellVersion   = getDellVersion(dom)
    vendorVersion = HelperXml.getNodeAttribute(dom, "vendorVersion", "SoftwareComponent").lower()
    sysDepTemplate = "system_ven_0x%04x_dev_0x%04x"
    fwFullName = ""
    for pciTuple in getPciDevices(dom):
        fwShortName = "pci_firmware_ven_0x%04x_dev_0x%04x_subven_0x%04x_subdev_0x%04x" % pciTuple
        fwFullName = ("%s_version_%s" % (fwShortName,dellVersion)).lower()
        depName     = "pci_firmware(ven_0x%04x_dev_0x%04x_subven_0x%04x_subdev_0x%04x)" % pciTuple

        packageIni = ConfigParser.ConfigParser()
        packageIni.add_section("package")
        common.setIni( packageIni, "package",
            type      = "DUP",
            name      = depName,
            safe_name = fwShortName,
            pciId     = pciTuple,
            module    = "dell_dup.dup",

            vendor_id =    "0x%04x" % pciTuple[0],
            device_id =    "0x%04x" % pciTuple[1],
            subvendor_id = "0x%04x" % pciTuple[2],
            subdevice_id = "0x%04x" % pciTuple[3],

            version        = vendorVersion,
            dell_version   = dellVersion,
            vendor_version = vendorVersion,
            )

        if deps:
            sysDepPath = os.path.join(outputTopdir, "dup", sysDepTemplate, fwFullName)
            for sysId in deps:
                packageIni.set("package", "limit_system_support", "ven_0x%04x_dev_0x%04x" % (DELL_VEN_ID,sysId))
                yield packageIni, sysDepPath % (DELL_VEN_ID, sysId)
        else:
            yield packageIni, os.path.join(outputTopdir, "dup", fwFullName)



supportedPciDevs = [ 1369, 1375, 2608, 3428, 5646, 6315, 6395, 6396, 9181, 9182, 9183, 9294, 9623, 9840, 10269, 12436, 13119, 13514, 13856, 13910 ]

# list of all component ids and name
DATA = """
 ID 00159 (1): Dell Server System BIOS
 ID 00160 (1): Dell ESM Firmware
#ID 01369 (0): LSI Logic PERC3/DCL, PERC3/DC, PERC3/QC, PERC3/SC
#ID 01375 (1): Adaptec PERC3/Di
 ID 02517 (0): Dell PowerVault 220S/221S SES Firmware
#ID 02608 (1): LSI Logic PERC 4/Di
#ID 03428 (0): LSI Logic PERC 4/SC, PERC 4/DC
 ID 03967 (1): Dell Backplane Firmware
 ID 04332 (1): Dell Remote Access Controller - ERA/O
 ID 04334 (1): Dell Remote Access Controller - ERA and DRAC III/XT
#ID 05646 (0): Adaptec CERC SATA1.5/6ch
 ID 05814 (1): Dell BMC Firmware
 ID 05974 (0): Dell Remote Access Controller - DRAC 4/I, Remote Access Controller - DRAC 4/P
#ID 06315 (0): LSI Logic PERC 4e/DC
#ID 06395 (1): LSI Logic Perc 4e/Di
#ID 06396 (1): LSI Logic PERC 4e/Si
 ID 08529 (0): Dell MD1000 Controller Card Firmware
 ID 08735 (0): Dell Remote Access Controller - DRAC 5
#ID 09181 (0): Dell PERC 5/E Adapter
#ID 09182 (0): Dell PERC 5/i Integrated
#ID 09183 (0): Dell PERC 5/i Adapter
#ID 09294 (0): Dell SAS 5/i Integrated
#ID 09623 (0): Dell SAS 5/iR Integrated
#ID 09840 (0): Dell SAS 5/E Adapter
#ID 10269 (0): Dell SAS 5/iR Adapter
 ID 11204 (0): Dell SAS Backplane Firmware
#ID 12436 (0): Dell PERC 6/E Adapter
#ID 13119 (0): Dell SAS 6/iR Adapter
 ID 13375 (0): Fujitsu AL10LX, 3.5", 15K, SAS, 73GB, DU, AL10LX, 3.5", 15K, SAS, 146GB, DU, AL10LX, 3.5", 15K, SAS, 300GB, DU
 ID 13380 (0): Hitachi Viper B, 3.5", 15K, SAS, 73GB, DU, Viper B, 3.5", 15K, SAS, 146GB, DU, Viper B, 3.5", 15K, SAS, 300GB, DU
 ID 13385 (0): Fujitsu AL10SE, 2.5", 10K, SAS, 73GB, DU, AL10SE, 2.5", 10K, SAS, 146GB, DU
#ID 13514 (0): Dell PERC 6/i Integrated
#ID 13856 (0): Dell SAS 6/iR Integrated
#ID 13910 (0): LSI Logic LSI2032
 ID 14610 (0): Hitachi Cobra B, 10K, SAS, 2.5"FF, 73GB, DU, Cobra B, 10K, SAS, 2.5"FF, 146GB, DU
 ID 14612 (0): Fujitsu AL10SX, 2.5", 15K, SAS, 73GB, DU, AL10SX, 2.5", 15K, SAS, 36GB, DU
 ID 15051 (0): Dell iDRAC v1.0
 ID 16109 (0): Seagate HD,146G,SAS,3,10K,2.5,SGT2,FIRE,DU, HD,73G,SAS,3,10K,2.5,SGT2,FIRE,DU
 ID 16111 (0): Seagate Timberland,15K5,SAS3.0,3.5",146GB,SGT3,DU, Timberland,15K5,SAS3.0,3.5",300GB,SGT3,DU, Timberland,15K5,SAS3.0,3.5",73GB,SGT3,DU
 ID 16114 (0): Seagate Timberland T10,10K,SAS3.0,3.5",146GB,SGT3,DU, Timberland T10,10K,SAS3.0,3.5",300GB,SGT3,DU, Timberland T10,10K,SAS3.0,3.5",73GB,SGT3,DU
 ID 16117 (0): Seagate Timberland NS,10K,SAS3.5",400GB,DU
"""

