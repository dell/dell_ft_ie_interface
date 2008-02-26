# vim:noexpandtab:autoindent:tabstop=8:shiftwidth=8:filetype=make:nocindent:tw=0:

include Makefile-std

pkgconfdir = $(sysconfdir)/firmware/firmware.d/
dist_pkgconf_DATA = pkg/dell-dup.conf

pkgdatadir = $(datadir)/firmware-tools/
dist_pkgdata_DATA = pkg/dup.spec.in  pkg/dell-inventory-collector.spec.in

pkgpython_PYTHON = \
	dell_dup/buildrpm_dup.py  dell_dup/dup.py  dell_dup/extract_dup.py  dell_dup/__init__.py   dell_dup/svm.py

REPLACE_VARS_ON_INSTALL= \
	$(pkgpythondir)/__init__.py

EXTRA_DIST += COPYING-GPL COPYING-OSL test

TESTS = test/testAll.py
nodist_check_SCRIPTS = test/testAll.py

