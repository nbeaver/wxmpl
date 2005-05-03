# Name: wxmpl
# Purpose: painless matplotlib embedding for wxPython
# Author: Ken McIvor <mcivor@iit.edu>
#
# Copyright 2005 Illinois Institute of Technology
#
# See the file "LICENSE" for information on usage and redistribution
# of this file, and for a DISCLAIMER OF ALL WARRANTIES.

"""
Embedding matplotlib in wxPython applications is straightforward, but the
default plotting widget lacks the capabilities necessary for interactive use.
WxMpl (wxPython+matplotlib) is a library of components that provide these
missing features.
"""

__version__ = '0.9'


import wx
import os.path
import weakref

import matplotlib
matplotlib.use('WXAgg')
from matplotlib.axes import PolarAxes, _process_plot_var_args
from matplotlib.backend_bases import FigureCanvasBase
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.transforms import Bbox, Point, Value
from matplotlib.transforms import bound_vertices, inverse_transform_bbox

__all__ = ['PlotPanel', 'PlotFrame', 'StripCharter', 'Channel', 'EVT_POINT',
    'EVT_SELECTION']


#
# Utility functions and classes
#

def is_polar(axes):
    """
    Returns a boolean indicating if C{axes} is a polar axes.
    """
    return isinstance(axes, PolarAxes)


def find_axes(canvas, x, y):
    """
    Finds the C{Axes} within a matplotlib C{FigureCanvas} contains the canavs
    coordinates C{(x, y)} and returns that axes and the corresponding data
    coordinates C{xdata, ydata} as a 3-tuple.

    If no axes contains the specified point a 3-tuple of C{None} is returned.
    """

    axes = None
    for a in canvas.get_figure().get_axes():
        if a.in_axes(x, y):
            if axes is None:
                axes = a
            else:
                return None, None, None

    if axes is None:
        return None, None, None

    xdata, ydata = axes.transData.inverse_xy_tup((x, y))
    return axes, xdata, ydata


def get_bbox_lims(bbox):
    """
    Returns the boundaries of the X and Y intervals of a C{Bbox}.
    """
    return bbox.intervalx().get_bounds(), bbox.intervaly().get_bounds()


def find_selected_axes(canvas, x1, y1, x2, y2):
    """
    Finds the C{Axes} within a matplotlib C{FigureCanvas} that overlaps with a
    canvas area from C{(x1, y1)} to C{(x1, y1)}.  That axes and the
    corresponding X and Y axes ranges are returned as a 3-tuple.

    If no axes overlaps with the specified area, or more than one axes
    overlaps, a 3-tuple of C{None}s is returned.
    """
    axes = None
    bbox = bound_vertices([(x1, y1), (x2, y2)])

    for a in canvas.get_figure().get_axes():
        if bbox.overlaps(a.bbox):
            if axes is None:
                axes = a
            else:
                return None, None, None

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


def format_coord(axes, xdata, ydata):
    """
    A C{None}-safe version of {Axes.format_coord()}.
    """
    if xdata is None or ydata is None:
        return ''
    return axes.format_coord(xdata, ydata)


class AxesLimits:
    """
    Alters the X and Y limits of C{Axes} objects while maintaining a history of
    the changes.
    """
    def __init__(self):
        self.history = weakref.WeakKeyDictionary()

    def _get_history(self, axes):
        """
        Returns the history list of X and Y limits associated with C{axes}.
        """
        return self.history.setdefault(axes, [])

    def zoomed(self, axes):
        """
        Returns a boolean indicating whether C{axes} has had its limits
        altered.
        """
        return not (not self._get_history(axes))

    def set(self, axes, xrange, yrange):
        """
        Changes the X and Y limits of C{axes} to C{xrange} and {yrange}
        respectively.  A boolean indicating whether or not the
        axes should be redraw is returned, because polar axes cannot have
        their limits changed sensibly.
        """
        if is_polar(axes):
            return False

        self._get_history(axes).append((axes.get_xlim(), axes.get_ylim()))
        axes.set_xlim(xrange)
        axes.set_ylim(yrange)
        return True

    def restore(self, axes):
        """
        Changes the X and Y limits of C{axes} to their previous values.  A
        boolean indicating whether or not the axes should be redraw is
        returned.
        """
        hist = self._get_history(axes)
        if not hist:
            return False
        else:
            xrange, yrange = hist.pop()
            axes.set_xlim(xrange)
            axes.set_ylim(yrange)
            return True


class DestructableViewMixin:
    """
    Utility class to break the circular reference between an object and its
    associated "view".
    """
    def destroy(self):
        """
        Sets this object's C{view} attribute to C{None}.
        """
        self.view = None


#
# Director of the matplotlib canvas
#

class PlotPanelDirector(DestructableViewMixin):
    """
    Encapsulates all of the user-interaction logic required by the
    C{PlotPanel}, following the Humble Dialog Box pattern proposed by Michael
    Feathers:
    U{http://www.objectmentor.com/resources/articles/TheHumbleDialogBox.pdf}
    """
    def __init__(self, view, zoom=True, selection=True, rightClickUnzoom=True):
        """
        Create a new director for the C{PlotPanel} C{view}.  The keyword
        arguments C{zoom} and C{selection} have the same meanings as for
        C{PlotPanel}.
        """
        self.view = view
        self.zoomEnabled = zoom
        self.selectionEnabled = selection
        self.rightClickUnzoom = rightClickUnzoom # FIXME: this is unused
        self.limits = AxesLimits()
        self.leftButtonPoint = None
        # FIXME: Law of Demeter -- merge all of the self.view.XYZ.something()
        # methods into accessor methods of the PlotPanel

    def setSelection(self, state):
        """
        Enable or disable left-click area selection.
        """
        self.selectionEnabled = state

    def setZoomEnabled(self, state):
        """
        Enable or disable zooming as a result of left-click area selection.
        """
        self.zoomEnabled = state

    def setRightClickUnzoom(self, state):
        """
        Enable or disable unzooming as a result of right-clicking.
        """
        self.rightClickUnzoom = state

    def canDraw(self):
        """
        Returns a boolean indicating whether or not the plot may be redrawn.
        """
        return self.leftButtonPoint is None

    def zoomed(self, axes):
        """
        Returns a boolean indicating whether or not the plot has been zoomed in
        as a result of a left-click area selection.
        """
        return self.limits.zoomed(axes)

    def keyDown(self, evt):
        """
        Handles wxPython key-press events.  These events are currently skipped.
        """
        evt.Skip()

    def keyUp(self, evt):
        """
        Handles wxPython key-release events.  These events are currently
        skipped.
        """
        evt.Skip()

    def leftButtonDown(self, evt, x, y):
        """
        Handles wxPython left-click events.
        """
        self.leftButtonPoint = (x, y)

        view = self.view
        axes, xdata, ydata = find_axes(view, x, y)

        if self.selectionEnabled and not is_polar(axes):
            view.cursor.setCross()
            view.crosshairs.clear()

    def leftButtonUp(self, evt, x, y):
        """
        Handles wxPython left-click-release events.
        """
        if self.leftButtonPoint is None:
            return

        view = self.view
        axes, xdata, ydata = find_axes(view, x, y)

        x0, y0 = self.leftButtonPoint
        self.leftButtonPoint = None
        view.rubberband.clear()

        if x0 == x:
            if y0 == y and axes is not None:
                view.notify_point(axes, x, y)
            return
        elif y0 == y:
            return

        xdata = ydata = None
        axes, xrange, yrange = find_selected_axes(view, x0, y0, x, y)

        if axes is not None:
            xdata, ydata = axes.transData.inverse_xy_tup((x, y))
            if self.zoomEnabled:
                if self.limits.set(axes, xrange, yrange):
                    self.view.draw()
            else:
                self.view.notify_selection(axes, x0, y0, x, y)

        if axes is None:
            view.cursor.setNormal()
        elif is_polar(axes):
            view.cursor.setNormal()
            view.location.set(format_coord(axes, xdata, ydata))
        else:
            view.crosshairs.set(x, y)
            view.location.set(format_coord(axes, xdata, ydata))

    def rightButtonDown(self, evt, x, y):
        """
        Handles wxPython right-click events.  These events are currently
        skipped.
        """
        evt.Skip()

    def rightButtonUp(self, evt, x, y):
        """
        Handles wxPython right-click-release events.
        """
        view = self.view
        axes, xdata, ydata = find_axes(view, x, y)
        if (axes is not None and self.zoomEnabled and self.rightClickUnzoom
        and self.limits.restore(axes)):
            view.crosshairs.clear()
            view.draw()
            view.crosshairs.set(x, y)

    def mouseMotion(self, evt, x, y):
        """
        Handles wxPython mouse motion events, dispatching them based on whether
        or not a selection is in process and what the cursor is over.
        """
        view = self.view
        axes, xdata, ydata = find_axes(view, x, y)

        if self.leftButtonPoint is not None:
            self.selectionMouseMotion(evt, x, y, axes, xdata, ydata)
        else:
            if axes is None:
                self.canvasMouseMotion(evt, x, y)
            elif is_polar(axes):
                self.polarAxesMouseMotion(evt, x, y, axes, xdata, ydata)
            else:
                self.axesMouseMotion(evt, x, y, axes, xdata, ydata)

    def selectionMouseMotion(self, evt, x, y, axes, xdata, ydata):
        """
        Handles wxPython mouse motion events that occur during a left-click
        area selection.
        """
        view = self.view
        x0, y0 = self.leftButtonPoint
        view.rubberband.set(x0, y0, x, y)
        if axes is None:
            view.location.clear()
        else:
            view.location.set(format_coord(axes, xdata, ydata))

    def canvasMouseMotion(self, evt, x, y):
        """
        Handles wxPython mouse motion events that occur over the canvas.
        """
        view = self.view
        view.cursor.setNormal()
        view.crosshairs.clear()
        view.location.clear()

    def axesMouseMotion(self, evt, x, y, axes, xdata, ydata):
        """
        Handles wxPython mouse motion events that occur over an axes.
        """
        view = self.view
        view.cursor.setCross()
        view.crosshairs.set(x, y)
        view.location.set(format_coord(axes, xdata, ydata))

    def polarAxesMouseMotion(self, evt, x, y, axes, xdata, ydata):
        """
        Handles wxPython mouse motion events that occur over a polar axes.
        """
        view = self.view
        view.cursor.setNormal()
        view.location.set(format_coord(axes, xdata, ydata))


#
# Components used by the PlotPanel
#

class Painter(DestructableViewMixin):
    """
    Painters encapsulate the mechanics of drawing some value in a wxPython
    window and erasing it.  Subclasses override template methods to process
    values and draw them.

    @cvar PEN: C{wx.Pen} to use (defaults to C{wx.BLACK_PEN})
    @cvar BRUSH: C{wx.Brush} to use (defaults to C{wx.TRANSPARENT_BRUSH})
    @cvar FUNCTION: Logical function to use (defaults to C{wx.COPY})
    @cvar FONT: C{wx.Font} to use (defaults to C{wx.NORMAL_FONT})
    @cvar TEXT_FOREGROUND: C{wx.Colour} to use (defaults to C{wx.BLACK})
    @cvar TEXT_BACKGROUND: C{wx.Colour} to use (defaults to C{wx.WHITE})
    """

    PEN = wx.BLACK_PEN
    BRUSH = wx.TRANSPARENT_BRUSH
    FUNCTION = wx.COPY
    FONT = wx.NORMAL_FONT
    TEXT_FOREGROUND = wx.BLACK
    TEXT_BACKGROUND = wx.WHITE

    def __init__(self, view, enabled=True):
        """
        Create a new painter attached to the wxPython window C{view}.  The
        keyword argument C{enabled} has the same meaning as the argument to the
        C{setEnabled()} method.
        """
        self.view = view
        self.lastValue = None
        self.enabled = enabled

    def setEnabled(self, state):
        """
        Enable or disable this painter.  Disabled painters do not draw their
        values and calls to C{set()} have no effect on them.
        """
        oldState, self.enabled = self.enabled, state
        if oldState and not self.enabled:
            self.clear()

    def set(self, *value):
        """
        Update this painter's value and then draw it.  Values may not be
        C{None}, which is used internally to represent the absence of a current
        value.
        """
        if self.enabled:
            value = self.formatValue(value)
            self._paint(value)
            self.lastValue = value

    def redraw(self):
        """
        Redraw this painter's current value.
        """
        value = self.lastValue
        self.lastValue = None
        self._paint(value)

    def clear(self):
        """
        Clear the painter's current value from the screen and the painter
        itself.
        """
        if self.lastValue is not None:
            self._paint(None)

    def _paint(self, value):
        """
        Draws a previously processed C{value} on this painter's window.
        """
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
        """
        Template method that processes the C{value} tuple passed to the
        C{set()} method, returning the processed version.
        """
        return value

    def drawValue(self, dc, value):
        """
        Template method that draws a previously processed C{value} using the
        wxPython device context C{dc}.  This DC has already been configured, so
        calls to C{BeginDrawing()} and C{EndDrawing()} may not be made.
        """
        pass

    def clearValue(self, dc, value):
        """
        Template method that clears a previously processed C{value} that was
        previously drawn, using the wxPython device context C{dc}.  This DC has
        already been configured, so calls to C{BeginDrawing()} and
        C{EndDrawing()} may not be made.
        """
        pass


class LocationPainter(Painter):
    """
    Draws a text message containing the current position of the mouse in the
    lower left corner of the plot.
    """

    PADDING = 2
    PEN = wx.WHITE_PEN
    BRUSH = wx.WHITE_BRUSH

    def formatValue(self, value):
        """
        Extracts a string from the 1-tuple C{value}.
        """
        return value[0]

    def get_XYWH(self, dc, value):
        """
        Returns the upper-left coordinates C{(X, Y)} for the string C{value}
        its width and height C{(W, H)}.
        """
        height = dc.GetSize()[1]
        w, h = dc.GetTextExtent(value)
        x = self.PADDING
        y = int(height - (h + self.PADDING))
        return x, y, w, h

    def drawValue(self, dc, value):
        """
        Draws the string C{value} in the lower left corner of the plot.
        """
        x, y, w, h = self.get_XYWH(dc, value)
        dc.DrawText(value, x, y)

    def clearValue(self, dc, value):
        """
        Clears the string C{value} from the lower left corner of the plot by
        painting a white rectangle over it.
        """
        x, y, w, h = self.get_XYWH(dc, value)
        dc.DrawRectangle(x, y, w, h)


class CrosshairPainter(Painter):
    """
    Draws crosshairs through the current position of the mouse.
    """

    PEN = wx.WHITE_PEN
    FUNCTION = wx.XOR

    def formatValue(self, value):
        """
        Converts the C{(X, Y)} mouse coordinates from matplotlib to wxPython.
        """
        x, y = value
        return int(x), int(self.view.get_figure().bbox.height() - y)

    def drawValue(self, dc, value):
        """
        Draws crosshairs through the C{(X, Y)} coordinates.
        """
        dc.CrossHair(*value)

    def clearValue(self, dc, value):
        """
        Clears the crosshairs drawn through the C{(X, Y)} coordinates.
        """
        dc.CrossHair(*value)


class RubberbandPainter(Painter):
    """
    Draws a selection rubberband from one point to another.
    """

    PEN = wx.WHITE_PEN
    FUNCTION = wx.XOR

    def formatValue(self, value):
        """
        Converts the C{(x1, y1, x2, y2)} mouse coordinates from matplotlib to
        wxPython.
        """
        x1, y1, x2, y2 = value
        height = self.view.get_figure().bbox.height()
        y1 = height - y1
        y2 = height - y2
        if x2 < x1: x1, x2 = x2, x1
        if y2 < y1: y1, y2 = y2, y1
        return [int(z) for z in (x1, y1, x2-x1, y2-y1)]

    def drawValue(self, dc, value):
        """
        Draws the selection rubberband around the rectangle
        C{(x1, y1, x2, y2)}.
        """
        dc.DrawRectangle(*value)

    def clearValue(self, dc, value):
        """
        Clears the selection rubberband around the rectangle
        C{(x1, y1, x2, y2)}.
        """
        dc.DrawRectangle(*value)


class CursorChanger(DestructableViewMixin):
    """
    Manages the current cursor of a wxPython window, allowing it to be switched
    between a normal arrow and a square cross.
    """
    def __init__(self, view, enabled=True):
        """
        Create a CursorChanger attached to the wxPython window C{view}.  The
        keyword argument C{enabled} has the same meaning as the argument to the
        C{setEnabled()} method.
        """
        self.view = view
        self.cursor = wx.CURSOR_DEFAULT
        self.enabled = enabled

    def setEnabled(self, state):
        """
        Enable or disable this cursor changer.  When disabled, the cursor is
        reset to the normal arrow and calls to the C{set()} methods have no
        effect.
        """
        oldState, self.enabled = self.enabled, state
        if oldState and not self.enabled and self.cursor != wx.CURSOR_DEFAULT:
            self.cursor = wx.CURSOR_DEFAULT
            self.view.SetCursor(wx.STANDARD_CURSOR)

    def setNormal(self):
        """
        Change the cursor of the associated window to a normal arrow.
        """
        if self.cursor != wx.CURSOR_DEFAULT and self.enabled:
            self.cursor = wx.CURSOR_DEFAULT
            self.view.SetCursor(wx.STANDARD_CURSOR)

    def setCross(self):
        """
        Change the cursor of the associated window to a square cross.
        """
        if self.cursor != wx.CURSOR_CROSS and self.enabled:
            self.cursor = wx.CURSOR_CROSS
            self.view.SetCursor(wx.CROSS_CURSOR)


#
# wxPython event interface for the PlotPanel and PlotFrame
#

EVT_POINT_ID = wx.NewId()

def EVT_POINT(win, func):
    """
    Register to receive wxPython C{PointEvent}s from a C{PlotPanel} or
    C{PlotFrame}.
    """
    win.Connect(-1, -1, EVT_POINT_ID, func)

class PointEvent(wx.PyEvent):
    """
    wxPython event emitted when a left-click-release occurs in a matplotlib
    axes of a window without an area selection.

    @cvar axes: matplotlib C{Axes} which was left-clicked
    @cvar x: matplotlib X coordinate
    @cvar y: matplotlib Y coordinate
    @cvar xdata: axes X coordinate
    @cvar ydata: axes Y coordinate
    """
    def __init__(self, axes, x, y):
        """
        Create a new C{PointEvent} for the matplotlib coordinates C{(x, y)} of
        an C{axes}.
        """
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_POINT_ID)
        self.axes = axes
        self.x = x
        self.y = y
        self.xdata, self.ydata = axes.transData.inverse_xy_tup((x, y))


EVT_SELECTION_ID = wx.NewId()

def EVT_SELECTION(win, func):
    """
    Register to receive wxPython C{SelectionEvent}s from a C{PlotPanel} or
    C{PlotFrame}.
    """
    win.Connect(-1, -1, EVT_SELECTION_ID, func)

class SelectionEvent(wx.PyEvent):
    """
    wxPython event emitted when an area selection occurs in a matplotlib axes
    of a window for which zooming has been disabled.  The selection is
    described by a rectangle from C{(x1, y1)} to C{(x2, y2)}, of which only
    one point is required to be inside the axes.

    @cvar axes: matplotlib C{Axes} which was left-clicked
    @cvar x1: matplotlib x1 coordinate
    @cvar y1: matplotlib y1 coordinate
    @cvar x2: matplotlib x2 coordinate
    @cvar y2: matplotlib y2 coordinate
    @cvar x1data: axes x1 coordinate
    @cvar y1data: axes y1 coordinate
    @cvar x2data: axes x2 coordinate
    @cvar y2data: axes y2 coordinate
    """
    def __init__(self, axes, x1, y1, x2, y2):
        """
        Create a new C{SelectionEvent} for the area described by the rectangle
        from C{(x1, y1)} to C{(x2, y2)} in an C{axes}.
        """
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_SELECTION_ID)
        self.axes = axes
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.x1data, self.y1data = axes.transData.inverse_xy_tup((x1, y1))
        self.x2data, self.y2data = axes.transData.inverse_xy_tup((x2, y2))


#
# Matplotlib canvas in a wxPython window
#

class PlotPanel(FigureCanvasWxAgg):
    """
    A matplotlib canvas suitable for embedding in wxPython applications.
    """
    def __init__(self, parent, id, size=(6.0, 3.70), dpi=96, cursor=True,
     location=True, crosshairs=True, selection=True, zoom=True):
        """
        Creates a new PlotPanel window that is the child of the wxPython window
        C{parent} with the wxPython identifier C{id}.

        The keyword arguments C{size} and {dpi} are used to create the
        matplotlib C{Figure} associated with this canvas.  C{size} is the
        desired width and height of the figure, in inches, as the 2-tuple
        C{(width, height)}.  C{dpi} is the dots-per-inch of the figure.

        The keyword arguments C{cursor}, C{location}, C{crosshairs},
        C{selection}, and C{zoom} enable or disable various user interaction
        features that are descibed in their associated C{set()} methods.
        """
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
        """
        Handles the wxPython window destruction event.
        """
        objects = [self.cursor, self.location, self.rubberband,
            self.crosshairs, self.director]
        for obj in objects:
            obj.destroy()

    def _onPaint(self, evt):
        """
        Overrides the C{FigureCanvasWxAgg} paint event.
        """
        if isinstance(self, FigureCanvasWxAgg):
            FigureCanvasWxAgg._onPaint(self, evt)

    def get_figure(self):
        """
        Returns the figure associated with this canvas.
        """
        return self.figure

    def set_cursor(self, state):
        """
        Enable or disable the changing mouse cursor.  When enabled, the cursor
        changes from the normal arrow to a square cross when the mouse enters a
        matplotlib axes on this canvas.
        """
        self.cursor.setEnabled(state)

    def set_location(self, state):
        """
        Enable or disable the display of the matplotlib axes coordinates of the
        mouse in the lower left corner of the canvas.
        """
        self.location.setEnabled(state)

    def set_crosshairs(self, state):
        """
        Enable or disable drawing crosshairs through the mouse cursor when it
        is inside a matplotlib axes.
        """
        self.crosshairs.setEnabled(state)

    def set_selection(self, state):
        """
        Enable or disable area selections, where user selects a rectangular
        area of the canvas by left-clicking and dragging the mouse.
        """
        self.rubberband.setEnabled(state)
        self.director.setSelectionEnabled(state)

    def set_zoom(self, state):
        """
        Enable or disable zooming in when the user makes an area selection and
        zooming out again when the user right-clicks.
        """
        self.director.setZoomEnabled(state)

    def zoomed(self, axes):
        """
        Returns a boolean indicating whether or not the C{axes} is zoomed in.
        """
        return self.director.zoomed(axes)

    def draw(self):
        """
        Draw the associated C{Figure} onto the screen.
        """
        if self.director.canDraw() and isinstance(self, FigureCanvasWxAgg):
            FigureCanvasWxAgg.draw(self)
            self.location.redraw()
            self.crosshairs.redraw()
            self.rubberband.redraw()

    def notify_point(self, axes, x, y):
        """
        Called by the associated C{PlotPanelDirector} to emit a C{PointEvent}.
        """
        wx.PostEvent(self, PointEvent(axes, x, y))

    def notify_selection(self, axes, x1, y1, x2, y2):
        """
        Called by the associated C{PlotPanelDirector} to emit a
        C{SelectionEvent}.
        """
        wx.PostEvent(self, SelectionEvent(axes, x1, y1, x2, y2))

    def _get_canvas_xy(self, evt):
        """
        Returns the X and Y coordinates of a wxPython event object converted to
        matplotlib canavas coordinates.
        """
        return evt.GetX(), self.figure.bbox.height() - evt.GetY()

    def _onKeyDown(self, evt):
        """
        Overrides the C{FigureCanvasWxAgg} key-press event handler, dispatching
        the event to the associated C{PlotPanelDirector}.
        """
        self.director.keyDown(evt)

    def _onKeyUp(self, evt):
        """
        Overrides the C{FigureCanvasWxAgg} key-release event handler,
        dispatching the event to the associated C{PlotPanelDirector}.
        """
        self.director.keyUp(evt)
 
    def _onLeftButtonDown(self, evt):
        """
        Overrides the C{FigureCanvasWxAgg} left-click event handler,
        dispatching the event to the associated C{PlotPanelDirector}.
        """
        x, y = self._get_canvas_xy(evt)
        self.director.leftButtonDown(evt, x, y)

    def _onLeftButtonUp(self, evt):
        """
        Overrides the C{FigureCanvasWxAgg} left-click-release event handler,
        dispatching the event to the associated C{PlotPanelDirector}.
        """
        x, y = self._get_canvas_xy(evt)
        self.director.leftButtonUp(evt, x, y)

    def _onRightButtonDown(self, evt):
        """
        Overrides the C{FigureCanvasWxAgg} right-click event handler,
        dispatching the event to the associated C{PlotPanelDirector}.
        """
        x, y = self._get_canvas_xy(evt)
        self.director.rightButtonDown(evt, x, y)

    def _onRightButtonUp(self, evt):
        """
        Overrides the C{FigureCanvasWxAgg} right-click-release event handler,
        dispatching the event to the associated C{PlotPanelDirector}.
        """
        x, y = self._get_canvas_xy(evt)
        self.director.rightButtonUp(evt, x, y)

    def _onMotion(self, evt):
        """
        Overrides the C{FigureCanvasWxAgg} mouse motion event handler,
        dispatching the event to the associated C{PlotPanelDirector}.
        """
        x, y = self._get_canvas_xy(evt)
        self.director.mouseMotion(evt, x, y)


#
# Matplotlib canvas in a top-level wxPython window
#

class PlotFrame(wx.Frame):
    """
    A matplotlib canvas embedded in a wxPython top-level window.

    @cvar ABOUT_TITLE: Title of the "About" dialog.
    @cvar ABOUT_MESSAGE: Contents of the "About" dialog.
    """

    ABOUT_TITLE = 'About wxmpl.PlotFrame'
    ABOUT_MESSAGE = ('wxmpl.PlotFrame %s\n' %  __version__
        + 'Written by Ken McIvor <mcivor@iit.edu>\n'
        + 'Copyright 2005 Illinois Institute of Technology')

    def __init__(self, parent, id, title, size=(6.0, 3.7), dpi=96, cursor=True,
     location=True, crosshairs=True, selection=True, zoom=True, **kwds):
        """
        Creates a new PlotFrame top-level window that is the child of the
        wxPython window C{parent} with the wxPython identifier C{id} and the
        title of C{title}.

        All of the named keyword arguments to this constructor have the same
        meaning as those arguments to the constructor of C{PlotPanel}.

        Any additional keyword arguments are passed to the constructor of
        C{wx.Frame}.
        """
        wx.Frame.__init__(self, parent, id, title, **kwds)
        self.panel = PlotPanel(self, -1, size, dpi, cursor, location,
            crosshairs, selection, zoom)

        mainMenu = wx.MenuBar()
        menu = wx.Menu()

        id = wx.NewId()
        menu.Append(id, '&Save As...\tCtrl+S',
            'Save a copy of the current plot')
        wx.EVT_MENU(self, id, self.OnMenuFileSave)

        menu.AppendSeparator()

        id = wx.NewId()
        menu.Append(id, '&Close Window\tCtrl+W',
            'Close the current plot window')
        wx.EVT_MENU(self, id, self.OnMenuFileClose)

        mainMenu.Append(menu, '&File')
        menu = wx.Menu()

        menu.Append(wx.ID_ABOUT, '&About...', 'Display version information')
        wx.EVT_MENU(self, wx.ID_ABOUT, self.OnMenuHelpAbout)

        mainMenu.Append(menu, '&Help')
        self.SetMenuBar(mainMenu)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel, 1, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(sizer)
        self.Fit()

    def OnMenuFileSave(self, event):
        """
        Handles File->Save menu events.
        """
        fileName = wx.FileSelector('Save Plot', default_extension='png',
            wildcard=('Portable Network Graphics (*.png)|*.png|'
                + 'Encapsulated Postscript (*.eps)|*.eps|All files (*.*)|*.*'),
            parent=self, flags=wx.SAVE|wx.OVERWRITE_PROMPT)

        if not fileName:
            return

        path, ext = os.path.splitext(fileName)
        ext = ext[1:].lower()

        if ext != 'png' and ext != 'eps':
            error_message = (
                'Only the PNG and EPS image formats are supported.\n'
                'A file extension of `png\' or `eps\' must be used.')
            wx.MessageBox(error_message, 'Error - plotit',
                parent=self, style=wx.OK|wx.ICON_ERROR)
            return

        try:
            self.panel.print_figure(fileName)
        except IOError, e:
            if e.strerror:
                err = e.strerror
            else:
                err = e

            wx.MessageBox('Could not save file: %s' % err, 'Error - plotit',
                parent=self, style=wx.OK|wx.ICON_ERROR)

    def OnMenuFileClose(self, event):
        """
        Handles File->Close menu events.
        """
        self.Close()

    def OnMenuHelpAbout(self, event):
        """
        Handles Help->About menu events.
        """
        wx.MessageBox(self.ABOUT_MESSAGE, self.ABOUT_TITLE, parent=self,
            style=wx.OK)

    def get_figure(self):
        """
        Returns the figure associated with this canvas.
        """
        return self.panel.figure

    def set_cursor(self, state):
        """
        Enable or disable the changing mouse cursor.  When enabled, the cursor
        changes from the normal arrow to a square cross when the mouse enters a
        matplotlib axes on this canvas.
        """
        self.panel.set_cursor(state)

    def set_location(self, state):
        """
        Enable or disable the display of the matplotlib axes coordinates of the
        mouse in the lower left corner of the canvas.
        """
        self.panel.set_location(state)

    def set_crosshairs(self, state):
        """
        Enable or disable drawing crosshairs through the mouse cursor when it
        is inside a matplotlib axes.
        """
        self.panel.set_crosshairs(state)

    def set_selection(self, state):
        """
        Enable or disable area selections, where user selects a rectangular
        area of the canvas by left-clicking and dragging the mouse.
        """
        self.panel.set_selection(state)

    def set_zoom(self, state):
        """
        Enable or disable zooming in when the user makes an area selection and
        zooming out again when the user right-clicks.
        """
        self.panel.set_zoom(state)

    def draw(self):
        """
        Draw the associated C{Figure} onto the screen.
        """
        self.panel.draw()


#
# wxApp providing a matplotlib canvas in a top-level wxPython window
#

class PlotApp(wx.App):
    """
    A wxApp that provides a matplotlib canvas embedded in a wxPython top-level
    window, encapsulating wxPython's nuts and bolts.

    @cvar ABOUT_TITLE: Title of the "About" dialog.
    @cvar ABOUT_MESSAGE: Contents of the "About" dialog.
    """

    ABOUT_TITLE = None
    ABOUT_MESSAGE = None

    def __init__(self, title="WxMpl", size=(6.0, 3.7), dpi=96, cursor=True,
     location=True, crosshairs=True, selection=True, zoom=True):
        """
        Creates a new PlotApp, which creates a PlotFrame top-level window.

        The keyword argument C{title} specifies the title of this top-level
        window.

        All of other the named keyword arguments to this constructor have the
        same meaning as those arguments to the constructor of C{PlotPanel}.
        """
        self.title = title
        self.size = size
        self.dpi = dpi
        self.cursor = cursor
        self.location = location
        self.crosshairs = crosshairs
        self.selection = selection
        self.zoom = zoom
        wx.App.__init__(self)

    def OnInit(self):
        self.panel = panel = PlotFrame(None, -1, self.title, self.size,
            self.dpi, self.cursor, self.location, self.crosshairs,
            self.selection, self.zoom)

        if self.ABOUT_TITLE is not None:
            panel.ABOUT_TITLE = self.ABOUT_TITLE

        if self.ABOUT_MESSAGE is not None:
            panel.ABOUT_MESSAGE = self.ABOUT_MESSAGE

        panel.Show(True)
        return True

    def get_figure(self):
        """
        Returns the figure associated with this canvas.
        """
        return self.panel.get_figure()

    def set_cursor(self, state):
        """
        Enable or disable the changing mouse cursor.  When enabled, the cursor
        changes from the normal arrow to a square cross when the mouse enters a
        matplotlib axes on this canvas.
        """
        self.panel.set_cursor(state)

    def set_location(self, state):
        """
        Enable or disable the display of the matplotlib axes coordinates of the
        mouse in the lower left corner of the canvas.
        """
        self.panel.set_location(state)

    def set_crosshairs(self, state):
        """
        Enable or disable drawing crosshairs through the mouse cursor when it
        is inside a matplotlib axes.
        """
        self.panel.set_crosshairs(state)

    def set_selection(self, state):
        """
        Enable or disable area selections, where user selects a rectangular
        area of the canvas by left-clicking and dragging the mouse.
        """
        self.panel.set_selection(state)

    def set_zoom(self, state):
        """
        Enable or disable zooming in when the user makes an area selection and
        zooming out again when the user right-clicks.
        """
        self.panel.set_zoom(state)

    def draw(self):
        """
        Draw the associated C{Figure} onto the screen.
        """
        self.panel.draw()


#
# Automatically resizing vectors and matrices
#

class VectorBuffer:
    """
    Manages a Numerical Python vector, automatically growing it as necessary to
    accomodate new entries.
    """
    def __init__(self):
        self.data = Numeric.zeros((16,), Numeric.Float)
        self.nextRow = 0

    def clear(self):
        """
        Zero and reset this buffer without releasing the underlying array.
        """
        self.data[:] = 0.0
        self.nextRow = 0

    def reset(self):
        """
        Zero and reset this buffer, releasing the underlying array.
        """
        self.data = Numeric.zeros((16,), Numeric.Float)
        self.nextRow = 0

    def append(self, point):
        """
        Append a new entry to the end of this buffer's vector.
        """
        nextRow = self.nextRow
        data = self.data

        resize = 1
        if nextRow == data.shape[0]:
            nR = int(Numeric.ceil(nR*1.5))
        else:
            resize = 0

        if resize:
            self.data = Numeric.zeros((nR,), Numeric.Float)
            self.data[0:data.shape[0]] = data

        self.data[nextRow] = point
        self.nextRow += 1

    def getData(self):
        """
        Returns the current vector or C{None} if the buffer contains no data.
        """
        if self.nextRow == 0:
            return None
        else:
            return self.data[0:self.nextRow]


class MatrixBuffer:
    """
    Manages a Numerical Python matrix, automatically growing it as necessary to
    accomodate new rows of entries.
    """
    def __init__(self):
        self.data = Numeric.zeros((16, 1), Numeric.Float)
        self.nextRow = 0

    def clear(self):
        """
        Zero and reset this buffer without releasing the underlying array.
        """
        self.data[:, :] = 0.0
        self.nextRow = 0

    def reset(self):
        """
        Zero and reset this buffer, releasing the underlying array.
        """
        self.data = Numeric.zeros((16, 1), Numeric.Float)
        self.nextRow = 0

    def append(self, row):
        """
        Append a new row of entries to the end of this buffer's matrix.
        """
        row = Numeric.asarray(row, Numeric.Float)
        nextRow = self.nextRow
        data = self.data
        nPts = row.shape[0]

        if nPts == 0:
            return

        resize = 1
        if nextRow == data.shape[0]:
            nC = data.shape[1]
            nR = int(Numeric.ceil(nR*1.5))
            if nC < nPts:
                nC = nPts
        elif data.shape[1] < nPts:
            nR = data.shape[0]
            nC = nPts
        else:
            resize = 0

        if resize:
            self.data = Numeric.zeros((nR, nC), Numeric.Float)
            rowEnd, colEnd = data.shape
            self.data[0:rowEnd, 0:colEnd] = data

        self.data[nextRow, 0:nPts] = row
        self.nextRow += 1

    def getData(self):
        """
        Returns the current matrix or C{None} if the buffer contains no data.
        """
        if self.nextRow == 0:
            return None
        else:
            return self.data[0:self.nextRow, :]


#
# Utility functions used by the StripCharter
#

def make_delta_bbox(X1, Y1, X2, Y2):
    """
    Returns a C{Bbox} describing the range of difference between two sets of X
    and Y coordinates.
    """
    return make_bbox(get_delta(X1, X2), get_delta(Y1, Y2))


def get_delta(X1, X2):
    """
    Returns the vector of contiguous, different points between two vectors.
    """
    n1 = X1.shape[0]
    n2 = X2.shape[0]

    if n1 < n2:
        return X2[n1:]
    elif n1 == n2:
        # shape is no longer a reliable indicator of change, so assume things
        # are different
        return X2
    else:
        return X2


def make_bbox(X, Y):
    """
    Returns a C{Bbox} that contains the supplied sets of X and Y coordinates.
    """
    if X is None or X.shape[0] == 0:
        x1 = x2 = 0.0
    else:
        x1 = min(X)
        x2 = max(X)

    if Y is None or Y.shape[0] == 0:
        y1 = y2 = 0.0
    else:
        y1 = min(Y)
        y2 = max(Y)

    return Bbox(Point(Value(x1), Value(y1)), Point(Value(x2), Value(y2)))


#
# Strip-charts lines using a matplotlib axes
#

class StripCharter:
    """
    Plots and updates lines on a matplotlib C{Axes}.
    """
    def __init__(self, axes):
        """
        Create a new C{StripCharter} associated with a matplotlib C{axes}.
        """
        self.axes = axes
        self.channels = []
        self.lines = {}

    def setChannels(self, channels):
        """
        Specify the data-providers of the lines to be plotted and updated.
        """
        self.lines = None
        self.channels = channels[:]

        # minimal Axes.cla()
        self.axes.legend_ = None
        self.axes.lines = []

    def update(self):
        """
        Redraw the associated axes with updated lines if any of the channels'
        data has changed.
        """
        axes = self.axes
        figureCanvas = axes.figure.canvas
        zoomed = figureCanvas.zoomed(axes)

        redraw = 0
        if self.lines is None:
            self._create_plot()
            redraw = 1
        else:
            for channel in self.channels:
                redraw = self._update_channel(channel, zoomed) or redraw

        if redraw:
            if not zoomed:
                axes.autoscale_view()
            figureCanvas.draw()

    def _create_plot(self):
        """
        Initially plot the lines corresponding to the data-providers.
        """
        self.lines = {}
        axes = self.axes

        styleGen = _process_plot_var_args()
        for channel in self.channels:
            self._plot_channel(channel, styleGen)

        self.axes.legend(pad=0.1, axespad=0.0, numpoints=2, handlelen=0.02,
            handletextsep=0.01, prop=FontProperties(size='xx-small'))

#        # Draw the legend on the figure instead...
#        handles = [self.lines[x] for x in self.channels]
#        labels = [x._label for x in handles]
#        self.axes.figure.legend(handles, labels, 'upper right',
#            pad=0.1, handlelen=0.02, handletextsep=0.01, numpoints=2,
#            prop=FontProperties(size='xx-small'))

    def _plot_channel(self, channel, styleGen):
        """
        Initially plot a line corresponding to one of the data-providers.
        """
        x = channel.getX()
        y = channel.getY()
        if x is None or y is None:
            x = y = Numeric.zeros((0,), Numeric.Float)
        lineStyle = channel.getLineStyle()

        if lineStyle:
            line = styleGen(x, y, channel.lineStyle).next()
        else:
            line = styleGen(x, y).next()

        line.set_label(channel.getLabel())
        self.axes.add_line(line)
        self.lines[channel] = line

    def _update_channel(self, channel, zoomed):
        """
        Replot a line corresponding to one of the data-providers if the data
        has changed.
        """
        if channel.hasChanged():
            channel.setChanged(False)
        else:
            return False

        axes = self.axes
        line = self.lines[channel]
        newX = channel.getX()
        newY = channel.getY()

        if newX is None or newY is None:
            return False

        oldX = line._x
        oldY = line._y

        x, y = newX, newY
        line.set_data(x, y)
        if line.get_transform() != axes.transData:
            xys = axes._get_verts_in_data_coords(
                line.get_transform(), zip(x, y))
            x = Numeric.array([a for (a, b) in xys])
            y = Numeric.array([b for (a, b) in xys])
        axes.update_datalim_numerix(x, y)

        if zoomed:
            return axes.viewLim.overlaps(
                make_delta_bbox(oldX, oldY, newX, newY))
        else:
            return True


#
# Data-providing interface to the StripCharter
#

class Channel:
    """
    Provides data for a C{StripCharter} to plot.  Subclasses of C{Channel}
    override the template methods C{getX()} and C{getY()} to provide plot data
    and call C{setChanged(True)} when that data has changed.
    """
    def __init__(self, name, lineStyle=None):
        """
        Creates a new C{Channel} with the matplotlib label C{name}.  If the
        keyword argument C{lineStyle} is provided, it will be used as the style
        string when the line is plotted.
        """
        self.name = name
        self.lineStyle = lineStyle
        self.changed = False

    def getLabel(self):
        """
        Returns the matplotlib label for this channel of data.
        """
        return self.name

    def getLineStyle(self):
        """
        Returns the style string to use when the line is plotted, or C{None} to
        use an automatically generated style.
        """
        return self.lineStyle

    def hasChanged(self):
        """
        Returns a boolean indicating if the line data has changed.
        """
        return self.changed

    def setChanged(self, changed):
        """
        Sets the change indicator to the boolean value C{changed}.

        @note: C{StripCharter} instances call this method after detecting a
        change, so a C{Channel} cannot be shared among multiple charts.
        """
        self.changed = changed

    def getX(self):
        """
        Template method that returns the vector of X axis data or C{None} if
        there is no data available.
        """
        return None

    def getY(self):
        """
        Template method that returns the vector of Y axis data or C{None} if
        there is no data available.
        """
        return None

