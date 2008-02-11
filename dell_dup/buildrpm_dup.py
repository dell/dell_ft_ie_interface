#!/usr/bin/python
# vim:expandtab:autoindent:tabstop=4:shiftwidth=4:filetype=python:textwidth=0:

  #############################################################################
  #
  # Copyright (c) 2005 Dell Computer Corporation
  # Dual Licenced under GNU GPL and OSL
  #
  #############################################################################
"""extract_lsi:  not executable
"""

from __future__ import generators

# import arranged alphabetically
import ConfigParser
import glob
import os
import re
import shutil
import sys
import xml.dom.minidom

import dell_lsiflash
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
__VERSION__ = dell_lsiflash.__VERSION__
plugin_type = (plugins.TYPE_CORE,)
requires_api_version = "2.0"
# end: api reqs

DELL_VEN_ID = 0x1028
moduleLog = getLog()
conf = None

#####################
# buildrpm hooks
#####################

# this is called from doCheck in buildrpm_cmd and should register any spec files
# and hooks this module supports
decorate(traceLog())
def buildrpm_doCheck_hook(conduit, *args, **kargs):
    global conf
    conf = checkConf_buildrpm(conduit.getConf(), conduit.getBase().opts)
    br.specMapping["DUP"] = {"spec": conf.delldupspec, "ini_hook": buildrpm_ini_hook}

shortName = None

decorate(traceLog())
def buildrpm_addSubOptions_hook(conduit, *args, **kargs):
    global shortName
    shortName =common.ShortName(conduit.getOptParser())

# this is called by the buildrpm_doCheck_hook and should ensure that all config
# options have reasonable default values and that config file values are
# properly overridden by cmdline options, where applicable.
decorate(traceLog())
def checkConf_buildrpm(conf, opts):
    shortName.check(conf, opts)
    if getattr(conf, "delldupspec", None) is None:
        conf.delldupspec = None
    return conf

# this hook is called during the RPM build process. It should munge the ini
# as appropriate. The INI is used as source for substitutions in the spec
# file.
decorate(traceLog())
def buildrpm_ini_hook(ini, pkgdir=None):
    # we want the RPMs to be versioned with the Dell version, but the
    # comparision at inventory level still uses plain 'version' field.
    ini.set("package", "version", ini.get("package", "dell_version"))

    # get the name
# <SoftwareComponent ...
#  <SupportedDevices>^M
#      <Device componentID="3428" embedded="0">^M
#            <PCIInfo deviceID="1960" vendorID="1000" subDeviceID="0520" subVendorID="1028" />^M
#            <Display lang="en"><![CDATA[LSI2032]]></Display>^M
    name = ini.get("package", "type")
    pciid = eval(ini.get("package", "pciid"))
    dom = xml.dom.minidom.parse(os.path.join(pkgdir, "package.xml"))
    for node in HelperXml.iterNodeElement(dom, "SoftwareComponent", "SupportedDevices", "Device"):
        # check properly-formatted name
        if HelperXml.getNodeElement(node, ("PCIInfo", {"vendorID": "%04X" % pciid[0], "deviceID": "%04X" % pciid[1],  "subVendorID": "%04X" % pciid[2], "subDeviceID": "%04X" % pciid[3]})):
            name = HelperXml.getNodeText(node, ("Display", {"lang": "en"})).strip()

        # check if DUP team messed up
        if HelperXml.getNodeElement(node, ("PCIInfo", {"vendorID": "%X" % pciid[0], "deviceID": "%X" % pciid[1],  "subVendorID": "%X" % pciid[2], "subDeviceID": "%X" % pciid[3]})):
            name = HelperXml.getNodeText(node, ("Display", {"lang": "en"})).strip()

    name = re.sub(r"[^A-Za-z0-9_]", "_", name)
    name = name.replace("____", "_")
    name = name.replace("___", "_")
    name = name.replace("__", "_")

    # set the rpm name
    rpmName = ini.get("package", "safe_name").replace("pci_firmware", name)
    if ini.has_option("package", "limit_system_support"):
        sys = ini.get("package", "limit_system_support")
        if sys:
            id = sys.split("_")
            shortname = shortName.getShortname(id[1], id[3])
            if shortname:
                rpmName = rpmName + "_for_" + shortname
            else:
                rpmName = rpmName + "_for_system_" + sys
        ini.set("package", "limit_system_support", "%%define limit_system_support %s" % sys)

    ini.set("package", "rpm_name", rpmName)

#####################
# END buildrpm hooks
#####################

