#!/usr/bin/python
# vim:expandtab:autoindent:tabstop=4:shiftwidth=4:filetype=python:textwidth=0:

  #############################################################################
  #
  # Copyright (c) 2005 Dell Computer Corporation
  # Dual Licenced under GNU GPL and OSL
  #
  #############################################################################
"""
"""

from __future__ import generators

# import arranged alphabetically
import os
import re
import shutil

import dell_ft_ie_interface
from firmwaretools.trace_decorator import decorate, traceLog, getLog
import firmwaretools.plugins as plugins
import firmware_addon_dell.HelperXml as HelperXml
import firmware_addon_dell.extract_common as common
try:
    import firmware_extract.buildrpm as br
except ImportError, e:
    # disable this plugin if firmware_extract not installed
    raise plugins.DisablePlugin

# required by the Firmware-Tools plugin API
__VERSION__ = dell_ft_ie_interface.__VERSION__
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
    br.specMapping["OfficialDUP"] = {"spec": conf.delldupspec, "ini_hook": buildrpm_ini_hook}

shortName = None

decorate(traceLog())
def buildrpm_addSubOptions_hook(conduit, *args, **kargs):
    global shortName
    shortName =common.ShortName(conduit.getOptParser())
    conduit.getOptParser().add_option(
        "--dup_spec", help="Path to the spec file to build official dups.",
        action="store", dest="delldupspec", default=None)

# this is called by the buildrpm_doCheck_hook and should ensure that all config
# options have reasonable default values and that config file values are
# properly overridden by cmdline options, where applicable.
decorate(traceLog())
def checkConf_buildrpm(conf, opts):
    shortName.check(conf, opts)
    if opts.delldupspec is not None:
        conf.delldupspec = os.path.realpath(os.path.expanduser(opts.delldupspec))
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
    shutil.copyfile(conf.license, os.path.join(pkgdir, os.path.basename(conf.license)))

    name = ini.get("package", "displayname")
    name = re.sub(r"[^A-Za-z0-9_]", "_", name)
    name = name.replace("____", "_")
    name = name.replace("___", "_")
    name = name.replace("__", "_")

    # set the rpm name
    rpmName = ini.get("package", "safe_name")
    rpmName = rpmName.replace("pci_firmware", name)
    rpmName = rpmName.replace("dell_dup", name)
    if ini.has_option("package", "limit_system_support"):
        system = ini.get("package", "limit_system_support")
        if system:
            id = system.split("_")
            shortname = shortName.getShortname(id[1], id[3])
            if shortname:
                rpmName = rpmName + "_for_" + shortname
            else:
                rpmName = rpmName + "_for_system_" + system
        ini.set("package", "system_dir", '/system_%s' % system)
        ini.set("package", "system_provides", '/system(%s)' % system)
    else:
        ini.set("package", "system_dir", "")
        ini.set("package", "system_provides", "")

    if not ini.has_option("package", "vendor_id"):
        ini.set("package", "vendor_id", "")

    ini.set("package", "rpm_name", rpmName)

#####################
# END buildrpm hooks
#####################

