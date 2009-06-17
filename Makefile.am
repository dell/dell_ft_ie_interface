# vim:noexpandtab:autoindent:tabstop=8:shiftwidth=8:filetype=make:nocindent:tw=0:

include Makefile-std

pkgconfdir = $(sysconfdir)/firmware/firmware.d/
dist_pkgconf_DATA = pkg/dell_ft_ie_interface.conf

pkgdatadir = $(datadir)/firmware-tools/

pkgpython_PYTHON = \
	dell_ft_ie_interface/ie_interface.py	\
	dell_ft_ie_interface/generated/__init__.py	\
	dell_ft_ie_interface/svm.py

EXTRA_DIST += COPYING-GPL COPYING-OSL test

TESTS = test/testAll.py
nodist_check_SCRIPTS = test/testAll.py

pkglibexecdir=$(libexecdir)/dell_dup/
__VERSION__=$(VERSION)
PYTHONDIR=$(pythondir)
PKGLIBEXECDIR=$(pkglibexecdir)

REPLACE_VARS+= __VERSION__ PYTHONDIR PKGLIBEXECDIR
EXTRA_DIST += dell_ft_ie_interface/__init__.py
DISTCLEANFILES +=   dell_ft_ie_interface/generated/__init__.py
dell_ft_ie_interface/generated/__init__.py: dell_ft_ie_interface/__init__.py configure Makefile config.status
	mkdir -p $$(dirname $@) ||:
	cp $< $@
	for var in $(REPLACE_VARS)	;\
	do	\
		perl -p -i -e "s|^$$var\s*=.*|$$var=\"$${!var}\"|"  $@;\
	done
