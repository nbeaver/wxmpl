# Name: ex11.py
# Purpose: WxMpl Example 11: Subplots
# Author: Ken McIvor <mcivor@iit.edu>
#
# Copyright 2005 Illinois Institute of Technology
#
# See the file "LICENSE" for information on usage and redistribution
# of this file, and for a DISCLAIMER OF ALL WARRANTIES.

import wxmpl
app = wxmpl.PlotApp('WxMpl Example 11')

### Create the data to plot ###

from matplotlib.numerix import arange, pi, sin, cos
x = arange(0.0, 2, 0.01)
y1 = sin(pi*x)
y2 = cos(pi*x)

### Plot it ###

fig = app.get_figure()

# Create the subplot Axes
axes1 = fig.add_subplot(2, 1, 1)
axes2 = fig.add_subplot(2, 1, 2)

axes1.plot(x, y1)
axes2.plot(x, y2)

# Subplots must be labeled carefully, since labels
# can be accidentally hidden by other subplots
axes1.set_title('Example 11: Subplots')
axes1.set_ylabel('y = sin(pi*x)')

axes2.set_xlabel('x axis')
axes2.set_ylabel('y = cos(pi*x)')

app.MainLoop()
