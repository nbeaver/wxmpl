# Name: ex08.py
# Purpose: WxMpl Example 8: Text properties
# Author: Ken McIvor <mcivor@iit.edu>
#
# Copyright 2005 Illinois Institute of Technology
#
# See the file "LICENSE" for information on usage and redistribution
# of this file, and for a DISCLAIMER OF ALL WARRANTIES.

import wxmpl
app = wxmpl.PlotApp('WxMpl Example 8')

### Create the data to plot ###

from matplotlib.numerix import arange, pi, sin
x = arange(0.0, 2, 0.01)
y = sin(pi*x)

### Plot it ###

fig = app.get_figure()
axes = fig.gca()

axes.plot(x, y)

# Red, Bold, 12pt
axes.set_title('Example 8: Text Properties', color='r',
    fontweight='bold', fontsize=12)

# Green, `smaller' size
axes.set_xlabel('x axis', color='g', fontsize='smaller')

# Italic
axes.set_ylabel('y = sin(pi*x)', fontstyle='italic')


app.MainLoop()
