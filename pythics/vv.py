#
#  Copyright 2012 Brian R. D'Urso
#
#  This file is part of Python Instrument Control System, also known as Pythics.
#
#  Pythics is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Pythics is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Pythics.  If not, see <http://www.gnu.org/licenses/>.
#


#
# load libraries
#
import multiprocessing

try:
    import numpy as np
    numpy_loaded = True
except:
    logger = multiprocessing.get_logger()
    logger.warning("'numpy' is not available.")
    numpy_loaded = False

from PyQt4 import QtGui, QtCore
import visvis as vv

import pythics.lib
import pythics.libcontrol
import pythics.vv_proxies as proxies


#
# Plot2D: plot panel with multiple plot types
#
class Plot2D(pythics.libcontrol.Control):
    """To be written.

    HTML Parameters: None
    """
    def __init__(self, parent, action=None, **kwargs):
        pythics.libcontrol.Control.__init__(self, parent,
                                            action=None,
                                            save=False,
                                            **kwargs)
        Figure = parent.main_window.vv_app.GetFigureClass()
        self.figure = Figure(parent)
        self.widget = self.figure._widget
        #vv.figure(self.figure)
        self.axes = vv.subplot(1,1,1)
        self.items = dict()
        #self.set_plot_properties(kwargs)

    def set_plot_properties(self, **kwargs):
        # make this the current figure
        vv.figure(self.figure)
        if 'antialiasing' in kwargs:
            value = kwargs.pop('antialiasing')
            p_w.setAntialiasing(value)
        if 'background' in kwargs:
            value = kwargs.pop('background')
            p_w.setBackground(value)
        if 'aspect_ratio' in kwargs:
            # 'auto', 'equal', or a number
            value = kwargs.pop('aspect_ratio')
            if value == 'auto':
                self.axes.daspectAuto = True
            elif value == 'equal':
                self.axes.daspectAuto = False
                self.axes.daspect = (1, 1)
        if 'x_auto_scale' in kwargs:
            value = kwargs.pop('x_auto_scale')
        if 'y_auto_scale' in kwargs:
            value = kwargs.pop('y_auto_scale')
        if 'x_scale' in kwargs:
            value = kwargs.pop('x_scale')
        if 'y_scale' in kwargs:
            value = kwargs.pop('y_scale')
        if 'title' in kwargs:
            value = kwargs.pop('title')
            vv.title(value)
        if 'x_label' in kwargs:
            value = kwargs.pop('x_label')
            self.axes.axis.xLabel = value
        if 'y_label' in kwargs:
            value = kwargs.pop('y_label')
            self.axes.axis.yLabel = value
        if 'x_grid' in kwargs:
            value = kwargs.pop('x_grid')
            p_i.showGrid(x=value)
        if 'y_grid' in kwargs:
            value = kwargs.pop('y_grid')
            p_i.showGrid(y=value)
        # SHOULD RAISE AN EXCEPTION OR AT LEAST A WARNING IF ANY kwargs ARE LEFT

    def set_curve_properties(self, e, **kwargs):
        if 'line_color' in kwargs:
            value = kwargs.pop('line_color')
            pen = e.pen()
            pen.setColor(QtGui.QColor(value))
            e.setPen(pen)
        if 'line_width' in kwargs:
            value = kwargs.pop('line_width')
            pen = e.pen()
            pen.setWidth(value)
            e.setPen(pen)
        if 'style' in kwargs:
            value = kwargs.pop('style')
            # need to lookup the style
            e.setStyle(value)
        if 'symbol_shape' in kwargs:
            value = kwargs.pop('symbol_shape')
            # need to lookup the symbol
            self.symbols
            #c.setSymbol(value)
        if 'symbol_fill_color' in kwargs:
            value = kwargs.pop('symbol_fill_color')
            # need to lookup the symbol
            self.symbols
            #c.setSymbol(value)
        # SHOULD RAISE AN EXCEPTION OR AT LEAST A WARNING IF ANY kwargs ARE LEFT

    def delete_item(self, key):
        (item_type, e) = self.items[key]
        if item_type == 'curve':
            e.detach()

    def generate_proxy(self, *args):
        return proxies.Plot2DProxy(*args)

    #---------------------------------------------------
    # methods below used only for access by action proxy

    @pythics.libcontrol.proxy_call_no_return_
    def _call_clear(self):
        self.axes.Clear()
        self.items = dict()

    @pythics.libcontrol.proxy_call_no_return_
    def _call_new_item(self, key, item_type, *args, **kwargs):
        if key in self.items:
            # an item with that key already exists
            # should raise an exception or warning
            pass
        else:
            # make this the current figure
            vv.figure(self.figure)
            # create a new dictionary of options for plotting
            plot_kwargs = dict()
            if 'line_width' in kwargs:
                value = kwargs.pop('line_width')
                plot_kwargs['lw'] = value
            if 'marker_width' in kwargs:
                value = kwargs.pop('marker_width')
                plot_kwargs['mw'] = value
            if 'marker_edge_width' in kwargs:
                value = kwargs.pop('marker_edge_width')
                plot_kwargs['mew'] = value
            if 'line_color' in kwargs:
                value = kwargs.pop('line_color')
                plot_kwargs['lc'] = value
            if 'marker_color' in kwargs:
                value = kwargs.pop('marker_color')
                plot_kwargs['mc'] = value
            if 'marker_edge_color' in kwargs:
                value = kwargs.pop('marker_edge_color')
                plot_kwargs['mec'] = value
            if 'line_style' in kwargs:
                value = kwargs.pop('line_style')
                plot_kwargs['ls'] = value
            if 'marker_style' in kwargs:
                value = kwargs.pop('marker_style')
                plot_kwargs['ms'] = value
            if 'adjust_axes' in kwargs:
                value = kwargs.pop('adjust_axes')
                plot_kwargs['axesAdjust'] = value
            # create the plot item
            if item_type == 'circular':
                data = pythics.lib.CircularArray(cols=2, length=kwargs['length'])
                item = vv.plot(np.array([]), np.array([]), axes=self.axes, **plot_kwargs)
            elif item_type == 'growable':
                data = pythics.lib.GrowableArray(cols=2, length=kwargs['length'])
                item = vv.plot(np.array([]), np.array([]), axes=self.axes, **plot_kwargs)
            else:
                data = np.array([])
                item = vv.plot(np.array([]), np.array([]), axes=self.axes, **plot_kwargs)
            self.items[key] = (item_type, data, item)

    @pythics.libcontrol.proxy_call_no_return_
    def _call_delete_item(self, key):
        self.items.pop(key)

    @pythics.libcontrol.proxy_call_no_return_
    def _call_clear_item_data(self, key):
        (item_type, old_data, item) = self.items[key]
        if item_type == 'circular' or item_type == 'growable':
            old_data.clear()
            #item.setData(old_data[:])
            item.setData(np.array([[0,0]]))
        else:
            data = np.array([])
            item.setData(np.array([[0,0]]))

    @pythics.libcontrol.proxy_call_no_return_
    def _call_set_item_data(self, key, data, rescale=True):
        (item_type, old_data, item) = self.items[key]
        if item_type == 'circular' or item_type == 'growable':
            old_data.clear()
            old_data.append(data)
            item.SetPoints(old_data[:])
        else:
            item.SetPoints(data)
        if rescale:
            self.axes.SetLimits()

    @pythics.libcontrol.proxy_call_no_return_
    def _call_append_item_data(self, key, data, rescale=True):
        (item_type, old_data, item) = self.items[key]
        if item_type == 'circular' or item_type == 'growable':
            old_data.append(data)
            item.SetPoints(old_data[:])
        else:
            pass # ERROR
        if rescale:
            self.axes.SetLimits()

    @pythics.libcontrol.proxy_call_no_return_
    def _call_set_item_properties(self, key, *args, **kwargs):
        (item_type, e) = self.items[key]
        if item_type == 'curve':
            e.setData(kwargs.pop('x'), kwargs.pop('y'))
        elif item_type == 'image':
            #data = Qwt.QwtMatrixRasterData()
            #data = Qwt.QwtRasterData()
            #data.setValueMatrix(kwargs.pop('z'))
            #e.setData(data)
            pass

    @pythics.libcontrol.proxy_call_no_return_
    def _call_set_plot_properties(self, **kwargs):
        self.set_plot_properties(**kwargs)
