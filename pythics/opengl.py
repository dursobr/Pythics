# -*- coding: utf-8 -*-
#
# Copyright 2017 - 2019 Brian R. D'Urso
#
# This file is part of Python Instrument Control System, also known as Pythics.
#
# Pythics is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pythics is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pythics.  If not, see <http://www.gnu.org/licenses/>.
#


#
# load libraries
#
import struct

import numpy as np

from pythics.settings import _TRY_PYSIDE
try:
    if not _TRY_PYSIDE:
        raise ImportError()
    import PySide2.QtCore as _QtCore
    import PySide2.QtGui as _QtGui
    import PySide2.QtWidgets as _QtWidgets
    import PySide2.QtPrintSupport as _QtPrintSupport
    QtCore = _QtCore
    QtGui = _QtGui
    QtWidgets = _QtWidgets
    QtPrintSupport = _QtPrintSupport
    Signal = QtCore.Signal
    Slot = QtCore.Slot
    Property = QtCore.Property
    USES_PYSIDE = True
except ImportError:
    import PyQt5.QtCore as _QtCore
    import PyQt5.QtGui as _QtGui
    import PyQt5.QtWidgets as _QtWidgets
    import PyQt5.QtPrintSupport as _QtPrintSupport
    QtCore = _QtCore
    QtGui = _QtGui
    QtWidgets = _QtWidgets
    QtPrintSupport = _QtPrintSupport
    Signal = QtCore.pyqtSignal
    Slot = QtCore.pyqtSlot
    Property = QtCore.pyqtProperty
    USES_PYSIDE = False

try:
    if USES_PYSIDE:
        from PySide import QtOpenGL
    else:
        from PyQt5 import QtOpenGL, QtWidgets
        #from OpenGL import GL
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False

import pythics.libcontrol


#
# ScopePlot
#
class ScopePlot(pythics.libcontrol.Control):
    """An oscilloscope-like plot for real time display of 2-dimensional curves,
    with OpenGL-accelerated drawing if available.

    HTML parameters:

      *antialias*: [ *True* (default) | *False* ]
        Render curves antialiased. This does not typically slow down rendering
        significantly but looks much nicer.

      *aspect_locked*: [ *True* | *False* (default) ]
        Whether to lock the aspect ratio of the plot coordinate system to 1:1.

      *grid_color*: (r, g, b, a)
        An RGBA tuple specifying the grid color.

      *grid_line_width*: int (default 1)
        Set the width of the grid lines in pixels.

      *use_opengl*: [ *True* | *False* (default) ]
        Whether to render with opengl for hardware acceleration (if available).
    """
    def __init__(self, parent, antialias=True, aspect_locked=False, grid_color=(200,200,200,255), grid_line_width=1, use_opengl=False, **kwargs):
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        self._widget = ScopePlotCanvas(antialias=antialias, aspect_locked=aspect_locked, grid_color=grid_color, grid_line_width=grid_line_width, use_opengl=use_opengl)

    #---------------------------------------------------
    # methods below used only for access by action proxy

    def new_curve(self, key, **kwargs):
        """Create a new curve or set of points on the plot.

        Arguments:

          *key*: str
            The name you give to this plot item for future access.

        Optional keyword arguments:

          *line_width*: int (default 1)
            Set the width of the lines in pixels. Widths other than 1 may be
            exceedingly slow without opengl hardware acceleration.

          *line_color*:  (r, g, b, a)
            An RGBA tuple specifying the line color.
        """
        self._widget.new_curve(key, **kwargs)

    def set_data(self, key, x, y):
        """Change the data of a plot item.

        Arguments:

          *key*: str
            The name you gave to the plot item when it was created.

          *x*: one-dimensional numpy array 
            X data values.

          *y*: one-dimensional numpy array 
            Y data values.
        """
        self._widget.set_data(key, x, y)

    def freeze(self):
        """Stop redrawing plot until thaw() is called.
        """
        self._widget.freeze()

    def thaw(self):
        """Update and resume redrawing plot (use with freeze()).
        """
        self._widget.thaw()
        self._widget.scene.update()

    def delete(self, key):
        """Delete a plot item.

        Arguments:

          *key*: str
            The name you gave to the plot item when it was created.
        """
        self._widget.delete(key)

    def clear(self):
        """Delete all plot items to clear the plot.
        """
        self._widget.clear()


class ScopePlotCanvas(QtWidgets.QGraphicsView):
    def __init__(self, antialias=False, aspect_locked=False, grid_color=(0,0,0,128), grid_line_width=1.0, use_opengl=False):
        QtWidgets.QGraphicsView.__init__(self)
        self.aspect_locked = aspect_locked
        self.grid_color = grid_color
        self.grid_line_width = grid_line_width

        self.setCacheMode(QtWidgets.QGraphicsView.CacheBackground)
        #self.setFocusPolicy(QtCore.Qt.StrongFocus)
        #self.setFrameShape(QtGui.QFrame.NoFrame)
        self.setFrameShape(QtWidgets.QFrame.Box)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.NoAnchor)
        #self.setTransformationAnchor(QtGui.QGraphicsView.AnchorViewCenter)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
        self.thaw()
        if antialias:
            self.setRenderHints(QtGui.QPainter.Antialiasing)
        self.setOptimizationFlag(self.DontAdjustForAntialiasing, True)
        self.setInteractive(False)
        self.scene = QtWidgets.QGraphicsScene(self)
        self.setScene(self.scene)
        #self.aspect_locked = True
        self.view_rect = QtCore.QRectF(0, 0, 1, 1)
        self.scene.setSceneRect(self.view_rect)
        if self.aspect_locked:
            self.fitInView(self.view_rect, QtCore.Qt.KeepAspectRatio)
        else:
            self.fitInView(self.view_rect, QtCore.Qt.IgnoreAspectRatio)
        if OPENGL_AVAILABLE and use_opengl:
            if antialias:
                qglf = QtOpenGL.QGLFormat()
                qglf.setSampleBuffers(True)
                qglw = QtOpenGL.QGLWidget(qglf)
                self.setViewport(qglw)
            else:
                self.setViewport(QtOpenGL.QGLWidget())

        # dictionary of plot objects such as lines, points, etc.
        self.plot_items = dict()
        
    def freeze(self):
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.NoViewportUpdate)

    def thaw(self):
        #self.setViewportUpdateMode(QtGui.QGraphicsView.MinimalViewportUpdate)
        #self.setViewportUpdateMode(QtGui.QGraphicsView.FullViewportUpdate)
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.BoundingRectViewportUpdate)

    def new_curve(self, key, **kwargs):
        # if a curve with this name already exists, delete it
        if key in self.plot_items:
            self.delete(key)
        # make the new curve
        properties = {"line_color":(255, 0, 0, 255), "line_width":1}
        properties.update(kwargs)
        color = QtGui.QColor.fromRgb(*properties["line_color"])
        pen = QtGui.QPen(color);
        pen.setWidth(properties["line_width"])
        pen.setCosmetic(True)
        x = np.array([0.0, 1.0])
        y = np.array([1.0, 1.0])
        path = arrayToQPath(x, y)
        item = ScopeCurveItem()
        item.setPath(path)
        item.setPen(pen)
        self.scene.addItem(item)
        self.plot_items[key] = item

    def set_data(self, key, x, y):
        item = self.plot_items[key]
        path = arrayToQPath(x, 1.0-y)
        item.setPath(path)

    def delete(self, key):
        item = self.plot_items.pop(key)
        self.scene.removeItem(item)

    def clear(self):
        for item in self.plot_items:
            self.scene.removeItem(item)
        self.plot_items = dict()

    def resizeEvent(self, ev):
        if self.aspect_locked:
            self.fitInView(self.view_rect, QtCore.Qt.KeepAspectRatio)
        else:
            self.fitInView(self.view_rect, QtCore.Qt.IgnoreAspectRatio)

    def drawBackground(self, painter, rect):
        if self.grid_line_width > 0:
            #color = QtGui.QColor(*self.grid_color)
            color = QtGui.QColor.fromRgb(*self.grid_color)
            #pen = QtGui.QPen(color, QtCore.Qt.SolidLine)
            pen = QtGui.QPen(color)
            pen.setWidth(self.grid_line_width)
            pen.setCosmetic(True)
            painter.setPen(pen)
            self.drawBackgroundLine(painter, 0.0, 0.0, 0.0, 1.0)
            self.drawBackgroundLine(painter, 0.1, 0.0, 0.1, 1.0)
            self.drawBackgroundLine(painter, 0.2, 0.0, 0.2, 1.0)
            self.drawBackgroundLine(painter, 0.3, 0.0, 0.3, 1.0)
            self.drawBackgroundLine(painter, 0.4, 0.0, 0.4, 1.0)
            self.drawBackgroundLine(painter, 0.5, 0.0, 0.5, 1.0)
            self.drawBackgroundLine(painter, 0.6, 0.0, 0.6, 1.0)
            self.drawBackgroundLine(painter, 0.7, 0.0, 0.7, 1.0)
            self.drawBackgroundLine(painter, 0.8, 0.0, 0.8, 1.0)
            self.drawBackgroundLine(painter, 0.9, 0.0, 0.9, 1.0)
            self.drawBackgroundLine(painter, 1.0, 0.0, 1.0, 1.0)

            self.drawBackgroundLine(painter, 0.0, 0.0, 1.0, 0.0)
            self.drawBackgroundLine(painter, 0.0, 0.1, 1.0, 0.1)
            self.drawBackgroundLine(painter, 0.0, 0.2, 1.0, 0.2)
            self.drawBackgroundLine(painter, 0.0, 0.3, 1.0, 0.3)
            self.drawBackgroundLine(painter, 0.0, 0.4, 1.0, 0.4)
            self.drawBackgroundLine(painter, 0.0, 0.5, 1.0, 0.5)
            self.drawBackgroundLine(painter, 0.0, 0.6, 1.0, 0.6)
            self.drawBackgroundLine(painter, 0.0, 0.7, 1.0, 0.7)
            self.drawBackgroundLine(painter, 0.0, 0.8, 1.0, 0.8)
            self.drawBackgroundLine(painter, 0.0, 0.9, 1.0, 0.9)
            self.drawBackgroundLine(painter, 0.0, 1.0, 1.0, 1.0)

    def drawBackgroundLine(self, painter, x1, y1, x2, y2):
        line = QtCore.QLineF(x1, y1, x2, y2)
        painter.drawLine(line)


class ScopeCurveItem(QtWidgets.QGraphicsPathItem):
    def boundingRect(self):
        return QtCore.QRectF(-0.1, -0.1, 1.1, 1.1)


"""
Function arrayToQPath is modified from pyqtgraph
Copyright 2010  Luke Campagnola
Distributed under MIT/X11 license. See license.txt for more infomation.
"""

def arrayToQPath(x, y):
    """Convert an array of x,y coordinats to QPainterPath as efficiently as possible.
    The *connect* argument may be 'all', indicating that each point should be
    connected to the next; 'pairs', indicating that each pair of points
    should be connected, or an array of int32 values (0 or 1) indicating
    connections.
    """

    ## Create all vertices in path. The method used below creates a binary format so that all
    ## vertices can be read in at once. This binary format may change in future versions of Qt,
    ## so the original (slower) method is left here for emergencies:
        #path.moveTo(x[0], y[0])
        #if connect == 'all':
            #for i in range(1, y.shape[0]):
                #path.lineTo(x[i], y[i])
        #elif connect == 'pairs':
            #for i in range(1, y.shape[0]):
                #if i%2 == 0:
                    #path.lineTo(x[i], y[i])
                #else:
                    #path.moveTo(x[i], y[i])
        #elif isinstance(connect, np.ndarray):
            #for i in range(1, y.shape[0]):
                #if connect[i] == 1:
                    #path.lineTo(x[i], y[i])
                #else:
                    #path.moveTo(x[i], y[i])
        #else:
            #raise Exception('connect argument must be "all", "pairs", or array')

    ## Speed this up using >> operator
    ## Format is:
    ##    numVerts(i4)   0(i4)
    ##    x(f8)   y(f8)   0(i4)    <-- 0 means this vertex does not connect
    ##    x(f8)   y(f8)   1(i4)    <-- 1 means this vertex connects to the previous vertex
    ##    ...
    ##    0(i4)
    ##
    ## All values are big endian--pack using struct.pack('>d') or struct.pack('>i')

    path = QtGui.QPainterPath()

    n = x.shape[0]
    # create empty array, pad with extra space on either end
    arr = np.empty(n+2, dtype=[('x', '>f8'), ('y', '>f8'), ('c', '>i4')])
    # write first two integers
    byteview = arr.view(dtype=np.ubyte)
    byteview[:12] = 0
    byteview.data[12:20] = struct.pack('>ii', n, 0)
    # Fill array with vertex values
    arr[1:-1]['x'] = x
    arr[1:-1]['y'] = y
    arr[1:-1]['c'] = 1

    # write last 0
    lastInd = 20*(n+1)
    byteview.data[lastInd:lastInd+4] = struct.pack('>i', 0)
    # create datastream object and stream into path

    ## Avoiding this method because QByteArray(str) leaks memory in PySide
    #buf = QtCore.QByteArray(arr.data[12:lastInd+4])  # I think one unnecessary copy happens here

    path.strn = byteview.data[12:lastInd+4] # make sure data doesn't run away
    try:
        buf = QtCore.QByteArray.fromRawData(path.strn)
    except TypeError:
        buf = QtCore.QByteArray(bytes(path.strn))
    ds = QtCore.QDataStream(buf)
    ds >> path

    return path
