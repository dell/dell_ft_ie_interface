#                                               -*- Autoconf -*-
# vim:tw=0:et:ts=4:sw=4
# Process this file with autoconf to produce a configure script.

####################################
# change version here.
AC_INIT([dell-dup],[1.1.0])

temp_RELEASE_NAME=dell-dup
temp_RELEASE_MAJOR=1
temp_RELEASE_MINOR=1
temp_RELEASE_SUBLEVEL=0
temp_RELEASE_EXTRALEVEL=
####################################

AC_PREREQ(2.61)
AC_CONFIG_AUX_DIR([pkg])
AM_INIT_AUTOMAKE
AM_MAINTAINER_MODE

# Checks for programs.
AC_PROG_INSTALL

# automake macros
AM_PATH_PYTHON

# Checks for header files.

# Checks for typedefs, structures, and compiler characteristics.

# Checks for library functions.

# setup python compiler vars
PYINCLUDE=$(python -c 'from distutils.sysconfig import get_python_inc; print get_python_inc()')
PYCFLAGS=$(python -c 'from distutils.sysconfig import get_config_var; print get_config_var("CFLAGS")')
PYLDFLAGS=$(python -c 'from distutils.sysconfig import get_config_var; print get_config_var("LDFLAGS")')
PKGPYTHONARCHDIR=$(python -c 'from distutils.sysconfig import get_python_lib; print get_python_lib(1)')
AC_SUBST([ PYINCLUDE PYCFLAGS PYLDFLAGS PKGPYTHONARCHDIR ])


# update 'real' variables from the temp variable names.
# do this at the end of the file so that they A) are not overwitten by other
# autoconf stuff, and B) so that user can override on cmdline
for i in RELEASE_NAME RELEASE_MAJOR RELEASE_MINOR RELEASE_SUBLEVEL RELEASE_EXTRALEVEL
do
    varname=temp_$i
    if test -z "${!i}"; then
        eval $i=${!varname}; export $i
    fi
done

# Update the version information only immediately before a public release of your software. More frequent updates are unnecessary, and only guarantee that the current interface number gets larger faster.
# If the library source code has changed at all since the last update, then increment revision (c:r:a becomes c:r+1:a).
# If any interfaces have been added, removed, or changed since the last update, increment current, and set revision to 0.
# If any interfaces have been added since the last public release, then increment age.
# If any interfaces have been removed since the last public release, then set age to 0. 
LIBTOOL_CURRENT=$RELEASE_MAJOR
LIBTOOL_REVISION=$RELEASE_MINOR
LIBTOOL_AGE=0

if test -z "$RELEASE_RPM_EXTRALEVEL"; then
    if test -z "$RELEASE_EXTRALEVEL"; then
        RELEASE_RPM_EXTRALEVEL=%{nil}
    else
        RELEASE_RPM_EXTRALEVEL=$RELEASE_EXTRALEVEL
    fi
fi

PACKAGE_VERSION=[`echo ${RELEASE_MAJOR}.${RELEASE_MINOR}.${RELEASE_SUBLEVEL}${RELEASE_EXTRALEVEL}`]
PACKAGE_STRING=[`echo ${RELEASE_NAME} ${RELEASE_MAJOR}.${RELEASE_MINOR}.${RELEASE_SUBLEVEL}${RELEASE_EXTRALEVEL}`]
VERSION=$PACKAGE_VERSION

cat confdefs.h |
    grep -v 'define VERSION ' |
    grep -v 'define PACKAGE_VERSION ' |
    grep -v 'define PACKAGE_STRING '  > confdefs.new
mv confdefs.new confdefs.h
cat >>confdefs.h <<_ACEOF 
#define VERSION "$VERSION"
#define PACKAGE_VERSION "$PACKAGE_VERSION"
#define PACKAGE_STRING "$PACKAGE_STRING"
_ACEOF

AC_SUBST([RELEASE_NAME RELEASE_MAJOR RELEASE_MINOR RELEASE_SUBLEVEL RELEASE_EXTRALEVEL RELEASE_RPM_EXTRALEVEL])
AC_SUBST([ LIBTOOL_CURRENT  LIBTOOL_REVISION LIBTOOL_AGE  ])

# check if build dir == source dir.
AM_CONDITIONAL([BLDDIR_NE_SRCDIR], [test x$srcdir != x.])

# this is used by the autobuilder hook to determine the version we built
echo "PACKAGE_NAME='$PACKAGE_NAME'" > version
echo "PACKAGE_VERSION='$PACKAGE_VERSION'" >> version
echo "PACKAGE_STRING='$PACKAGE_STRING'" >> version

# firmware-tools oddity: package name cannot contain '-', so we have to fix it
pkgpythondir=\${pythondir}/dell_dup
pkgpyexecdir=\${pyexecdir}/dell_dup

# generate files and exit
AC_CONFIG_FILES([ Makefile pkg/${PACKAGE_NAME}.spec ])
AC_OUTPUT

