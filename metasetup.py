################################################################################
# Name: metasetup.py
# Purpose: A scriptlet to simplify writing `setup.py' scripts
# Author: Ken McIvor <mcivor@iit.edu>
#
#
# Metasetup does several things that make writing setup scripts easier:
#   1. Automagically translates uppercased global variables into their
#      corresponding keyword arguments
#   2. Manages keyword argument compatability for you (e.g. keyword arguments
#      for setuptools are omitted when using distutils)
#   3. Detects setuptools and uses it instead of distutils
#   4. Adds support for "package_data" when using distutils with Python < 2.4
#
#
# Automatic Translation
#   Any global variable that is the uppercased version of a keyword argument
#   will be used as that keyword arguments value.
#
#   In other words,
#
#     AUTHOR = 'Ken McIvor'
#     AUTHOR_EMAIL = 'mcivor@iit.edu'
#
#   will be turned into
#
#     setup(..., author='Ken McIvor', author_email='mcivor@iit.edu', ...)
#
#
# Keyword Compatability
#   Metasetup omits keyword arguments that are incompatible with your current
#   build environment:
#    * Python >= 2.2.3: classifiers, download_url
#    * setuptools: zip_safe, install_requires, entry_points, extras_require,
#                  setup_requires, namespace_packages, test_suite,
#                  eager_resources
#
#   Arguments for py2app and py2exe are omitted unless you imported them
#   before running metasetup:
#    * py2app: app
#    * py2exe: console, windows, service, com_server, zipfile
#
#
# Building Extensions
#   Setuptools monkeypatches distutils, injecting its own Extension class into
#   distutils.core.  This makes things break if you import setuptools *after*
#   creating instances of distutils.Extension.  Here's the workaround:
#
#   try:
#       from setuptools import Extension
#   except ImportError:
#       from distutils.core import Extension
#
#
# Requiring Setuptools
#   If you're using setuptools-specific features to build your packages, you
#   can tell metasetup to refuse to run without setuptools:
#     * In `setup.py', set the global variable REQUIRE_SETUPTOOLS to True.
#     * Set the environment variable REQUIRE_SETUPTOOLS to y, yes, on, or true.
#       These values are case-insensitive.
#
#
# Disabling Setuptools
#   By default, metasetup favors setuptools over distutils.  However, you can
#   force it to use distutils instead:
#     * In `setup.py', set the global variable USE_SETUPTOOLS to False.
#     * Set the environment variable USE_SETUPTOOLS to n, no, off, or
#       false.  These values are case-insensitive.
#
#
# Using metasetup
#   Use execfile() to run metasetup at the end of `setup.py':
#       # Example setup.py that uses metasetup
#       NAME    = 'example'
#       VERSION = '1.0'
#       PACKAGE_DIR = {'': 'lib'}
#       PY_MODULES  = ['example.py']
#       execfile('metasetup.py')
#
################################################################################
#
# LICENSING AND COPYRIGHT
#
# The class `_package_data_build_py' is derived from Python 2.4's distutils
# package.  This portion of the software is licensed under the terms of the PSF
# License Agreement for Python 2.4.
#
#
# Copyright 2005 Illinois Institute of Technology
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL ILLINOIS INSTITUTE OF TECHNOLOGY BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Except as contained in this notice, the name of Illinois Institute
# of Technology shall not be used in advertising or otherwise to promote
# the sale, use or other dealings in this Software without prior written
# authorization from Illinois Institute of Technology.
#
################################################################################
#
# ChangeLog
#
# 11-11-2005  Ken McIvor <mcivor@iit.edu>
#  * Release: 1.0
################################################################################


import sys
import glob
import os.path
import distutils.command.build_py
import distutils.dist
import distutils.log
import distutils.util

__metasetup_version__ = '1.0'


#
# Functions and classes to setup the build environment appropriately
#


def _have_setuptools():
    """
    Checks for the presence of the setuptools package.

    Requiring Setuptools
      If you're using setuptools-specific features to build your packages, you
      can tell metasetup to refuse to run without setuptools:
        * In `setup.py', set the global variable REQUIRE_SETUPTOOLS to True.
        * Set the environment variable REQUIRE_SETUPTOOLS to y, yes, on, or
          true.  These values are case-insensitive.

    Disabling Setuptools
      By default, metasetup favors setuptools over distutils.  However, you can
      force it to use distutils instead:
        * In `setup.py', set the global variable USE_SETUPTOOLS to False.
        * Set the environment variable USE_SETUPTOOLS to n, no, off, or
          false.  These values are case-insensitive.
    """
    # if it's been set, return the cached value
    hst = getattr(_have_setuptools, 'HAVE_SETUPTOOLS', None)
    if hst is not None:
        return hst

    true_values  = 'y', 'yes',  'on',  'true'
    false_values = 'n', 'no',   'off', 'false'

    hst = False
    useVar    = globals().get('USE_SETUPTOOLS', True)
    useEnvVar = os.getenv('USE_SETUPTOOLS', 'true').lower()

    rst = False
    reqVar    = globals().get('REQUIRE_SETUPTOOLS', False)
    reqEnvVar = os.getenv('REQUIRE_SETUPTOOLS', 'false').lower()

    hst = False
    if not useVar or useEnvVar in false_values:
        if 'setuptools' in sys.modules:
            hst = True
            distutils.log.warn('metasetup: ignoring USE_SETUPTOOLS '
                '(setuptools is already loaded)')
            _have_setuptools.HAVE_SETUPTOOLS = hst
            return hst
        elif reqVar or reqEnvVar in true_values:
            distutils.log.error('metasetup: ignoring USE_SETUPTOOLS '
                '(REQUIRE_SETUPTOOLS is true)')

    try:
        import setuptools
    except ImportError:
        hst = False
    else:
        hst = True

    if not hst and (reqVar or reqEnvVar in true_values):
        distutils.log.error('%s: this script requires setuptools to run'
            ' (even to display help)' % os.path.basename(sys.argv[0]))
        sys.exit(1)

    _have_setuptools.HAVE_SETUPTOOLS = hst
    return hst


def _get_setup_function():
    """
    Retrieve the appropriate setup() function.  Setuptools is favored over
    distutils if it is installed.
    """
    if _have_setuptools():
        from setuptools import setup
    else:
        from distutils.core import setup
    return setup


class _package_data_build_py(distutils.command.build_py.build_py):
    """
    Adds support for package data files to distutils for Python < 2.4.

    The contents of this class are derived from Python 2.4's build_py class,
    located in the distutils.command.build_py module (revision $Id:
    install_lib.py,v 1.45 2004/12/02 20:14:16 lemburg Exp $).  Subsequently,
    this portion of the software is licensed under the terms of the PSF
    License Agreement for Python 2.4.

    NOTE: When using metasetup.py to invoke setup(), this command class must be
    installed by _install_package_data_support(), rather than using the
    CMDCLASS variable.
    """
    def initialize_options (self):
        distutils.command.build_py.build_py.initialize_options(self)
        self.package_data = None

    def finalize_options (self):
        distutils.command.build_py.build_py.finalize_options(self)
        self.package_data = self.distribution.package_data
        self.data_files = self.get_data_files()

    def run(self):
        if self.py_modules:
            self.build_modules()
        if self.packages:
            self.build_packages()
            self.build_package_data()

        self.byte_compile(self.get_outputs(include_bytecode=0))

    def get_data_files (self):
        """Generate list of '(package,src_dir,build_dir,filenames)' tuples"""
        data = []
        if not self.packages or self.package_data is None:
            return data
        for package in self.packages:
            # Locate package source directory
            src_dir = self.get_package_dir(package)

            # Compute package build directory
            build_dir = os.path.join(*([self.build_lib] + package.split('.')))

            # Length of path to strip from found files
            plen = len(src_dir)+1

            # Strip directory from globbed filenames
            filenames = [
                file[plen:] for file in self.find_data_files(package, src_dir)
                ]
            data.append((package, src_dir, build_dir, filenames))
        return data

    def find_data_files (self, package, src_dir):
        """Return filenames for package's data files in 'src_dir'"""
        globs = (self.package_data.get('', [])
                 + self.package_data.get(package, []))
        files = []
        for pattern in globs:
            platform_path = distutils.util.convert_path(pattern)
            # Each pattern has to be converted to a platform-specific path
            filelist = glob.glob(os.path.join(src_dir, platform_path))
            # Files that match more than one pattern are only added once
            files.extend([fn for fn in filelist if fn not in files])
        return files

    def build_package_data (self):
        """Copy data files into build directory"""
        for package, src_dir, build_dir, filenames in self.data_files:
            for filename in filenames:
                target = os.path.join(build_dir, filename)
                self.mkpath(os.path.dirname(target))
                self.copy_file(os.path.join(src_dir, filename), target,
                               preserve_mode=False)


def _install_package_data_support():
    """
    Installs support for the package_data argument if necessary.
    """
    global CMDCLASS

    try:
        CMDCLASS
    except NameError:
        CMDCLASS = None

    # check for setuptools or Python >= 2.4
    if _have_setuptools() or sys.version_info[0:2] >= (2,4):
        return

    # prevent distutils from complaining about the package_data keyword argument
    distutils.dist.Distribution.package_data = None

    # override the default build_py command
    if CMDCLASS is None:
        CMDCLASS = {}
    if not CMDCLASS.has_key('build_py'):
        CMDCLASS['build_py'] = _package_data_build_py


#
# Create the lists of variables that correspond to keyword arguments of setup()
#

# package metadata
_distutils_base_metadata_variables = [
    'NAME', 'VERSION', 'AUTHOR', 'AUTHOR_EMAIL', 'MAINTAINER',
    'MAINTAINER_EMAIL', 'URL', 'LICENSE', 'DESCRIPTION', 'LONG_DESCRIPTION',
    'KEYWORDS', 'PLATFORMS']

# package metadata added in Python 2.2.3
_distutils_py223_metadata_variables = ['CLASSIFIERS', 'DOWNLOAD_URL']

# packages, modules, and extensions
_distutils_python_variables = [
    'PACKAGES', 'PACKAGE_DIR', 'PY_MODULES', 'EXT_MODULES']

# build options
_distutils_extension_variables = [
    'LIBRARIES', 'HEADERS', 'INCLUDE_DIRS', 'EXTRA_PATH', 'OPTIONS']

# additional files to distribute
_distutils_resource_variables = ['SCRIPTS', 'PACKAGE_DATA', 'DATA_FILES']

# hooks to override the behavior of distutils
_distutils_command_variables = [
    'CMDCLASS', 'DISTCLASS', 'SCRIPT_NAME', 'SCRIPT_ARGS']

# setuptools options
_setuptools_variables = [
    'ZIP_SAFE', 'INSTALL_REQUIRES', 'ENTRY_POINTS', 'EXTRAS_REQUIRE',
    'SETUP_REQUIRES', 'NAMESPACE_PACKAGES', 'TEST_SUITE', 'EAGER_RESOURCES']

# py2app options
_py2app_variables = ['APP']

# py2exe options
_py2exe_variables = ['CONSOLE', 'WINDOWS', 'SERVICE', 'COM_SERVER', 'ZIPFILE']


#
# Setup the build envrionment and invoke setup()
#

if __name__ == '__main__':
    # Prevent people from running this script directly
    if os.path.basename(sys.argv[0]).startswith('metasetup'):
        sys.stderr.write('%s: please run `setup.py\' instead\n'
            % os.path.basename(sys.argv[0]))
        sys.exit(1)

    # if necessary, install support for the 'package_data' keyword argument
    _install_package_data_support()

    # omit the new metadata keyword arguments for Python < 2.2.3
    if sys.version >= '2.2.3':
        _distutils_metadata_variables = _distutils_base_metadata_variables
    else:
        _distutils_metadata_variables = (_distutils_base_metadata_variables
            + _distutils_py223_metadata_variables)

    # start building the list of supported keyword arguments
    _kwd_variables = (_distutils_metadata_variables
        + _distutils_python_variables   + _distutils_extension_variables
        + _distutils_resource_variables + _distutils_command_variables)

    # include the setuptools keyword arguments
    if _have_setuptools():
        _kwd_variables += _setuptools_variables

    # include the py2app keyword arguments
    if 'py2app' in sys.modules:
        _kwd_variables += _py2app_variables

    # include the py2exe keyword arguments
    if 'py2exe' in sys.modules:
        _kwd_variables += _py2exe_variables

    # build the arguments dictionary
    _kwd_arguments = {}
    for _kwd_name in _kwd_variables:
        _kwd_value = globals().get(_kwd_name)
        if _kwd_value is not None:
            _kwd_arguments[_kwd_name.lower()] = _kwd_value

    # fetch and invoke setup()
    _setup_function = _get_setup_function()
    _setup_function(**_kwd_arguments)
