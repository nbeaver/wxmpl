# Name: ex02.py
# Purpose: WxMpl Example 2: y=sin(pi*x)
# Author: Ken McIvor <mcivor@iit.edu>
#
# Copyright 2005 Illinois Institute of Technology
#
# See the file "LICENSE" for information on usage and redistribution
# of this file, and for a DISCLAIMER OF ALL WARRANTIES.

import wxmpl
app = wxmpl.PlotApp('WxMpl Example 2')

### Create the data to plot ###

from matplotlib.numerix import arange, pi, sin
x = arange(0.0, 2, 0.01)
y = sin(pi*x)

### Plot it ###

# All of WxMpl's plotting classes have a get_figure(),
# which returns the associated matplotlib Figure.
fig = app.get_figure()

# Create an Axes on the Figure to plot in.
axes = fig.gca()

# Plot the function
axes.plot(x, y)

app.MainLoop()
