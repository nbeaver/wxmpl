#!/usr/bin/env python

# Name: setup.py
# Purpose: wxmpl distutils install program
# Author: Ken McIvor <mcivor@iit.edu>
#
# Copyright 2005 Illinois Institute of Technology
#
# See the file "LICENSE" for information on usage and redistribution
# of this file, and for a DISCLAIMER OF ALL WARRANTIES.


import distutils
from distutils.core import setup

setup(
    name = 'wxmpl',
    version = '1.2',
    maintainer = 'Ken McIvor',
    maintainer_email = 'mcivor@iit.edu',
    license = 'MIT X11/XFree86 style',
    description = 'A library for painlessly embedding matplotlib in wxPython',
    package_dir = {'': 'python'},
    py_modules = ['wxmpl']
)
