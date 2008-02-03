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
# buildrpm hooks
#####################

# this is called from doCheck in buildrpm_cmd and should register any spec files
# and hooks this module supports
decorate(traceLog())
def buildrpm_doCheck_hook(conduit, *args, **kargs):
    global conf
    conf = checkConf_buildrpm(conduit.getConf(), conduit.getBase().opts)


decorate(traceLog())
def buildrpm_addSubOptions_hook(conduit, *args, **kargs):
    pass

# this is called by the buildrpm_doCheck_hook and should ensure that all config
# options have reasonable default values and that config file values are
# properly overridden by cmdline options, where applicable.
decorate(traceLog())
def checkConf_buildrpm(conf, opts):
    return conf

# this hook is called during the RPM build process. It should munge the ini
# as appropriate. The INI is used as source for substitutions in the spec
# file.
decorate(traceLog())
def buildrpm_ini_hook(ini):
    pass

#####################
# END buildrpm hooks
#####################

