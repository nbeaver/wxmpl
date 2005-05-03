# Name: ex04.py
# Purpose: WxMpl Example 4: Axes legends
# Author: Ken McIvor <mcivor@iit.edu>
#
# Copyright 2005 Illinois Institute of Technology
#
# See the file "LICENSE" for information on usage and redistribution
# of this file, and for a DISCLAIMER OF ALL WARRANTIES.

import wxmpl
app = wxmpl.PlotApp('WxMpl Example 4')

### Create the data to plot ###

from matplotlib.numerix import arange, pi, sin, cos, exp
x = arange(0.0, 2, 0.01)
y1 = sin(pi*x)
y2 = cos(pi*x)
y3 = exp(x)

### Plot it ###

fig = app.get_figure()
axes = fig.gca()

# `label' is the line property that matplotlib uses
# to create the Axes legend.
axes.plot(x, y1, label='sin(pi*x)')
axes.plot(x, y2, label='cos(pi*x)')
axes.plot(x, y3, label='exp(x)')
# Create the legend
axes.legend()

app.MainLoop()
