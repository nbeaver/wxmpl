# Name: ex10.py
# Purpose: WxMpl Example 10: Arbitrary text placement
# Author: Ken McIvor <mcivor@iit.edu>
#
# Copyright 2005 Illinois Institute of Technology
#
# See the file "LICENSE" for information on usage and redistribution
# of this file, and for a DISCLAIMER OF ALL WARRANTIES.

import wxmpl
app = wxmpl.PlotApp('WxMpl Example 10')

### Create the data to plot ###

from matplotlib.numerix import arange, pi, sin
x = arange(0.0, 2, 0.01)
y = sin(pi*x)

### Plot it ###

fig = app.get_figure()
axes = fig.gca()

axes.plot(x, y)

axes.set_title('Example 10: Text Placement')
theme = {'fontname': 'courier', 'fontsize': 12}

# text(x, y, string, [theme-dictionary,] [text properties])
axes.text(0.5, 0, '0.5', theme, color='r')
axes.text(1.0, 0, '1.0', theme, color='k')
axes.text(1.5, 0, '1.5', theme, color='g')


app.MainLoop()
