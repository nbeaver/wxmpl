#!/usr/bin/env python

#
# Stripcharting Strawman
#

import Numeric
from matplotlib.axes import _process_plot_var_args
from matplotlib.transforms import Bbox, Point, Value
from matplotlib.font_manager import FontProperties


class VectorBuffer:
    def __init__(self):
        self.data = Numeric.zeros((16,), Numeric.Float)
        self.nextRow = 0

    def clear(self):
        self.data[:] = 0.0
        self.nextRow = 0

    def reset(self):
        self.data = Numeric.zeros((16,), Numeric.Float)
        self.nextRow = 0

    def append(self, point):
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
        if self.nextRow == 0:
            return None
        else:
            return self.data[0:self.nextRow]


class MatrixBuffer:
    def __init__(self):
        self.data = Numeric.zeros((16, 1), Numeric.Float)
        self.nextRow = 0

    def clear(self):
        self.data[:, :] = 0.0
        self.nextRow = 0

    def reset(self):
        self.data = Numeric.zeros((16, 1), Numeric.Float)
        self.nextRow = 0

    def append(self, row):
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
        if self.nextRow == 0:
            return None
        else:
            return self.data[0:self.nextRow, :]

#
# TODO: split into StripCharter and PlotUpdater?  This would require two
# classes of Channel (X and X/Y)
#
class StripCharter:
    def __init__(self, axes):
        self.axes = axes
        self.channels = []
        self.lines = {}

    def setChannels(self, channels):
        self.lines = None
        self.channels = channels[:]

    def update(self):
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
        self.lines = {}
        axes = self.axes

        styleGen = _process_plot_var_args()
        for channel in self.channels:
            self._plot_channel(channel, styleGen)

        self.axes.legend(pad=0.1, axespad=0.0, numpoints=2, handlelen=0.02,
            handletextsep=0.01, prop=FontProperties(size='xx-small'))

        # Draw the legend on the figure instead...
        # handles = [self.lines[x] for x in self.channels]
        # labels = [x._label for x in handles]
        # self.axes.figure.legend(handles, labels, 'upper right',
        #     pad=0.1, handlelen=0.02, handletextsep=0.01, numpoints=2,
        #     prop=FontProperties(size='xx-small'))

    def _plot_channel(self, channel, styleGen):
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
        axes = self.axes
        line = self.lines[channel]
        newX = channel.getX()
        newY = channel.getY()
        if newX is None or newY is None:
            newX = newY = Numeric.zeros((0,), Numeric.Float)

        oldX = line._x
        oldY = line._y

        if newX.shape[0] == oldX.shape[0] and newY.shape[0] == oldY.shape[0]:
            return False

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


class StripCharter2(StripCharter):
#    def __init__(self, axes):
#        StripCharter.__init__(self, axes)

    def _create_plot(self):
        from matplotlib.lines import Line2D
        from matplotlib.transforms import Bbox, Point, Value
        from matplotlib.transforms import unit_bbox, get_bbox_transform

        self.lines = {}
        axes = self.axes

#        styleGen = _process_plot_var_args()
#        for channel in self.channels:
#            self._plot_channel(channel, styleGen)
#
#        self.axes.legend(pad=0.1, axespad=0.0, numpoints=2, handlelen=0.02,
#            handletextsep=0.01, prop=FontProperties(size='xx-small'))

        boxin = Bbox(
            Point(axes.viewLim.ll().x(), Value(-20)),
            Point(axes.viewLim.ur().x(), Value(20)))

        height = axes.bbox.ur().y() - axes.bbox.ll().y()
        boxout = Bbox(
            Point(axes.bbox.ll().x(), Value(-1)*height),
            Point(axes.bbox.ur().x(), Value(1) * height))

        transOffset = get_bbox_transform(
            unit_bbox(),
            Bbox( Point( Value(0), axes.bbox.ll().y()),
                  Point( Value(1), axes.bbox.ur().y())
                  ))

        ticklocs = []
        numRows = len(self.channels)
        for i in range(0, numRows):
            channel = self.channels[i]
            x = channel.getX()
            y = channel.getY()
            if x is None or y is None:
                x = y = Numeric.zeros((0,), Numeric.Float)

            trans = get_bbox_transform(boxin, boxout) 
            offset = (i+1.0)/(numRows+1.0)
            trans.set_offset( (0, offset), transOffset)
            line = Line2D(x, y)
            line.set_transform(trans)
            axes.add_line(line)
            ticklocs.append(offset)
            self.lines[channel] = line

        axes.set_yticks(ticklocs)
        axes.set_yticklabels([x.getLabel() for x in self.channels])

        for tick in axes.yaxis.get_major_ticks():
            tick.label1.set_transform(axes.transAxes)
            tick.label2.set_transform(axes.transAxes)        
            tick.tick1line.set_transform(axes.transAxes)
            tick.tick2line.set_transform(axes.transAxes)        
            tick.gridline.set_transform(axes.transAxes)


def make_delta_bbox(X1, Y1, X2, Y2):
    return make_bbox(get_delta(X1, X2), get_delta(Y1, Y2))


def get_delta(X1, X2):
    n1 = X1.shape[0]
    n2 = X2.shape[0]

    if n1 < n2:
        return X2[n1:]
    elif n1 == n2:
        return None
    else:
        return X2


def make_bbox(X, Y):
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
# TODO: add modification tracking
#

class Channel:
    def __init__(self, name, lineStyle=None):
        self.name = name
        self.lineStyle = lineStyle

    def getLabel(self):
        return self.name

    def getLineStyle(self):
        return self.lineStyle

    def getX(self):
        return None

    def getY(self):
        return None

    def update(self, line, force):
        pass # calls line.set_data(x, y), returns True if new data





def main():
    import wx
    import wxmpl
    app = wx.PySimpleApp()
    frame = wxmpl.PlotFrame(None, -1, 'stripchart test')
    chart = StripCharter(frame.get_figure().gca())
    frame.Show(True)
    app.MainLoop()



if __name__ == '__main__':
    main()
