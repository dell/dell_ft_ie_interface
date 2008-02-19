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
import sys

# local modules
import firmwaretools as ft
import firmwaretools.plugins as plugins
import firmwaretools.package as package
from firmwaretools.trace_decorator import decorate, traceLog, getLog

import svm
import firmware_addon_dell.extract_common as common
import firmware_addon_dell.HelperXml as xmlHelp
import firmware_addon_dell.biosHdr as biosHdr

plugin_type = (plugins.TYPE_INVENTORY)
requires_api_version = "2.0"

base=None
decorate(traceLog())
def config_hook(conduit, *args, **kargs):
    global base
    base = conduit.getBase()
    base.registerInventoryFunction("inventory_dup", InventoryFromDup)
    base.registerInventoryFunction("inventory_collector_inventory", InventoryFromInventoryCollector)
    base.registerBootstrapFunction("bootstrap_dup", BootstrapFromDup)
    base.registerBootstrapFunction("inventory_collector_bootstrap", BootstrapFromInventoryCollector)

# dummy package type for inventory collector
class INVCOL(package.RepositoryPackage):
    pass

class DUP(package.RepositoryPackage):
    def __init__(self, *args, **kargs):
        super(DUP, self).__init__(*args, **kargs)
        self.capabilities['can_downgrade'] = False
        self.capabilities['can_reflash'] = False

    def install(self):
        self.status = "in_progress"
        try:
            pie = getDupPIE(self)
            env = dict(os.environ)
            env["PATH"] = os.path.pathsep.join([os.environ.get('PATH',''), self.path])
            out = common.loggedCmd( pie["sExecutionCliBin"] + " " + pie["sExecutionCliArgs"], shell=True, returnOutput=True, cwd=self.path, timeout=int(pie["sExecutionCliTimeout"]), logger=getLog(), env=env)
        finally:
            self.status = "failed"
        self.status = "warm_reboot_needed"

def getPieConfig(pkg):
    for pieConfig in ("PIEConfig.sh", "framework/PIEConfig.sh"):
        if os.path.exists( os.path.join(pkg.path, pieConfig )):
            return os.path.join(pkg.path, pieConfig)
    raise IOError, "PIEConfig.sh not found in package: %s" % pkg.path

vars = ["sInventoryCliBin", "sInventoryCliArgs", "sInventoryCliTimeout",
        "sExecutionCliBin", "sExecutionCliArgs", "sExecutionCliTimeout", "sExecutionCliForceArgs" ]

def getDupPIE(pkg):
    fd = open( getPieConfig(pkg), "r" )
    pie = {}
    while True:
        line = fd.readline()
        if line == "": break
        if line[-1:] == "\n": line = line[:-1]
        for i in vars:
            if line.startswith( i + "=" ):
                pie[i] = line.replace( i + "=", "" )
                pie[i] = pie[i].replace('"', '')

    return pie

DELL_VEN_ID = 0x1028

decorate(traceLog())
def BootstrapFromInventoryCollector(base=None, cb=None, *args, **kargs):
    for pkg in InventoryFromInventoryCollector(base=base, cb=cb, *args, **kargs):
        yield pkg
        sysid = xmlHelp.getNodeAttribute(pkg.dom, "systemID", "SVMInventory", "System")
        if sysid:
            sysid = int(sysid,16)
            pkg.name = "%s/%s" % (pkg.name, "system(ven_0x1028_dev_0x%04x)" % sysid)
            yield pkg

decorate(traceLog())
def InventoryFromInventoryCollector(base=None, cb=None, *args, **kargs):
    thisSys = "ven_0x%04x_dev_0x%04x" % (DELL_VEN_ID,biosHdr.getSystemId())
    for pkg in base.repo.iterLatestPackages():
        if not isinstance(pkg, INVCOL):
            getLog(prefix="verbose.").info("Not a Inventory Collector.")
            continue

        try:
            ft.callCB(cb, who="inventory_collector_inventory", what="running_inventory", details="This may take several minutes...")
            env = dict(os.environ)
            env["LD_LIBRARY_PATH"] = os.path.pathsep.join([os.environ.get('LD_LIBRARY_PATH',''), pkg.path])
            out = common.loggedCmd( os.path.join(pkg.path,"invcol"), returnOutput=True, env=env, cwd=pkg.path, timeout=1200, logger=getLog())

            for pkg in svm.genPackagesFromSvmXml(out):
                yield pkg
        except IOError:
            pass


decorate(traceLog())
def InventoryFromDup(base=None, cb=None, *args, **kargs):
    bootstrap = [i.name for i in base.yieldBootstrap()]
    thisSys = "ven_0x%04x_dev_0x%04x" % (DELL_VEN_ID,biosHdr.getSystemId())
    for pkg in base.repo.iterLatestPackages():
        if not isinstance(pkg, DUP):
            getLog(prefix="verbose.").info("Not a DUP.")
            continue

        if not pkg.name in bootstrap:
            getLog(prefix="verbose.").info("Not in bootstrap: %s" % repr(pkg.name))
            continue

        if pkg.conf.has_option("package", "limit_system_support"):
            sys = pkg.conf.get("package", "limit_system_support")
            if sys != thisSys:
                getLog(prefix="verbose.").info("System-specific pkg doesnt match this system: %s != %s" % (thisSys, sys))
                continue

        try:
            pie = getDupPIE(pkg)
            ft.callCB(cb, who="dup_inventory", what="running_inventory", details="cmd %s" % pie["sInventoryCliBin"])

            env = dict(os.environ)
            env["PATH"] = os.path.pathsep.join([os.environ.get('PATH',''), pkg.path])
            out = common.loggedCmd( pie["sInventoryCliBin"] + " " + pie["sInventoryCliArgs"], shell=True, returnOutput=True, cwd=pkg.path, timeout=int(pie["sInventoryCliTimeout"]), logger=getLog(), env=env)

            for pkg in svm.genPackagesFromSvmXml(out):
                yield pkg
        except IOError:
            pass




decorate(traceLog())
def BootstrapFromDup(base=None, cb=None, *args, **kargs):
    thisSys = "ven_0x%04x_dev_0x%04x" % (DELL_VEN_ID,biosHdr.getSystemId())
    for pkg in base.repo.iterLatestPackages():
        if not isinstance(pkg, DUP):
            getLog(prefix="verbose.").info("Not a DUP.")
            continue

        if pkg.conf.has_option("package", "limit_system_support"):
            sys = pkg.conf.get("package", "limit_system_support")
            if sys != thisSys:
                getLog(prefix="verbose.").info("System-specific pkg doesnt match this system: %s != %s" % (thisSys, sys))
                continue

        try:
            pie = getDupPIE(pkg)
            ft.callCB(cb, who="dup_inventory", what="running_inventory", details="cmd %s" % pie["sInventoryCliBin"])

            env = dict(os.environ)
            env["PATH"] = os.path.pathsep.join([os.environ.get('PATH',''), pkg.path])
            out = common.loggedCmd( pie["sInventoryCliBin"] + " " + pie["sInventoryCliArgs"], shell=True, returnOutput=True, cwd=pkg.path, timeout=int(pie["sInventoryCliTimeout"]), logger=getLog(), env=env)

            for pkg in svm.genPackagesFromSvmXml(out):
                yield pkg
        except IOError:
            pass

