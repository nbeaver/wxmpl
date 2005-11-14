#!/usr/bin/env python

# Name: setup.py
# Purpose: wxmpl distutils install program
# Author: Ken McIvor <mcivor@iit.edu>
#
# Copyright 2005 Illinois Institute of Technology
#
# See the file "LICENSE" for information on usage and redistribution
# of this file, and for a DISCLAIMER OF ALL WARRANTIES.


NAME    = 'wxmpl'
VERSION = '1.2.3'

AUTHOR       = 'Ken McIvor'
AUTHOR_EMAIL = 'mcivor@iit.edu'

LICENSE    = 'MIT'
DESCRPTION = 'A library for painlessly embedding matplotlib in wxPython'

PACKAGE_DIR = {'': 'lib'}
PY_MODULES  = ['wxmpl']
SCRIPTS     = ['plotit']

execfile('metasetup.py')
