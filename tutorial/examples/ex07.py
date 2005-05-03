# Name: ex07.py
# Purpose: WxMpl Example 7: Title and X/Y axis labels
# Author: Ken McIvor <mcivor@iit.edu>
#
# Copyright 2005 Illinois Institute of Technology
#
# See the file "LICENSE" for information on usage and redistribution
# of this file, and for a DISCLAIMER OF ALL WARRANTIES.

import wxmpl
app = wxmpl.PlotApp('WxMpl Example 7')

### Create the data to plot ###

from matplotlib.numerix import arange, pi, sin
x = arange(0.0, 2, 0.01)
y = sin(pi*x)

### Plot it ###

fig = app.get_figure()
axes = fig.gca()

axes.plot(x, y)

# Label the plot
axes.set_title('Example 7: Titles and Labels')
axes.set_xlabel('x axis')
axes.set_ylabel('y = sin(pi*x)')


app.MainLoop()
