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
import subprocess
import xml.dom.minidom

#import dell_dup
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
__VERSION__ = "1.0" #TODO: change this to dell_official_dup.__VERSION__ when we get that.
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
    extract_cmd.registerPlugin(genericPIE, __VERSION__)

decorate(traceLog())
def extract_addSubOptions_hook(conduit, *args, **kargs):
    conduit.getOptParser().add_option(
        "--device-type-xsl", help="Path to the DeviceType.xsl.",
        action="store", dest="device_type_xsl", default=None)

true_vals = ("1", "true", "yes", "on")
decorate(traceLog())
def checkConf(conf, opts):
    if opts.device_type_xsl is not None:
        conf.device_type_xsl = os.path.realpath(os.path.expanduser(opts.device_type_xsl))
    if getattr(conf, "device_type_xsl", None) is None:
        conf.helper_dat = ""  # <-- the default if no cfg or cmdline
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
def getPciDevices(dom=None, deviceNode=None):
    ''' returns list of supported systems from package xml '''
#      <PCIInfo deviceID="0060" vendorID="1000" subDeviceID="1F0A" subVendorID="1028" />^M

    if deviceNode is None:
        xmlPath = ("SoftwareComponent", "SupportedDevices", "Device", "PCIInfo")
    else:
        xmlPath = ("PCIInfo",)
        dom = deviceNode

    for pci in HelperXml.iterNodeElement(dom, *xmlPath):
        ven = int(HelperXml.getNodeAttribute(pci, "vendorID"),16)
        dev = int(HelperXml.getNodeAttribute(pci, "deviceID"),16)
        subven = int(HelperXml.getNodeAttribute(pci, "subVendorID"),16)
        subdev = int(HelperXml.getNodeAttribute(pci, "subDeviceID"),16)
        yield (ven, dev, subven, subdev)



decorate(traceLog())
def genericPIE(statusObj, outputTopdir, logger, *args, **kargs):
    common.assertFileExt(statusObj.file, '.pie')
    
    packageXml = os.path.join(os.path.dirname(statusObj.file), "package.xml")
    if not os.path.exists(packageXml):
        raise common.skip

    common.copyToTmp(statusObj)
    shutil.copyfile( packageXml, os.path.join(statusObj.tmpdir, "package.xml") )

    dom = xml.dom.minidom.parse(packageXml)
    dom.filename = packageXml

    subprocess.call( ["unzip", statusObj.tmpfile, "common/payload/*", "-d", statusObj.tmpdir], stdout=file("/dev/null", "w+"), stderr=subprocess.STDOUT )

    extracted = False
    for packageIni, outdir in getOutputDirs( dom, statusObj, outputTopdir, logger ):
        shutil.rmtree(outdir, ignore_errors=1)
        try:
            os.makedirs( os.path.dirname(outdir) )
        except OSError:
            pass
        shutil.copytree( os.path.join(statusObj.tmpdir, "common", "payload"), outdir )
        shutil.copyfile(conf.license, os.path.join(outdir, os.path.basename(conf.license)))

        fd = None
        try:
            fd = open( os.path.join(outdir, "package.ini"), "w+")
            packageIni.write( fd )
        finally:
            if fd is not None:
                fd.close()

        extracted = True

    return extracted

def getOutputDirs(dom, statusObj, outputTopdir, logger):
    deps = []
    for sysId in getSystemDependencies(dom):
        deps.append(sysId)

    dellVersion   = HelperXml.getNodeAttribute(dom, "dellVersion", "SoftwareComponent").lower()
    vendorVersion = HelperXml.getNodeAttribute(dom, "vendorVersion", "SoftwareComponent").lower()
    sysDepTemplate = "system_ven_0x%04x_dev_0x%04x"

    pobj = subprocess.Popen( ["xsltproc", conf.device_type_xsl, dom.filename], stdout=subprocess.PIPE )
    (stdout, stderr) = pobj.communicate(None)
    def validate(letter):
        if letter.isalnum():
            return letter 
        return "_"
    IEType = "".join([ validate(i) for i in stdout.strip()])
    
    for devNode in HelperXml.iterNodeElement(dom, "SoftwareComponent", "SupportedDevices", "Device"):
        packageIni = ConfigParser.ConfigParser()
        packageIni.add_section("package")
        componentId = int(HelperXml.getNodeAttribute(devNode, "componentID").strip(),10)
        displayName = HelperXml.getNodeText(devNode, ("Display", {"lang": "en"})).strip()
        depName = "dell_dup_componentid_%05d" % componentId
        fwFullName = "%s_version_%s" % (depName, dellVersion)

        logger.info("Got package for %s,  componentId: %s  dellVersion: %s  vendorVersion: %s" % (displayName, componentId, dellVersion, vendorVersion))
        logger.info("deps: %s" % repr(deps))

        common.setIni( packageIni, "package",
            name = depName,
            safe_name = depName,
            type      = "OfficialDUP",
            module    = "dell_dup_official.dup",
            ie_type   = IEType,
            displayname = displayName,
            dup_component_id = componentId,
            version        = vendorVersion,
            dell_version   = dellVersion,
            vendor_version = vendorVersion,
            )

        gotPciDev = False
        for pciTuple in getPciDevices(deviceNode=devNode):
            gotPciDev = True
            fwShortName = "pci_firmware_ven_0x%04x_dev_0x%04x_subven_0x%04x_subdev_0x%04x" % pciTuple
            fwFullName = ("%s_version_%s" % (fwShortName,dellVersion)).lower()
            depName     = "pci_firmware(ven_0x%04x_dev_0x%04x_subven_0x%04x_subdev_0x%04x)" % pciTuple

            logger.info("  PCI Device: %s" % repr(pciTuple))

            common.setIni( packageIni, "package",
                name      = depName,
                safe_name = fwShortName,
                pciId     = pciTuple,

                vendor_id =    "0x%04x" % pciTuple[0],
                device_id =    "0x%04x" % pciTuple[1],
                subvendor_id = "0x%04x" % pciTuple[2],
                subdevice_id = "0x%04x" % pciTuple[3],
                )

            for i,j in yieldIniAndPath(packageIni, outputTopdir, deps, fwFullName, sysDepTemplate, logger):
                yield i,j

        if not gotPciDev:
            logger.info("  NOT A PCI Device.")
            for i,j in yieldIniAndPath(packageIni, outputTopdir, deps, fwFullName, sysDepTemplate, logger):
                yield i,j


def yieldIniAndPath(packageIni, outputTopdir, deps, fwFullName, sysDepTemplate, logger):
    if deps:
        sysDepPath = os.path.join(outputTopdir, "dup", sysDepTemplate, fwFullName)
        for sysId in deps:
            logger.info("  Package for system: 0x%04x" % sysId)
            packageIni.set("package", "limit_system_support", "ven_0x%04x_dev_0x%04x" % (DELL_VEN_ID,sysId))
            yield packageIni, sysDepPath % (DELL_VEN_ID, sysId)
    else:
        logger.info("  Generic Package")
        yield packageIni, os.path.join(outputTopdir, "dup", fwFullName)




