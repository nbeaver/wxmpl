# Name: ex06.py
# Purpose: WxMpl Example 6: Line properties
# Author: Ken McIvor <mcivor@iit.edu>
#
# Copyright 2005 Illinois Institute of Technology
#
# See the file "LICENSE" for information on usage and redistribution
# of this file, and for a DISCLAIMER OF ALL WARRANTIES.

import wxmpl
app = wxmpl.PlotApp('WxMpl Example 6')

### Create the data to plot ###

from matplotlib.numerix import arange, pi, sin, cos, exp
x = arange(0.0, 2, 0.1)
y1 = sin(pi*x)
y2 = cos(pi*x)

### Plot it ###

fig = app.get_figure()
axes = fig.gca()

axes.plot(x, y1,     '--b', label='LW=1', linewidth=1)
axes.plot(x, y1+0.5, '--r', label='LW=2', linewidth=2)
axes.plot(x, y1+1.0, '--k', label='LW=3', linewidth=3)

axes.plot(x, y2,     'xr', label='MS=3', markersize=3)
axes.plot(x, y2+0.5, 'xk', label='MS=5', markersize=5)
axes.plot(x, y2+1.0, 'xb', label='MS=7', markersize=7)

axes.legend()

app.MainLoop()
