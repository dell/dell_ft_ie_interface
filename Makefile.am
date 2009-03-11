# vim:noexpandtab:autoindent:tabstop=8:shiftwidth=8:filetype=make:nocindent:tw=0:

include Makefile-std

pkgconfdir = $(sysconfdir)/firmware/firmware.d/
dist_pkgconf_DATA = pkg/dell_ft_ie_interface.conf

pkgdatadir = $(datadir)/firmware-tools/
dist_pkgdata_DATA = pkg/update-payload.spec.in

pkgpython_PYTHON = \
	dell_ft_ie_interface/buildrpm_plugin.py	\
	dell_ft_ie_interface/dup.py	\
	dell_ft_ie_interface/create_payload.py	\
	dell_ft_ie_interface/__init__.py	\
	dell_ft_ie_interface/svm.py

REPLACE_VARS_ON_INSTALL= \
	$(pkgpythondir)/__init__.py

EXTRA_DIST += COPYING-GPL COPYING-OSL test

TESTS = test/testAll.py
nodist_check_SCRIPTS = test/testAll.py

