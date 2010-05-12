# vim:tw=0:expandtab:autoindent:tabstop=4:shiftwidth=4:filetype=python:

  #############################################################################
  #
  # Copyright (c) 2005 Dell Computer Corporation
  # Dual Licenced under GNU GPL and OSL
  #
  #############################################################################
"""module

some docs here eventually.
"""

# import arranged alphabetically
import firmware_addon_dell.HelperXml as xmlHelp
import firmwaretools.package as package
import xml.dom.minidom

from firmwaretools.trace_decorator import decorate, traceLog, getLog
import logging
moduleLog = getLog()
moduleVerboseLog = getLog(prefix="verbose.")

# sample XML:
# <?xml version="1.0" encoding="UTF-8"?>
# <SVMInventory lang="en">
#   <Device vendorID="1028" deviceID="0015" subDeviceID="1F03" subVendorID="1028" bus="2" device="14" function="0" display="Dell PERC 5/i Integrated Controller 1">
#       <Application componentType="FRMW" version="5.0.1-0030" display="Dell PERC 5/i Integrated Controller 1 Firmware"/>
#   </Device>
#</SVMInventory>
#
# loathe SVM team. What kind of idiots specify hex values in a dtd without leading 0x? Are bus/device/function also hex? Who knows?

# more sample XML:

#<?xml version="1.0" encoding="UTF-8"?>
#<SVMInventory lang="en">
#  <Device vendorID="1000" deviceID="0060" subDeviceID="1F0C" subVendorID="1028" bus="5" device="0" function="0" display="PERC 6/i Integrated Controller 0" impactsTPMmeasurements="TRUE">
#    <Application componentType="FRMW" version="6.0.1-0080" display="PERC 6/i Integrated Controller 0 Firmware"/>
#  </Device>
#  <Device componentID="13313" enum="CtrlId 0 DeviceId 0" display="ST973402SS">
#    <Application componentType="FRMW" version="S206" display="ST973402SS Firmware"/>
#  </Device>
#  <Device componentID="00000" enum="CtrlId 0 DeviceId 1" display="ST936701SS">
#     <Application componentType="FRMW" version="S103" display="ST936701SS Firmware"/>
#  </Device>
#  <Device componentID="11204" enum="CtrlId 0 DeviceId 20 Backplane" display="SAS/SATA Backplane 0:0 Backplane">
#    <Application componentType="FRMW" version="1.05" display="SAS/SATA Backplane 0:0 Backplane Firmware"/>
#  </Device>
# </SVMInventory>

# sample XML from inventory collector:
#
# <?xml version="1.0" encoding="UTF-8"?>
#<SVMInventory lang="en" schemaVersion="1.0" timeStamp="2008-02-19T19:14:48">
#        <OperatingSystem osCode="LIN" osVendor="Redhat" osArch="x86" majorVersion="redhat-release-5Server" minorVersion="2.6.18-8.5patches" usingTPMmeasurements="FALSE"/>
#        <System systemID="0221" TPMmeasurementsOn="FALSE"/><Device componentID="159" display="BIOS" impactsTPMmeasurements="TRUE"><Application componentType="BIOS" version="0.2.15" display="BIOS"/></Device>
#        <Device vendorID="1000" deviceID="0030" subDeviceID="50c0" subVendorID="1000" bus="35" device="8" function="0" display="Ultra320 SCSI PCIe Host Adapter" impactsTPMmeasurements="TRUE"><Application componentType="FRMW" version="1.03.39.00.5.10.08.00.12" display="Ultra320 SCSI PCIe Host Adapter"/></Device>
#        <Device componentID="5814" display="Baseboard Management Controller">
#      <Application componentType="FRMW" version="1.44" display="BMC"/>
#   </Device>
#        <Device vendorID="1000" deviceID="0060" subDeviceID="1F0C" subVendorID="1028" bus="5" device="0" function="0" display="PERC 6/i Integrated Controller 0" impactsTPMmeasurements="TRUE"><Application componentType="FRMW" version="6.0.1-0080" display="PERC 6/i Integrated Controller 0 Firmware"/></Device>
#        <Device componentID="13313" enum="CtrlId 0 DeviceId 0" display="ST973402SS"><Application componentType="FRMW" version="S206" display="ST973402SS Firmware"/></Device>
#        <Device componentID="00000" enum="CtrlId 0 DeviceId 1" display="ST936701SS"><Application componentType="FRMW" version="S103" display="ST936701SS Firmware"/></Device>
#        <Device componentID="11204" enum="CtrlId 0 DeviceId 20 Backplane" display="SAS/SATA Backplane 0:0 Backplane"><Application componentType="FRMW" version="1.05" display="SAS/SATA Backplane 0:0 Backplane Firmware"/></Device>
#        </SVMInventory>


pciShortFirmStr = "pci_firmware(ven_0x%04x_dev_0x%04x)"
pciFullFirmStr = "pci_firmware(ven_0x%04x_dev_0x%04x_subven_0x%04x_subdev_0x%04x)"

def genPackagesFromSvmXml(xmlstr, path):
    otherAttrs={}
    try:
        dom = xml.dom.minidom.parseString(xmlstr)
    except (xml.parsers.expat.ExpatError,), e:
        moduleLog.info("Invalid XML from module %s", path)
        return

    otherAttrs["dom"] = dom
    for nodeElem in xmlHelp.iterNodeElement( dom, "SVMInventory", "Device" ):
        otherAttrs["xmlNode"] = nodeElem
        type = package.Device
        componentId = xmlHelp.getNodeAttribute(nodeElem, "componentID")
        if componentId:
            otherAttrs["dup_component_id"] = int(componentId,10)
            name = "dell_dup_componentid_%05d" % int(componentId,10)

        displayname =  xmlHelp.getNodeAttribute(nodeElem, "display", "Application")
        if not displayname:
            displayname =  xmlHelp.getNodeAttribute(nodeElem, "display")
        if not displayname:
            displayname =  "Unknown Dell Update Package"

        venId = xmlHelp.getNodeAttribute(nodeElem, "vendorID")
        devId = xmlHelp.getNodeAttribute(nodeElem, "deviceID")
        subdevId = xmlHelp.getNodeAttribute(nodeElem, "subDeviceID")
        subvenId = xmlHelp.getNodeAttribute(nodeElem, "subVendorID")

        bus = xmlHelp.getNodeAttribute(nodeElem, "bus")
        device = xmlHelp.getNodeAttribute(nodeElem, "device")
        function = xmlHelp.getNodeAttribute(nodeElem, "function")


        otherAttrs["version"] = "unknown"
        ver = xmlHelp.getNodeAttribute(nodeElem, "version", "Application")
        if ver:
            otherAttrs["version"] = ver.lower()

        shortname = None
        if venId and devId:
            venId = int(venId, 16)
            devId = int(devId, 16)
            shortname = name = pciShortFirmStr % (venId, devId)
            if subvenId and subdevId:
                subdevId = int(subdevId,16)
                subvenId = int(subvenId,16)
                name = pciFullFirmStr % (venId, devId, subvenId, subdevId)
            else:
                shortname = None

        if bus and device and function:
            bus = int(bus, 16)
            device = int(device, 16)
            function = int(function, 16)
            otherAttrs["pciDbdf"] = (0, bus, device, function)
            type = package.PciDevice

        if not name:
            continue

        otherAttrs["compareStrategy"] = package.defaultCompareStrategy

#        yield type(
#            name=name,
#            displayname=displayname,
#            **otherAttrs
#            )
        if shortname:
            yield type (
            name = name,
            shortname=shortname,
            displayname=displayname,
            **otherAttrs
            )
        else:
       	    yield type (
            name = name,
            displayname=displayname,
            **otherAttrs
        );
              
