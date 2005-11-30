# Name: WxMplPoints.py
# Purpose: Demonstrates point picking in WxMpl
# Author: Ken McIvor <mcivor@iit.edu>
#
# Copyright 2005 Illinois Institute of Technology
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL ILLINOIS INSTITUTE OF TECHNOLOGY BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Except as contained in this notice, the name of Illinois Institute
# of Technology shall not be used in advertising or otherwise to promote
# the sale, use or other dealings in this Software without prior written
# authorization from Illinois Institute of Technology.


import wx
import wxmpl
import matplotlib.numerix as nx
import matplotlib.patches


class MyApp(wx.App):
    def OnInit(self):
        self.frame = panel = MyFrame(None, -1, 'Point Picker')
        self.frame.Show(True)
        return True


class MyFrame(wx.Frame):
    def __init__(self, parent, id, title, **kwds):
        wx.Frame.__init__(self, parent, id, title, **kwds)

        self.points = []
        self.selectionPoints = []
        self.plotPanel = wxmpl.PlotPanel(self, -1)
        self.regionButton = wx.ToggleButton(self, -1, 'Pick Region')
        self.pointButton  = wx.ToggleButton(self, -1, 'Pick Point')

        wx.EVT_TOGGLEBUTTON(self, self.regionButton.GetId(),
            self._on_regionButton)

        wxmpl.EVT_POINT(self,     self.plotPanel.GetId(), self._on_point)
        wxmpl.EVT_SELECTION(self, self.plotPanel.GetId(), self._on_selection)

        self._layout()
        self._replot()

    def _layout(self):
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((1, 1), 1, 0, 0)
        btnSizer.Add(self.regionButton, 0, wx.BOTTOM|wx.RIGHT, 5)
        btnSizer.Add(self.pointButton,  0, wx.BOTTOM|wx.RIGHT, 5)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.plotPanel, 0, wx.ALL, 5)
        sizer.Add(btnSizer, 0, wx.EXPAND, 0)

        self.SetSizer(sizer)
        self.Fit()

    def _replot(self):
        PI = nx.pi
        t = nx.arange(0.0, 2.0, 0.01)
        s = nx.sin(2*PI*t)

        fig = self.plotPanel.get_figure()
        axes = fig.gca()

        # store the current zoom limits
        xlim = axes.get_xlim()
        ylim = axes.get_ylim()

        # clear the axes and replot everything
        axes.cla()
        axes.plot(t, s, linewidth=1.0, label='sin')

        # plot the selected regions as rectangles
        for (xy, w, h) in self.selectionPoints:
            sel = matplotlib.patches.Rectangle(xy, w, h, edgecolor='k',
                    facecolor='r', label='_nolegend_', alpha=0.25)
            axes.add_patch(sel)

        # plot the points
        if self.points:
            pts  = nx.array(self.points)
            ptsY = nx.cos(2*PI*pts)
            axes.plot(pts, ptsY, 'go', markersize=5, label='pts')

            if 1 < len(self.points):
                rng  = nx.arange(min(self.points), max(self.points), 0.01)
                rngY = nx.cos(2*PI*rng)
                axes.plot(rng, rngY, 'g-', linewidth=1,  label='cos')

        axes.set_xlabel('time (s)')
        axes.set_ylabel('voltage (mV)')
        axes.set_title('Peter Plotter Picked a Point of Pickled Plotting')
        axes.legend()

        # restore the zoom limits (unless they're for an empty plot)
        if xlim != (0.0, 1.0) or ylim != (0.0, 1.0):
            axes.set_xlim(xlim)
            axes.set_ylim(ylim)

        # redraw the disply
        self.plotPanel.draw()

    def _on_regionButton(self, evt):
        self.plotPanel.set_zoom(False)

    def _on_selection(self, evt):
        self.plotPanel.set_zoom(True)
        self.regionButton.SetValue(False)

        x1, y1 = evt.x1data, evt.y1data
        x2, y2 = evt.x2data, evt.y2data

        self.selectionPoints.append(((x1, y1), x2-x1, y2-y1))
        self._replot()

    def _on_point(self, evt):
        print '_on_point()'
        if self.pointButton.GetValue():
            self.pointButton.SetValue(False)
            if evt.axes is not None:
                self.points.append(evt.xdata)
                self._replot()


#app = wxmpl.PlotApp()
#figure = app.get_figure()
#plot_simple(figure)

app = MyApp()
app.MainLoop()
