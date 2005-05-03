# Name: ex05.py
# Purpose: WxMpl Example 5: Line styles with format strings
# Author: Ken McIvor <mcivor@iit.edu>
#
# Copyright 2005 Illinois Institute of Technology
#
# See the file "LICENSE" for information on usage and redistribution
# of this file, and for a DISCLAIMER OF ALL WARRANTIES.

import wxmpl
app = wxmpl.PlotApp('WxMpl Example 5')

### Create the data to plot ###

from matplotlib.numerix import arange, pi, sin, cos, exp
x = arange(0.0, 2, 0.1)
y1 = sin(pi*x)
y2 = cos(pi*x)
y3 = exp(x)

### Plot it ###

fig = app.get_figure()
axes = fig.gca()

# solid line, blue, circle symbols
axes.plot(x, y1, '-bo', label='-bo')

# no line, red, cross symbols
axes.plot(x, y2, 'rx', label='rx')

# dashed line, black, vertical line symbols
axes.plot(x, y3, '--k|', label='--k|')

axes.legend()

app.MainLoop()
