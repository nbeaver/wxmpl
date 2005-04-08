#!/usr/bin/env python

# Name: wxmpl-plotit
# Purpose: Experiment data visualization
# Author: Ken McIvor <mcivor@iit.edu>
#
# Copyright 2004-2005 Illinois Institute of Technology
#
# See the file "LICENSE" for information on usage and redistribution
# of this file, and for a DISCLAIMER OF ALL WARRANTIES.


__version__ = '1.0'


import Numeric
import os.path
import sys
import xdp
import wx
from wxmpl import PlotFrame


class PlotApp(wx.App):
    def __init__(self, xExpr, yExpr, plotFiles, **kwds):
        self.xExpr = xExpr
        self.yExpr = yExpr
        self.plotFiles = plotFiles
        wx.App.__init__(self, **kwds)

    def OnInit(self):
        frame = PlotFrame(None, -1, 'plotit')
        axes = frame.get_figure().gca()

        for plt in self.plotFiles:
            axes.plot(plt.x, plt.y, label=os.path.basename(plt.fileName))

        axes.legend()

        frame.Show(1)
        self.SetTopWindow(frame)
        return 1

#
# Command-Line Part
#

def fatalError(msg):
    sys.stderr.write('Error: ')
    sys.stderr.write(str(msg))
    sys.stderr.write('\n')
    sys.exit(1)


def fatalIOError(err):
    if isinstance(err, IOError) and err.strerror and err.filename:
        err = '%s: %s' % (err.strerror, err.filename)
    fatalError(err)


def ParseArguments(args):
    try:
        from optik import OptionParser
    except ImportError:
        try:
            from optparse import OptionParser
        except ImportError:
            fatalError(
'This program requires Optik, availible from http://optik.sourceforge.net/\n')

    USAGE = '%prog X-EXPR Y-EXPR FILE FILE...'
    VERSION = '%prog ' + __version__ + ', by Ken McIvor <mcivken@iit.edu>'
    parser = OptionParser(usage=USAGE, version=VERSION)

    opts, args = parser.parse_args(args)
    if len(args) < 3:
        parser.print_usage()
        sys.exit(1)

    return opts, (args[0], args[1], args[2:])


class PlotFile:
    class EvaluationError(Exception):
        pass

    def __init__(self, fileName, xExpr, yExpr):
        self.fileName = fileName
        self.header, self.data = xdp.io.readFile(fileName)

        try:
            self.x = self.data.evaluate(xExpr)
        except xdp.ColumnNameError, e:
            err = 'invalid column %s' % str(e)
            raise PlotFile.EvaluationError(
                'while evaluating "%s" in file %s: %s'
                % (xExpr, fileName, err))
        except Exception, e:
            raise PlotFile.EvaluationError(
                'while evaluating "%s" in file %s: %s'
                % (xExpr, fileName, str(e)))

        if not isinstance(self.x, Numeric.ArrayType) or len(self.x.shape) != 1:
            raise PlotFile.EvaluationError(('X expression "%s" does not'
                + ' evaluate to a one-dimensional Numeric array in file %s')
                % (xExpr, fileName))

        try:
            self.y = self.data.evaluate(yExpr)
        except xdp.ColumnNameError, e:
            err = 'invalid column %s' % str(e)
            raise PlotFile.EvaluationError(
                'while evaluating "%s" in file %s: %s'
                % (yExpr, fileName, err))
        except Exception, e:
            raise PlotFile.EvaluationError(
                'while evaluating "%s" in file %s: %s'
                % (yExpr, fileName, str(e)))

        if not isinstance(self.y, Numeric.ArrayType) or len(self.y.shape) != 1:
            raise PlotFile.EvaluationError(('Y expression "%s" does not'
                + ' evaluate to a one-dimensional Numeric array in file %s')
                % (yExpr, fileName))

        if self.x.shape != self.y.shape:
            raise PlotFile.EvaluationError(
            'X and Y expressions in %s do not have the same number of elements'
                % fileName)


def main(options, arguments):
    xExpr, yExpr, inputFileNames = arguments

    try:
        files = [ PlotFile(name, xExpr, yExpr) for name in inputFileNames ]
    except IOError, e:
        fatalIOError(e)
    except PlotFile.EvaluationError, e:
        fatalError(e)

    app = PlotApp(xExpr, yExpr, files, redirect=0)
    app.MainLoop()


if __name__ == '__main__':
    options, args = ParseArguments(sys.argv[1:])
    main(options, args)
