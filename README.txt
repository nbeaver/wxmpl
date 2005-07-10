WxMpl - Painless matplolib embedding for wxPython
-------------------------------------------------

The `wxmpl' module provides an matplotlib `FigureCanvas' with user-interaction
features like point-under-cursor and zooming in on a selected area.
Support for creating stripcharts, plots that update as their data changes, is
also included.

Documentation of the module itself is available in the`reference/'
subdirectory.  An introduction to using matplotlib with WxMpl is available in
the `tutorial/' subdirectory.  Scripts demonstrating some of matplotlib's
examples with WxMpl and plotting stripcharts data are in the `demos/'
subdirectory.


REQUIREMENTS
------------

* Python 2.3.  Version 2.4 has not been tested.
    http://www.python.org

* wxPython 2.4.2.4, a later 2.5 release, or 2.6.0.  Early 2.5 releases are
  incompatible due to API changes that were later abandoned.
    http://www.wxpython.org

* matplotlib 0.72 or above.
    http://matplotlib.sourceforge.net


PLATFORMS
---------

WxMpl has been tested under Debian Stable, Debian Testing, Debian Unstable, and
Mac OS 10.3.9.


INSTALLATION
------------

The Python Distutils system provides packaging, compilation, and installation
for wxmpl.

To install, execute the following command as superuser:
  # python setup.py install [OPTIONS]

For more information about installation options, execute the following
command:
  > python setup.py install --help

For information about other Distutils commands, execute the following command:
  > python setup.py install --help-commands


AVAILABILITY
------------

There is no website for WxMpl yet, so your best bet is to bug Ken.

WxMpl's subversion repository is http://svn.csrri.iit.edu/mr-software/wxmpl/


AUTHOR
------

WxMpl was written by Ken McIvor <mcivor@iit.edu>


COPYRIGHT & LICENSE
-------------------

  Copyright 2005 Illinois Institute of Technology

  Permission is hereby granted, free of charge, to any person obtaining
  a copy of this software and associated documentation files (the
  "Software"), to deal in the Software without restriction, including
  without limitation the rights to use, copy, modify, merge, publish,
  distribute, sublicense, and/or sell copies of the Software, and to
  permit persons to whom the Software is furnished to do so, subject to
  the following conditions:

  The above copyright notice and this permission notice shall be
  included in all copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
  IN NO EVENT SHALL ILLINOIS INSTITUTE OF TECHNOLOGY BE LIABLE FOR ANY
  CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
  TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

  Except as contained in this notice, the name of Illinois Institute
  of Technology shall not be used in advertising or otherwise to promote
  the sale, use or other dealings in this Software without prior written
  authorization from Illinois Institute of Technology.
