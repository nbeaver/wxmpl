# Name: ex09.py
# Purpose: WxMpl Example 9: Text themes
# Author: Ken McIvor <mcivor@iit.edu>
#
# Copyright 2005 Illinois Institute of Technology
#
# See the file "LICENSE" for information on usage and redistribution
# of this file, and for a DISCLAIMER OF ALL WARRANTIES.

import wxmpl
app = wxmpl.PlotApp('WxMpl Example 9')

### Create the data to plot ###

from matplotlib.numerix import arange, pi, sin
x = arange(0.0, 2, 0.01)
y = sin(pi*x)

### Plot it ###

fig = app.get_figure()
axes = fig.gca()

axes.plot(x, y)

theme = {'color': 'r', 'fontsize': 10}
axes.set_title('Example 9: Text Themes', theme, fontsize=12)
axes.set_xlabel('x axis', theme, color='g')
axes.set_ylabel('y = sin(pi*x)', theme, fontstyle='italic')


app.MainLoop()
