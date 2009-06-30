#                                               -*- Autoconf -*-
# vim:tw=0:et:ts=4:sw=4
# Process this file with autoconf to produce a configure script.

##############################################################################
#  RELEASE VARIABLES
##############################################################################
#
# The following variables define the libsmbios release version.
#   This is the "marketing" version, or overall version of the project.
#   This doesnt have anything in relation to the ABI versions of individual
#   libraries, which are defined further below.
#
# To change the version, change the last "echo" statement at the end of each line.
# The version defined in this file can be overridden at compile time by setting the appropriate
# environment variable before running autogen.sh. For example:
#   RELEASE_MAJOR=9 RELEASE_MINOR=8 RELEASE_MICRO=7 ./autogen.sh
m4_define([release_major_version], [m4_esyscmd(test -n "$RELEASE_MAJOR" && echo -n $RELEASE_MAJOR || echo -n 1)])
m4_define([release_minor_version], [m4_esyscmd(test -n "$RELEASE_MINOR" && echo -n $RELEASE_MINOR || echo -n 0)])
m4_define([release_micro_version], [m4_esyscmd(test -n "$RELEASE_MICRO" && echo -n $RELEASE_MICRO || echo -n 3)])
# if you define any "extra" version info, include a leading dot (".")
m4_define([release_extra_version], [m4_esyscmd(test -n "$RELEASE_EXTRA" && echo -n $RELEASE_EXTRA || echo -n "")])

AC_INIT([dell_ft_ie_interface],
          [release_major_version().release_minor_version().release_micro_version()release_extra_version()])

####################################

AC_PREREQ(2.59)
AC_CONFIG_AUX_DIR([pkg])
AM_INIT_AUTOMAKE([1.9 subdir-objects tar-ustar dist-bzip2 no-define foreign])
AM_MAINTAINER_MODE

# Checks for programs.
AC_PROG_INSTALL

# automake macros
AM_PATH_PYTHON

# Checks for header files.

# Checks for typedefs, structures, and compiler characteristics.

# Checks for library functions.

RELEASE_MAJOR=release_major_version()
RELEASE_MINOR=release_minor_version()
RELEASE_MICRO=release_micro_version()
RELEASE_EXTRA=release_extra_version()
if test -z "$RELEASE_RPM_EXTRA"; then
    if test -z "$RELEASE_EXTRA"; then
        RELEASE_RPM_EXTRA=%{nil}
    else
        RELEASE_RPM_EXTRA=$RELEASE_EXTRA
    fi
fi


AC_SUBST([RELEASE_MAJOR])
AC_SUBST([RELEASE_MINOR])
AC_SUBST([RELEASE_MICRO])
AC_SUBST([RELEASE_EXTRA])
AC_SUBST([RELEASE_RPM_EXTRA])

# generate files and exit
AC_CONFIG_FILES([Makefile])
AC_CONFIG_FILES([pkg/dell_ft_ie_interface.spec])
AC_OUTPUT

