#!/bin/sh

if [ -n "$1" ]; then
	exec > $1 2>&1
fi

SCRIPT_DIR=$(cd $(dirname $0); pwd)
cat $SCRIPT_DIR/inventory.xml
