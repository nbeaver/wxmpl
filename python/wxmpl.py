# Name: wxmpl
# Purpose: painless matplotlib embedding for wxPython
# Author: Ken McIvor <mcivken@iit.edu>
#
# Copyright 2005 Illinois Institute of Technology
#
# See the file "LICENSE" for information on usage and redistribution
# of this file, and for a DISCLAIMER OF ALL WARRANTIES.

"""
This module embeds matplotlib plotting canvases in wxPython programs, providing
some bells and whistles for interactive use.

Real documentation needs to be written.  For now your best bet is to check out
the `wxmpl-demos.py' program included with this release.
"""

__version__ = '0.9'


import wx
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.axes import PolarAxes
from matplotlib.backend_bases import FigureCanvasBase
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure
from matplotlib.transforms import bound_vertices, inverse_transform_bbox


__all__ = ['PlotPanel', 'PlotFrame']


def is_polar(axes):
    return isinstance(axes, PolarAxes)


def get_bbox_lims(bbox):
    return bbox.intervalx().get_bounds(), bbox.intervaly().get_bounds()


def find_axes(canvas, x, y):
    axes = None
    for a in canvas.get_figure().get_axes():
        if a.in_axes(x, y):
            if axes is None:
                axes = a
            else:
                return None, None, None # XXX: broken for plot_axes() demo

    if axes is None:
        return None, None, None

    xdata, ydata = axes.transData.inverse_xy_tup((x,y))
    return axes, xdata, ydata


def find_selected_axes(canvas, x1, y1, x2, y2):
    axes = None
    bbox = bound_vertices([(x1, y1), (x2, y2)])

    for a in canvas.get_figure().get_axes():
        if bbox.overlaps(a.bbox):
            if axes is None:
                axes = a
            else:
                return None, None, None # XXX: broken for plot_axes() demo

    if axes is None:
        return None, None, None

    bxr, byr = get_bbox_lims(bbox)
    axr, ayr = get_bbox_lims(axes.bbox)

    xmin = max(bxr[0], axr[0])
    xmax = min(bxr[1], axr[1])
    ymin = max(byr[0], ayr[0])
    ymax = min(byr[1], ayr[1])
    xrange, yrange = get_bbox_lims(
        inverse_transform_bbox(axes.transData,
            bound_vertices([(xmin, ymin), (xmax, ymax)])))
    return axes, xrange, yrange


class AxesLimits:
    def __init__(self):
        self.history = {}

    def _get_history(self, axes):
        return self.history.setdefault(axes, [])

    def set(self, axes, xrange, yrange):
        if is_polar(axes):
            return False

        self._get_history(axes).append((axes.get_xlim(), axes.get_ylim()))
        axes.set_xlim(xrange)
        axes.set_ylim(yrange)
        return True

    def restore(self, axes):
        hist = self._get_history(axes)
        if not hist:
            return False
        else:
            xrange, yrange = hist.pop()
            axes.set_xlim(xrange)
            axes.set_ylim(yrange)
            return True


class DestructableViewMixin:
    def destroy(self):
        self.view = None


def format_coord(axes, xdata, ydata):
    if xdata is None or ydata is None:
        return ''
    return axes.format_coord(xdata, ydata)


class PlotPanelDirector(DestructableViewMixin):
    def __init__(self, view, zoom=True, selection=True):
        self.view = view
        self.zoomEnabled = zoom
        self.selectionEnabled = selection
        self.limits = AxesLimits()
        self.leftButtonPoint = None

    def setSelection(self, state):
        self.selectionEnabled = state

    def setZoomEnabled(self, state):
        self.zoomEnabled = state

    def canDraw(self):
        return self.leftButtonPoint is None

    def keyDown(self, evt):
        pass

    def keyUp(self, evt):
        pass

    def leftButtonDown(self, evt, x, y):
        view = self.view
        axes, xdata, ydata = find_axes(view, x, y)

        if self.selectionEnabled and not is_polar(axes):
            self.leftButtonPoint = (x, y)
            view.cursor.setCross()
            view.crosshairs.clear()

    def leftButtonUp(self, evt, x, y):
        view = self.view

        if self.leftButtonPoint is None:
            view.notifyPoint(x, y)
            return None

        x0, y0 = self.leftButtonPoint
        self.leftButtonPoint = None
        view.rubberband.clear()

        if x0 == x:
            if y0 == y:
                view.notifyPoint(x, y)
            return
        elif y0 == y:
            return

        xdata = ydata = None
        axes, xrange, yrange = find_selected_axes(view, x0, y0, x, y)

        if not self.zoomEnabled:
            self.view.notifySelection(x0, y0, x, y)
        elif axes is not None:
            xdata, ydata = axes.transData.inverse_xy_tup((x,y))
            if self.limits.set(axes, xrange, yrange):
                self.view.draw()

        if axes is None:
            view.cursor.setNormal()
        elif is_polar(axes):
            view.cursor.setNormal()
            view.location.set(format_coord(axes, xdata, ydata))
        else:
            view.crosshairs.set(x, y)
            view.location.set(format_coord(axes, xdata, ydata))

    def rightButtonDown(self, evt, x, y):
        pass

    def rightButtonUp(self, evt, x, y):
        view = self.view
        axes, xdata, ydata = find_axes(view, x, y)
        if axes is not None and self.limits.restore(axes):
            view.crosshairs.clear()
            view.draw()
            view.crosshairs.set(x, y)

    def mouseMotion(self, evt, x, y):
        view = self.view
        axes, xdata, ydata = find_axes(view, x, y)

        if self.leftButtonPoint is None:
            if axes is None:
                self.canvasMouseMotion(evt, x, y)
            elif is_polar(axes):
                self.polarAxesMouseMotion(evt, x, y, axes, xdata, ydata)
            else:
                self.axesMouseMotion(evt, x, y, axes, xdata, ydata)
        else:
            x0, y0 = self.leftButtonPoint
            view.rubberband.set(x0, y0, x, y)
            if axes is None:
                view.location.clear()
            else:
                view.location.set(format_coord(axes, xdata, ydata))

    def canvasMouseMotion(self, evt, x, y):
        view = self.view
        view.cursor.setNormal()
        view.crosshairs.clear()
        view.location.clear()

    def polarAxesMouseMotion(self, evt, x, y, axes, xdata, ydata):
        view = self.view
        view.cursor.setNormal()
        view.location.set(format_coord(axes, xdata, ydata))

    def axesMouseMotion(self, evt, x, y, axes, xdata, ydata):
        view = self.view
        view.cursor.setCross()
        view.crosshairs.set(x, y)
        view.location.set(format_coord(axes, xdata, ydata))


class Painter(DestructableViewMixin):
    PEN = wx.BLACK_PEN
    BRUSH = wx.TRANSPARENT_BRUSH
    FUNCTION = wx.COPY
    FONT = wx.NORMAL_FONT
    TEXT_FOREGROUND = wx.BLACK
    TEXT_BACKGROUND = wx.WHITE

    def __init__(self, view, enabled=True):
        self.view = view
        self.lastValue = None
        self.enabled = enabled

    def setEnabled(self, state):
        self.enabled = state

    def set(self, *value):
        if self.enabled:
            value = self.formatValue(value)
            self._paint(value)
            self.lastValue = value
        else:
            self.clear()

    def clear(self):
        if self.lastValue is not None:
            self._paint(None)

    def _paint(self, value):
        dc = wx.ClientDC(self.view)
        dc.SetPen(self.PEN)
        dc.SetBrush(self.BRUSH)
        dc.SetFont(self.FONT)
        dc.SetTextForeground(self.TEXT_FOREGROUND)
        dc.SetTextBackground(self.TEXT_BACKGROUND)
        dc.SetLogicalFunction(self.FUNCTION)
        dc.BeginDrawing()

        if self.lastValue is not None:
            self.clearValue(dc, self.lastValue)
            self.lastValue = None

        if value is not None:
            self.drawValue(dc, value)
            self.lastValue = value

        dc.EndDrawing()

    def formatValue(self, value):
        return value

    def drawValue(self, dc, value):
        pass

    def clearValue(self, dc, value):
        pass


class LocationPainter(Painter):
    PADDING = 2
    PEN = wx.WHITE_PEN
    BRUSH = wx.WHITE_BRUSH

    def formatValue(self, value):
        return value[0]

    def getXYWH(self, dc, value):
        height = dc.GetSize()[1]
        w, h = dc.GetTextExtent(value)
        x = self.PADDING
        y = int(height - (h + self.PADDING))
        return x, y, w, h

    def drawValue(self, dc, value):
        x, y, w, h = self.getXYWH(dc, value)
        dc.DrawText(value, x, y)

    def clearValue(self, dc, value):
        x, y, w, h = self.getXYWH(dc, value)
        dc.DrawRectangle(x, y, w, h)


class CrosshairPainter(Painter):
    PEN = wx.WHITE_PEN
    FUNCTION = wx.XOR

    def formatValue(self, value):
        x, y = value
        return int(x), int(self.view.get_figure().bbox.height() - y)

    def drawValue(self, dc, value):
        dc.CrossHair(*value)

    def clearValue(self, dc, value):
        dc.CrossHair(*value)


class RubberbandPainter(Painter):
    PEN = wx.WHITE_PEN
    FUNCTION = wx.XOR

    def formatValue(self, value):
        x1, y1, x2, y2 = value
        height = self.view.get_figure().bbox.height()
        y1 = height - y1
        y2 = height - y2
        if x2 < x1: x1, x2 = x2, x1
        if y2 < y1: y1, y2 = y2, y1
        return [int(z) for z in (x1, y1, x2-x1, y2-y1)]

    def drawValue(self, dc, value):
        dc.DrawRectangle(*value)

    def clearValue(self, dc, value):
        dc.DrawRectangle(*value)


class CursorChanger(DestructableViewMixin):
    def __init__(self, view, enabled=True):
        self.view = view
        self.cursor = wx.CURSOR_DEFAULT
        self.enabled = enabled

    def setEnabled(self, state):
        self.enabled = state

    def setNormal(self):
        if self.cursor != wx.CURSOR_DEFAULT and self.enabled:
            self.cursor = wx.CURSOR_DEFAULT
            self.view.SetCursor(wx.STANDARD_CURSOR)

    def setCross(self):
        if self.cursor != wx.CURSOR_CROSS and self.enabled:
            self.cursor = wx.CURSOR_CROSS
            self.view.SetCursor(wx.CROSS_CURSOR)


class PlotPanel(FigureCanvasWxAgg):
    def __init__(self, parent, id, size=(6.0, 3.70), dpi=96, cursor=True,
     location=True, crosshairs=True, selection=True, zoom=True):
        FigureCanvasWxAgg.__init__(self, parent, id, Figure(size, dpi))

        self.cursor = CursorChanger(self, cursor)
        self.location = LocationPainter(self, location)
        self.crosshairs = CrosshairPainter(self, crosshairs)
        self.rubberband = RubberbandPainter(self, selection)
        self.director = PlotPanelDirector(self, zoom, selection)

        self.figure.set_edgecolor('black')
        self.figure.set_facecolor('white')
        self.SetBackgroundColour(wx.WHITE)

        wx.EVT_WINDOW_DESTROY(self, self.OnDestroy)

    def OnDestroy(self, evt):
        objects = [self.cursor, self.location, self.rubberband,
            self.crosshairs, self.director]

        self._onPaint = lambda *a, **b: None
        for obj in objects:
            obj.destroy()

    def set_figure(self, figure):
        self.figure = figure
        figure.set_canvas(self)
        self.draw()

    def get_figure(self):
        return self.figure

    def set_zoom(self, state):
        self.director.setZoomEnabled(state)

    def set_selection(self, state):
        self.rubberband.setEnabled(state)
        self.director.setSelectionEnabled(state)

    def set_location(self, state):
        self.location.setEnabled(state)

    def set_crosshairs(self, state):
        self.crosshairs.setEnabled(state)

    def set_cursor(self, state):
        self.cursor.setEnabled(state)

    def draw(self):
        if self.director.canDraw():
            wx.BeginBusyCursor()
            FigureCanvasWxAgg.draw(self)
            wx.EndBusyCursor()

    def notifyPoint(self, x, y):
        print 'notifyPoint():', x, y

    def notifySelection(self, x1, y1, x2, y2):
        print 'notifySelection():',  (x1, y1),  (x2, y2)

    def _get_canvas_xy(self, evt):
        return evt.GetX(), self.figure.bbox.height() - evt.GetY()

    def _onKeyDown(self, evt):
        key = self._get_key(evt)
        evt.Skip()
        self.director.keyDown(evt)
        FigureCanvasBase.key_press_event(self, key)

    def _onKeyUp(self, evt):
        key = self._get_key(evt)
        evt.Skip()
        self.director.keyUp(evt)
        FigureCanvasBase.key_release_event(self, key)
 
    def _onLeftButtonDown(self, evt):
        x, y = self._get_canvas_xy(evt)
        evt.Skip()
        self.director.leftButtonDown(evt, x, y)
        FigureCanvasBase.button_press_event(self, x, y, 1)

    def _onLeftButtonUp(self, evt):
        x, y = self._get_canvas_xy(evt)
        evt.Skip()
        self.director.leftButtonUp(evt, x, y)
        FigureCanvasBase.button_release_event(self, x, y, 1)

    def _onRightButtonDown(self, evt):
        x, y = self._get_canvas_xy(evt)
        evt.Skip()
        self.director.rightButtonDown(evt, x, y)
        FigureCanvasBase.button_press_event(self, x, y, 3)        

    def _onRightButtonUp(self, evt):
        x, y = self._get_canvas_xy(evt)
        evt.Skip()
        self.director.rightButtonUp(evt, x, y)
        FigureCanvasBase.button_release_event(self, x, y, 3)        

    def _onMotion(self, evt):
        x, y = self._get_canvas_xy(evt)
        evt.Skip()
        self.director.mouseMotion(evt, x, y)
        FigureCanvasBase.motion_notify_event(self, x, y)


class PlotFrame(wx.Frame):
    def __init__(self, parent, id, title, size=(6.0, 3.7), dpi=96, cursor=True,
     location=True, crosshairs=True, selection=True, zoom=True, **kwds):
        wx.Frame.__init__(self, parent, id, title, **kwds)
        self.panel = PlotPanel(self, -1, size, dpi, cursor, location,
            crosshairs, selection, zoom)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel, 1, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(sizer)
        self.Fit()

    def set_figure(self, figure):
        self.panel.set_figure(figure)

    def get_figure(self):
        return self.panel.figure

    def set_zoom(self, state):
        self.panel.set_zoom(state)

    def set_selection(self, state):
        self.panel.set_selection(state)

    def set_location(self, state):
        self.panel.set_location(state)

    def set_crosshairs(self, state):
        self.panel.set_crosshairs(state)

    def set_cursor(self, state):
        self.panel.set_cursor(state)

    def draw(self):
        self.panel.draw()

