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
# Extract hooks
#####################

decorate(traceLog())
def extract_doCheck_hook(conduit, *args, **kargs):
    global conf
    conf = checkConf(conduit.getConf(), conduit.getBase().opts)
    extract_cmd.registerPlugin(dupFromLinuxDup, __VERSION__)

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
def getSystemDependencies(packageXml):
    ''' returns list of supported systems from package xml '''
    dom = xml.dom.minidom.parse(packageXml)
    for systemId in HelperXml.iterNodeAttribute(dom, "systemID", "SoftwareComponent", "SupportedSystems", "Brand", "Model"):
        yield int(systemId, 16)


decorate(traceLog())
def dupFromLinuxDup(statusObj, outputTopdir, logger, *args, **kargs):
    common.assertFileExt( statusObj.file, '.bin')
    common.copyToTmp(statusObj)
    common.doOnce( statusObj, common.dupExtract, statusObj.tmpfile, statusObj.tmpdir, logger )

    files = [ f.lower() for f in os.listdir(statusObj.tmpdir) ]

    if not 'package.xml' in files:
        raise common.skip, "not a dup, no package.xml present"

    
