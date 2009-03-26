#!/bin/sh

echo "HEY, hello from $(basename $0)" >&2
echo " our args: $@" >&2

if [ -z "$FORCEFAIL" ]; then
cat <<-EOF
<SVMExecution lang="en">
<Device vendorID="1000" deviceID="1960" subDeviceID="0518" subVendorID="1028" bus="3" device="11" function="0" display="PowerEdge Expandable RAID Controller 4/DC">
<Application componentType="FRMW" version="352B" display="PowerEdge Expandable RAID Controller 4/DC Firmware"/>
</Device>
<Device vendorID="1028" deviceID="0013" subDeviceID="016D" subVendorID="1028" bus="2" device="14" function="0" display="PowerEdge Expandable RAID Controller 4e/Di">
<Application componentType="FRMW" version="5A2D" display="PowerEdge Expandable RAID Controller 4e/Di Firmware"/>
</Device>
<SPStatus result="true">
<Message id="0">Execution Success!</Message>
</SPStatus>
</SVMExecution>
EOF

else

cat <<-EOF
<SVMExecution lang="en">
<Device vendorID="1000" deviceID="1960" subDeviceID="0518" subVendorID="1028" bus="3" device="11" function="0" display="PowerEdge Expandable RAID Controller 4/DC">
<Application componentType="FRMW" version="352B" display="PowerEdge Expandable RAID Controller 4/DC Firmware"/>
</Device>
<Device vendorID="1028" deviceID="0013" subDeviceID="016D" subVendorID="1028" bus="2" device="14" function="0" display="PowerEdge Expandable RAID Controller 4e/Di">
<Application componentType="FRMW" version="5A2D" display="PowerEdge Expandable RAID Controller 4e/Di Firmware"/>
</Device>
<SPStatus result="false">
<Message id="0">flash failed. DOOM!</Message>
</SPStatus>
</SVMExecution>
EOF

fi
