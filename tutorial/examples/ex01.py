# Name: ex01.py
# Purpose: WxMpl Example 1: Boilerplate
# Author: Ken McIvor <mcivor@iit.edu>
#
# Copyright 2005 Illinois Institute of Technology
#
# See the file "LICENSE" for information on usage and redistribution
# of this file, and for a DISCLAIMER OF ALL WARRANTIES.

# load WxMpl's Python module
import wxmpl

# Create the PlotApp instance.
# The title string is one of several optional arguments.
app = wxmpl.PlotApp('WxMpl Example 1')

# <== This spot is where the plotting happens

# Let wxPython do its thing.
app.MainLoop()
