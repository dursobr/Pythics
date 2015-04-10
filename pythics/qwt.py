# -*- coding: utf-8 -*-
#
# Copyright 2008 - 2013 Brian R. D'Urso
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
from PyQt4 import QtCore, QtGui
import PyQt4.Qwt5 as Qwt

import pythics.lib
import pythics.libcontrol


#
# Gauge: shows a progress bar-like display - display only
#
class Gauge(pythics.libcontrol.Control):
    """A progress bar or thermometer-like indicator.

    HTML parameters:

      *save*: [ *True* (default) | *False* ]
        whether to save the value as a default

      *orientation*: [ 'horizontal' (default) | 'vertical' ]

      *scale_position*: [ 'top' | 'bottom' | 'left' | 'right' | *None* (default) ]

      *border_width*: int (default 1)

      *pipe_width*: int (default 10)

      *fill_color*: str (default 'green')

      *alarm_color*: str (default 'red')
    """

    def __init__(self, parent,
                    min=0.0, max=1.0, step=0.0, alarm=None,
                    orientation='horizontal', scale_position=None,
                    border_width=1, pipe_width=10,
                    fill_color='green', alarm_color='red',
                    **kwargs):
        #signals = []
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        # orientation selection
        if orientation == 'horizontal':
            orient = QtCore.Qt.Horizontal
        else:
            orient = QtCore.Qt.Vertical
        # scale position selection
        if scale_position == 'top':
            scalePos = Qwt.QwtThermo.TopScale
        elif scale_position == 'bottom':
            scalePos = Qwt.QwtThermo.BottomScale
        elif scale_position == 'left':
            scalePos = Qwt.QwtThermo.LeftScale
        elif scale_position == 'right':
            scalePos = Qwt.QwtThermo.RightScale
        else:
            scalePos = Qwt.QwtThermo.NoScale
        self._widget = Qwt.QwtThermo()
        self._widget.setOrientation(orient, scalePos)
        self._min = float(min)
        self._max = float(max)
        self._step = float(step)
        self._widget.setScale(self._min, self._max, self._step)
        self._widget.setRange(self._min, self._max)
        self._widget.setBorderWidth(border_width)
        self._widget.setPipeWidth(pipe_width)
        self._widget.setFillColor(QtGui.QColor(fill_color))
        self._widget.setAlarmColor(QtGui.QColor(alarm_color))
        if alarm is not None:
            self._widget.setAlarmLevel(float(alarm))

    def get_parameter(self):
        return self._widget.value()

    def set_parameter(self, value):
        self._widget.setValue(value)

    #---------------------------------------------------
    # methods below used only for access by action proxy

    def pulse(self):
        """Change the Gauge to indicate progress.

        This should be used when there is not a known beginning or end to the
        progress which is indicated. It can be called an arbitrary number of
        times
        """
        self._widget.setValue((self._widget.value() + 0.1) % 1.0)

    def _get_alarm(self):
        """A number which sets the level at which the indicator changes color.

        The Gauge color changes from `fill_color` to `alarm_color` for values
        which exceed the alarm level.
        """
        return self._widget.alarmLevel()

    def _set_alarm(self, value):
        self._widget.setAlarmLevel(value)

    alarm = property(_get_alarm, _set_alarm)

    def _get_range(self):
        return self.min, self.max, self.step

    def _set_range(self, min, max, step):
        self.min = min
        self.max = max
        self.step = step
        self._widget.setScale(min, max, step)
        self._widget.setRange(min, max)

    range = property(_get_range, _set_range)

    def _get_value(self):
        return self._widget.value()

    def _set_value(self, value):
        self._widget.setValue(float(value))

    value = property(_get_value, _set_value)


#
# Knob
#
class Knob(pythics.libcontrol.Control):
    """A control shaped like a know which can be turned to set a value.

    HTML parameters:

      *save*: [ *True* (default) | *False* ]
        whether to save the value as a default

      *tracking*: [ *True* | *False* (default) ]

      *minimum*: float (default 0.0)

      *maximum*: float (default 1.0)

      *step*: float (default 0.0)

      *scale_step*: float (default 0.1)

      *total_angle*: float (default 270.0)

      *knob_width*: int (default 100)

      *border_width*: int (default 1)

      *actions*: dict
        a dictionarly of key:value pairs where the key is the name of a signal
        and value is the function to run when the signal is emitted

        actions in this control:

        ================    ===================================================
        signal              when emitted
        ================    ===================================================
        'valueChanged'      value is changed
        ================    ===================================================
    """
    def __init__(self, parent, tracking=False,
                 minimum=0.0, maximum=1.0, step=0.0, scale_step=0.1,
                 total_angle=270.0, knob_width=100, border_width=1,
                 **kwargs):
        #signals = ['valueChanged']
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        self._widget = Qwt.QwtKnob(parent)
        self._widget.setTracking(tracking)
        self._widget.setScale(float(minimum), float(maximum), float(scale_step))
        self._widget.setRange(float(minimum), float(maximum), float(step))
        self._widget.setTotalAngle(float(total_angle))
        self._widget.setKnobWidth(knob_width)
        self._widget.setBorderWidth(border_width)

    def get_parameter(self):
        return self._widget.value()

    def set_parameter(self, value):
        with self._block_signals():
            self._widget.fitValue(value)

    #---------------------------------------------------
    # methods below used only for access by action proxy

    def _get_value(self):
        return self._widget.value()

    def _set_value(self, value):
        with self._block_signals():
            self._widget.fitValue(value)

    value = property(_get_value, _set_value)


#
# Slider: sliding control
#
class Slider(pythics.libcontrol.Control):
    """A scrollbar-like control for setting a numerical value.

    HTML parameters:

      *save*: [ *True* (default) | *False* ]
        whether to save the value as a default

      *tracking*: [ *True* | *False* (default) ]

      *minimum*: float (default 0.0)

      *maximum*: float (default 1.0)

      *step*: float (default 0.0)

      *scale_step*: float (default 0.1)

      *orientation*: [ 'horizontal' (default) | 'vertical' ]

      *scale_position*: [ 'top' | 'bottom' | 'left' | 'right' | *None* (default) ]

      *style*: [ 'trough' (default) | 'slot' | 'both' ]

      *actions*: dict
        a dictionarly of key:value pairs where the key is the name of a signal
        and value is the function to run when the signal is emitted

        actions in this control:

        ================    ===================================================
        signal              when emitted
        ================    ===================================================
        'valueChanged'      value is changed
        ================    ===================================================
    """
    def __init__(self, parent, tracking=False,
                    minimum=0.0, maximum=1.0, step=0.0, scale_step=0.1,
                    orientation='horizontal', scale_position=None, style='trough',
                 **kwargs):
        #signals = ['valueChanged']
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        # orientation selection
        if orientation == 'horizontal':
            orient = QtCore.Qt.Horizontal
        else:
            orient = QtCore.Qt.Vertical
        # scale position selection
        if scale_position == 'top':
            scalePos = Qwt.QwtSlider.TopScale
        elif scale_position == 'bottom':
            scalePos = Qwt.QwtSlider.BottomScale
        elif scale_position == 'left':
            scalePos = Qwt.QwtSlider.LeftScale
        elif scale_position == 'right':
            scalePos = Qwt.QwtSlider.RightScale
        else:
            scalePos = Qwt.QwtSlider.NoScale
        # background style selection
        if style == 'trough':
            bgStyle = Qwt.QwtSlider.BgTrough
        elif style == 'slot':
            bgStyle = Qwt.QwtSlider.BgSlot
        else:
            bgStyle = Qwt.QwtSlider.BgTrough | Qwt.QwtSlider.BgSlot
        self._widget = Qwt.QwtSlider(parent, orient, scalePos, bgStyle)
        self._widget.setTracking(tracking)
        self._widget.setScale(float(minimum), float(maximum), float(scale_step))
        self._widget.setRange(float(minimum), float(maximum), float(step))

    def get_parameter(self):
        return self._widget.value()

    def set_parameter(self, value):
        with self._block_signals():
            self._widget.fitValue(value)

    #---------------------------------------------------
    # methods below used only for access by action proxy

    def _get_value(self):
        return self._widget.value()

    def _set_value(self, value):
        with self._block_signals():
            self._widget.fitValue(value)

    value = property(_get_value, _set_value)


#
# Chart: scrolled plot panel with multiple line plots
#
class Chart(pythics.libcontrol.Control):
    """Make a strip chart like plot of data with multiple y values for a given
    x value. Additional data can be added efficiently and the user can scroll
    through the chart history with a built-in scrollbar. Note: mpl.Chart2D is
    recommended for new projects.

    HTML parameters:

      *plots*: int (default 1)

      *history*: int (default 1000)
    """
    def __init__(self, parent, plots=1, history=1000, **kwargs):
        #signals = []
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        self._widget = QtGui.QFrame(parent)
        # initialize parameters that only depend on the number of plots
        self._n_plots = plots
        self._history = history
        self._n_plot_range = xrange(self._n_plots)
        # initialize parameters that depend on the number of lines
        self._n_curves_per_plot = list([1])*self._n_plots
        # set up plots
        self._plots = list()
        self._grids = list()
        self._sizer = QtGui.QVBoxLayout()
        for i in self._n_plot_range:
            new_plot = Qwt.QwtPlot()
            new_plot.setCanvasBackground(QtCore.Qt.white)
            new_plot.axisScaleEngine(Qwt.QwtPlot.xBottom).setAttribute(Qwt.QwtScaleEngine.Floating)
            self._sizer.addWidget(new_plot)
            self._plots.append(new_plot)
            new_grid = Qwt.QwtPlotGrid()
            new_grid.enableX(False)
            new_grid.enableY(False)
            new_grid.attach(new_plot)
            self._grids.append(new_grid)
        # set up scoll bar
        self._scroll_to_end = True
        self._pressed = False
        self._scrollbar = QtGui.QScrollBar(QtCore.Qt.Horizontal)
        self._scrollbar.setTracking(True)
        self._sizer.addWidget(self._scrollbar)
        self._scrollbar.valueChanged.connect(self._scroll)
        self._scrollbar.sliderPressed.connect(self._pressed_start)
        self._scrollbar.sliderReleased.connect(self._pressed_end)
        self._widget.setLayout(self._sizer)
        self._requested_span = self._history
        self._curves = list()
        self._init_curve_properties()
        self.clear()

    def _init_curve_properties(self):
        # initialize all curve properties
        #   whenever the number of curves is changed
        self._n_curves_total = sum(self._n_curves_per_plot)
        # first clear out old curves
        for curve in self._curves:
            curve.detach()
        self._curves = list()
        self._pens = list()
        self._symbols = list()
        for i in range(self._n_plots):
            for j in range(self._n_curves_per_plot[i]):
                new_pen = QtGui.QPen(QtCore.Qt.black)
                self._pens.append(new_pen)
                new_curve = Qwt.QwtPlotCurve()
                new_curve.setPen(new_pen)
                self._curves.append(new_curve)
                self._symbols.append(None)
                new_curve.attach(self._plots[i])
        self._data = pythics.lib.RingBuffer(self._history, self._n_curves_total+1)

    def _scroll(self):
        self._scroll_position = self._scrollbar.value()
        self._update_plot()

    def _pressed_start(self):
        self._pressed = True

    def _pressed_end(self):
        self._pressed = False

    def _go_to_end(self):
        return self._scroll_to_end and (not self._pressed)

    def _update_scrollbar(self):
        self._scrollbar.setMaximum(self._data_length-self._scroll_page_size)
        self._scrollbar.setPageStep(self._scroll_page_size)
        self._scrollbar.setValue(self._scroll_position)

    def _update_plot(self):
        start = self._scroll_position
        stop = self._scroll_position + self._scroll_page_size
        data_x_ys = self._data.read(start-self._data_length, stop-self._data_length)
        # all share the same x values
        data_x = data_x_ys[:,0]
        for i in range(self._n_curves_total):
            data_y = data_x_ys[:,i+1]
            if self._curves[i] is not None:
                self._curves[i].setData(data_x, data_y)
        for p in self._plots:
            p.replot()

    #---------------------------------------------------
    # methods below used only for access by action proxy

    def clear(self):
        self._data_length = 0
        self._scroll_page_size = 0
        self._scroll_position = 0
        self._update_scrollbar()
        self._update_plot()

    def append(self, value):
        self._data.write(value)
        self._data_length = min(self._data_length+1, self._history)
        self._scroll_page_size = min(self._requested_span, self._data_length)
        if self._go_to_end():
            self._scroll_position = self._data_length - self._scroll_page_size
        self._update_scrollbar()
        self._update_plot()

    def append_array(self, value):
        self._data.write_array(value)
        self._data_length = min(self._data_length + value.shape[0], self._history)
        self._scroll_page_size = min(self._requested_span, self._data_length)
        if self._scroll_to_end == True:
            self._scroll_position = self._data_length - self._scroll_page_size
        self._update_scrollbar()
        self._update_plot()

    def update(self):
        self._update_plot()

    def _get_data(self):
        return self._data.read(-self._data_length, 0)

    def _set_data(self, value):
        self._data.write_array(value)
        self._data_length = min(value.shape[0], self._history)
        self._scroll_page_size = min(self._requested_span, self._data_length)
        if self._go_to_end():
            self._scroll_position = self._data_length - self._scroll_page_size
        self._update_scrollbar()
        self._update_plot()

    data = property(_get_data, _set_data)

    def _get_scroll_to_end(self):
        return self._scroll_to_end

    def _set_scroll_to_end(self, value):
        self._scroll_to_end = value
        if value == True:
            self._scroll_position = self._data_length - self._scroll_page_size
            self._update_scrollbar()
            self._update_plot()

    def _get_span(self):
        if self._requested_span == self._history:
            return None
        else:
            return self._scroll_page_size

    def _set_span(self, value):
        if value is None:
            self._requested_span = self._history
        else:
            self._requested_span = value
        self._scroll_page_size = min(self._requested_span, self._data_length)
        self._scroll_position = min(self._scroll_position,
                                   self._data_length - self._scroll_page_size)
        self._update_scrollbar()
        self._update_plot()

    span = property(_get_span, _set_span)

    def _get_curves_per_plot(self):
        return self._n_curves_per_plot

    def _set_curves_per_plot(self, value):
        self._n_curves_per_plot = value
        self._init_curve_properties()

    curves_per_plot = property(_get_curves_per_plot, _set_curves_per_plot)

    def set_plot_properties(self, plot=0, **kwargs):
        p = self._plots[plot]
        g = self._grids[plot]
        if 'background' in kwargs:
            value = kwargs.pop('background')
            p.setCanvasBackground(QtGui.QColor(value))
        if 'margin' in kwargs:
            value = kwargs.pop('margin')
            p.setMargin(value)
        if 'title' in kwargs:
            value = kwargs.pop('title')
            p.setTitle(value)
        if 'y_auto_scale' in kwargs:
            value = kwargs.pop('y_auto_scale')
            p.setAxisAutoScale(value)
        if 'y_scale' in kwargs:
            value = kwargs.pop('y_scale')
            # NEED TO CONVERT VALUE TO THE APPROPRIATE TYPE!!!!!!!!!!!!!!!!!
            p.setAxisScale(Qwt.QwtPlot.yLeft, value)
        if 'x_title' in kwargs:
            value = kwargs.pop('x_title')
            p.setAxisTitle(Qwt.QwtPlot.xBottom, value)
        if 'y_title' in kwargs:
            value = kwargs.pop('y_title')
            p.setAxisTitle(Qwt.QwtPlot.yLeft, value)
        if 'x_grid' in kwargs:
            value = kwargs.pop('x_grid')
            g.enableX(value)
        if 'y_grid' in kwargs:
            value = kwargs.pop('y_grid')
            g.enableY(value)
        if 'dashed_grid' in kwargs:
            if kwargs.pop('dashed_grid'):
                grid_line = QtGui.QPen(QtCore.Qt.DashLine)
                g.setPen(grid_line)
        # SHOULD RAISE AN EXCEPTION OR AT LEAST A WARNING IF ANY kwargs ARE LEFT

    def set_curve_properties(self, curve=0, **kwargs):
        c = self._curves[curve]
        if 'line_color' in kwargs:
            value = kwargs.pop('line_color')
            pen = self._pens[curve]
            pen.setColor(QtGui.QColor(value))
            c.setPen(pen)
        if 'line_width' in kwargs:
            value = kwargs.pop('line_width')
            pen = self._pens[curve]
            pen.setWidth(value)
            c.setPen(pen)
        if 'style' in kwargs:
            value = kwargs.pop('style')
            # need to lookup the style
            c.setStyle(value)
        if 'symbol_shape' in kwargs:
            value = kwargs.pop('symbol_shape')
            # need to lookup the symbol
            self._symbols
            #c.setSymbol(value)
        if 'symbol_fill_color' in kwargs:
            value = kwargs.pop('symbol_fill_color')
            # need to lookup the symbol
            self._symbols
            #c.setSymbol(value)
        # SHOULD RAISE AN EXCEPTION OR AT LEAST A WARNING IF ANY kwargs ARE LEFT


#
# Plot: plot panel with multiple plot types
#
class Plot(pythics.libcontrol.Control):
    """2-D plot. mpl.Plot2D is recommended for new projects.

    HTML parameters: None
    """
    def __init__(self, parent, **kwargs):
        #signals = []
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        self._widget = Qwt.QwtPlot()
        self._grid = Qwt.QwtPlotGrid()
        self._grid.enableX(False)
        self._grid.enableY(False)
        self._grid.attach(self._widget)
        self._elements = dict()
        p = self._widget
        g = self._grid
        if 'background' in kwargs:
            value = kwargs.pop('background')
            p.setCanvasBackground(QtGui.QColor(value))
        else:
            # default white background color
            self._widget.setCanvasBackground(QtCore.Qt.white)
        if 'margin' in kwargs:
            value = kwargs.pop('margin')
            p.setMargin(value)
        if 'x_auto_scale' in kwargs:
            value = kwargs.pop('x_auto_scale')
            p.setAxisAutoScale(Qwt.QwtPlot.xBottom, value)
        if 'y_auto_scale' in kwargs:
            value = kwargs.pop('y_auto_scale')
            p.setAxisAutoScale(Qwt.QwtPlot.yLeft, value)
        if 'x_scale' in kwargs:
            value = kwargs.pop('x_scale')
            # NEED TO CONVERT VALUE TO THE APPROPRIATE TYPE!!!!!!!!!!!!!!!!!
            p.setAxisScale(Qwt.QwtPlot.xBottom, value)
        if 'y_scale' in kwargs:
            value = kwargs.pop('y_scale')
            # NEED TO CONVERT VALUE TO THE APPROPRIATE TYPE!!!!!!!!!!!!!!!!!
            p.setAxisScale(Qwt.QwtPlot.yLeft, value)
        if 'title' in kwargs:
            value = kwargs.pop('title')
            p.setTitle(value)
        if 'x_title' in kwargs:
            value = kwargs.pop('x_title')
            p.setAxisTitle(Qwt.QwtPlot.xBottom, value)
        if 'y_title' in kwargs:
            value = kwargs.pop('y_title')
            p.setAxisTitle(Qwt.QwtPlot.yLeft, value)
        if 'x_grid' in kwargs:
            value = kwargs.pop('x_grid')
            g.enableX(value)
        if 'y_grid' in kwargs:
            value = kwargs.pop('y_grid')
            g.enableY(value)
        if 'dashed_grid' in kwargs:
            if kwargs.pop('dashed_grid'):
                grid_line = QtGui.QPen(QtCore.Qt.DashLine)
                g.setPen(grid_line)
        # SHOULD RAISE AN EXCEPTION OR AT LEAST A WARNING IF ANY kwargs ARE LEFT

    def _set_curve_properties(self, e, **kwargs):
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
            self._symbols
            #c.setSymbol(value)
        if 'symbol_fill_color' in kwargs:
            value = kwargs.pop('symbol_fill_color')
            # need to lookup the symbol
            self._symbols
            #c.setSymbol(value)
        # SHOULD RAISE AN EXCEPTION OR AT LEAST A WARNING IF ANY kwargs ARE LEFT

    def _delete_element(self, key):
        (element_type, e) = self._elements[key]
        if element_type == 'curve':
            e.detach()

    #---------------------------------------------------
    # methods below used only for access by action proxy

    def clear(self):
        for k in self._elements.iterkeys():
            self._delete_element(k)
        self._elements = dict()
        self._widget.replot()

    def new_element(self, key, element_type, **kwargs):
        # SHOULD CHECK TO SEE IF AN ELEMENT WITH THIS NAME ALREADY EXISTS!
        if key in self._elements:
            # an element with that key already exists
            # should raise an exception or warning
            pass
        else:
            if element_type == 'curve':
                new_pen = QtGui.QPen(QtCore.Qt.black)
                e = Qwt.QwtPlotCurve()
                e.setPen(new_pen)
                e.attach(self._widget)
                self._set_curve_properties(e, **kwargs)
            elif element_type == 'contours':
                pass
            elif element_type == 'image':
                e = Qwt.QwtPlotSpectrogram()
            self._elements[key] = (element_type, e)

    def delete_element(self, key):
        self._delete_element(key)
        self._elements.pop(key)

    def set_element_data(self, key, *args, **kwargs):
        (element_type, e) = self._elements[key]
        if element_type == 'curve':
            e.setData(kwargs.pop('x'), kwargs.pop('y'))
        elif element_type == 'image':
            #data = Qwt.QwtMatrixRasterData()
            #data = Qwt.QwtRasterData()
            #data.setValueMatrix(kwargs.pop('z'))
            #e.setData(data)
            pass

    def update(self):
        self._widget.replot()

    def set_plot_properties(self, **kwargs):
        p = self._widget
        g = self._grid
        if 'x_top_auto_scale' in kwargs:
            value = kwargs.pop('x_top_auto_scale')
            p.setAxisAutoScale(Qwt.QwtPlot.xTop, value)
        if 'x_bottom_auto_scale' in kwargs:
            value = kwargs.pop('x_bottom_auto_scale')
            p.setAxisAutoScale(Qwt.QwtPlot.xBottom, value)
        if 'y_left_auto_scale' in kwargs:
            value = kwargs.pop('y_left_auto_scale')
            p.setAxisAutoScale(Qwt.QwtPlot.yLeft, value)
        if 'y_right_auto_scale' in kwargs:
            value = kwargs.pop('y_right_auto_scale')
            p.setAxisAutoScale(Qwt.QwtPlot.yRight, value)
        if 'background' in kwargs:
            value = kwargs.pop('background')
            p.setCanvasBackground(QtGui.QColor(value))
        if 'margin' in kwargs:
            value = kwargs.pop('margin')
            p.setMargin(value)
        if 'title' in kwargs:
            value = kwargs.pop('title')
            p.setTitle(value)
        if 'x_title' in kwargs:
            value = kwargs.pop('x_title')
            p.setAxisTitle(Qwt.QwtPlot.xBottom, value)
        if 'y_title' in kwargs:
            value = kwargs.pop('y_title')
            p.setAxisTitle(Qwt.QwtPlot.yLeft, value)
        if 'x_grid' in kwargs:
            value = kwargs.pop('x_grid')
            g.enableX(value)
        if 'y_grid' in kwargs:
            value = kwargs.pop('y_grid')
            g.enableY(value)
        if 'dashed_grid' in kwargs:
            if kwargs.pop('dashed_grid'):
                grid_line = QtGui.QPen(QtCore.Qt.DashLine)
                g.setPen(grid_line)
        # SHOULD RAISE AN EXCEPTION OR AT LEAST A WARNING IF ANY kwargs ARE LEFT

    def set_element_properties(self, key, **kwargs):
        element_type = self._elements[key][0]
        e = self._elements[key][1]
        if element_type == 'curve':
            self._set_curve_properties(e, **kwargs)


#
# PointLinePlot: simplified plot panel for plotting points and lines
#
class PointLinePlot(pythics.libcontrol.Control):
    """Simplified 2-D plot. mpl.Plot2D is recommended for new projects.

    HTML parameters: None
    """
    def __init__(self, parent, **kwargs):
        #signals = []
        pythics.libcontrol.Control.__init__(self, parent, **kwargs)
        self._widget = Qwt.QwtPlot()
        self._grid = Qwt.QwtPlotGrid()
        self._grid.enableX(False)
        self._grid.enableY(False)
        self._grid.attach(self._widget)
        self._curves = list()
        self._last_line_point = (0, 0)
        self._point_elements = dict()
        self._line_elements = dict()
        p = self._widget
        g = self._grid
        self._default_point_properties = dict({
        'line_color': 'black',
        'line_width': 1,
        'fill_color': 'black',
        'symbol': 'circle',
        'size': 3})
        self._default_line_properties = dict({
        'line_color': 'black',
        'line_width': 1})
        if 'background' in kwargs:
            value = kwargs.pop('background')
            p.setCanvasBackground(QtGui.QColor(value))
        else:
            # default white background color
            self._widget.setCanvasBackground(QtCore.Qt.white)
        if 'margin' in kwargs:
            value = kwargs.pop('margin')
            p.setMargin(value)
        if 'x_auto_scale' in kwargs:
            value = kwargs.pop('x_auto_scale')
            p.setAxisAutoScale(Qwt.QwtPlot.xBottom, value)
        if 'y_auto_scale' in kwargs:
            value = kwargs.pop('y_auto_scale')
            p.setAxisAutoScale(Qwt.QwtPlot.yLeft, value)
        if 'x_scale' in kwargs:
            value = kwargs.pop('x_scale')
            # NEED TO CONVERT VALUE TO THE APPROPRIATE TYPE!!!!!!!!!!!!!!!!!
            p.setAxisScale(Qwt.QwtPlot.xBottom, value)
        if 'y_scale' in kwargs:
            value = kwargs.pop('y_scale')
            # NEED TO CONVERT VALUE TO THE APPROPRIATE TYPE!!!!!!!!!!!!!!!!!
            p.setAxisScale(Qwt.QwtPlot.yLeft, value)
        if 'title' in kwargs:
            value = kwargs.pop('title')
            p.setTitle(value)
        if 'x_title' in kwargs:
            value = kwargs.pop('x_title')
            p.setAxisTitle(Qwt.QwtPlot.xBottom, value)
        if 'y_title' in kwargs:
            value = kwargs.pop('y_title')
            p.setAxisTitle(Qwt.QwtPlot.yLeft, value)
        if 'x_grid' in kwargs:
            value = kwargs.pop('x_grid')
            g.enableX(value)
        if 'y_grid' in kwargs:
            value = kwargs.pop('y_grid')
            g.enableY(value)
        if 'dashed_grid' in kwargs:
            if kwargs.pop('dashed_grid'):
                grid_line = QtGui.QPen(QtCore.Qt.DashLine)
                g.setPen(grid_line)
        # SHOULD RAISE AN EXCEPTION OR AT LEAST A WARNING IF ANY kwargs ARE LEFT

    def _set_curve_point_properties(self, curve, properties_in):
        # make a copy of properties so we can pop out elements
        #   without changing the original
        properties = properties_in.copy()
        new_symbol = Qwt.QwtSymbol()
        # pen to draw the symbol outline
        new_pen = QtGui.QPen()
        if 'line_color' in properties:
            value = properties.pop('line_color')
            new_pen.setColor(QtGui.QColor(value))
        if 'line_width' in properties:
            value = properties.pop('line_width')
            new_pen.setWidth(value)
        if 'fill_color' in properties:
            value = properties.pop('fill_color')
            # brush to fill the symbol interior
            new_brush = QtGui.QBrush(QtGui.QColor(value))
        if 'symbol' in properties:
            s = properties.pop('symbol')
            if s == 'square':
                new_symbol.setStyle(Qwt.QwtSymbol.Rect)
            elif s == 'diamond':
                new_symbol.setStyle(Qwt.QwtSymbol.Diamond)
            elif s == 'triangle':
                new_symbol.setStyle(Qwt.QwtSymbol.Triangle)
            elif s == 'triangle_down':
                new_symbol.setStyle(Qwt.QwtSymbol.DTriangle)
            elif s == 'triangle_up':
                new_symbol.setStyle(Qwt.QwtSymbol.UTriangle)
            elif s == 'triangle_left':
                new_symbol.setStyle(Qwt.QwtSymbol.LTriangle)
            elif s == 'triangle_right':
                new_symbol.setStyle(Qwt.QwtSymbol.RTriangle)
            elif s == 'cross':
                new_symbol.setStyle(Qwt.QwtSymbol.Cross)
            elif s == 'cross_x':
                new_symbol.setStyle(Qwt.QwtSymbol.XCross)
            elif s == 'line_horizontal':
                new_symbol.setStyle(Qwt.QwtSymbol.HLine)
            elif s == 'line_vertical':
                new_symbol.setStyle(Qwt.QwtSymbol.VLine)
            elif s == 'star':
                new_symbol.setStyle(Qwt.QwtSymbol.Star1)
            elif s == 'star_2':
                new_symbol.setStyle(Qwt.QwtSymbol.Star2)
            elif s == 'hexagon':
                new_symbol.setStyle(Qwt.QwtSymbol.Hexagon)
            else: # 'circle'
                new_symbol.setStyle(Qwt.QwtSymbol.Ellipse)
        if 'size' in properties:
            value = properties.pop('size')
            new_symbol.setSize(value)
        new_symbol.setPen(new_pen)
        new_symbol.setBrush(new_brush)
        curve.setSymbol(new_symbol)

    def _set_curve_line_properties(self, curve, properties_in):
        # make a copy of properties so we can pop out elements
        #   without changing the original
        properties = properties_in.copy()
        new_pen = QtGui.QPen()
        if 'line_color' in properties:
            value = properties.pop('line_color')
            new_pen.setColor(QtGui.QColor(value))
        if 'line_width' in properties:
            value = properties.pop('line_width')
            new_pen.setWidth(value)
        curve.setPen(new_pen)

    #---------------------------------------------------
    # methods below used only for access by action proxy

    def draw_point(self, point, key=None, **kwargs):
        properties = self._default_point_properties
        properties.update(kwargs)
        new_curve = Qwt.QwtPlotCurve()
        new_curve.setStyle(Qwt.QwtPlotCurve.NoCurve)
        self._set_curve_point_properties(new_curve, properties)
        xs = [point[0]]
        ys = [point[1]]
        new_curve.setData(xs, ys)
        if key != None:
            if key in self._point_elements:
                # remove old curve
                self._point_elements[key][0].detach()
            self._point_elements[key] = (new_curve, xs, ys, properties.copy())
        else:
            self._curves.append(new_curve)
        new_curve.attach(self._widget)
        self._widget.replot()

    def draw_points(self, points, key=None, **kwargs):
        properties = self._default_point_properties
        properties.update(kwargs)
        new_curve = Qwt.QwtPlotCurve()
        new_curve.setStyle(Qwt.QwtPlotCurve.NoCurve)
        self._set_curve_point_properties(new_curve, properties)
        xs = points[:,0]
        ys = points[:,1]
        new_curve.setData(xs, ys)
        if key != None:
            if key in self._point_elements:
                # remove old curve
                self._point_elements[key][0].detach()
            self._point_elements[key] = (new_curve, xs, ys, properties.copy())
        else:
            self._curves.append(new_curve)
        new_curve.attach(self._widget)
        self._widget.replot()

    def change_point_data(self, point, key):
        if key in self._point_elements:
            curve = self._point_elements[key][0]
            xs = [point[0]]
            ys = [point[1]]
            properties = self._point_elements[key][3]
            curve.setData(xs, ys)
            self._point_elements[key] = (curve, xs, ys, properties)
        self._widget.replot()

    def change_points_data(self, points, key):
        if key in self._point_elements:
            curve = self._point_elements[key][0]
            xs = points[:,0]
            ys = points[:,1]
            properties = self._point_elements[key][3]
            curve.setData(xs, ys)
            self._point_elements[key] = (curve, xs, ys, properties)
        self._widget.replot()

    def change_point_properties(self, key, **kwargs):
        if key in self._point_elements:
            old_curve, xs, ys, properties = self._point_elements[key]
            properties.update(kwargs)
            old_curve.detach()
            new_curve = Qwt.QwtPlotCurve()
            new_curve.setData(xs, ys)
            new_curve.setStyle(Qwt.QwtPlotCurve.NoCurve)
            self._set_curve_point_properties(new_curve, properties)
            self._point_elements[key] = (new_curve, xs, ys, properties)
            new_curve.attach(self._widget)
            self._widget.replot()

    def delete_points(self, *keys):
        for k in keys:
            if k in self._point_elements:
                self._point_elements[k][0].detach()
                del self._point_elements[k]
        self._widget.replot()

    def draw_line(self, point_1, point_2, key=None, **kwargs):
        properties = self._default_line_properties
        properties.update(kwargs)
        new_curve = Qwt.QwtPlotCurve()
        new_curve.setStyle(Qwt.QwtPlotCurve.Lines)
        self._set_curve_line_properties(new_curve, properties)
        xs = [point_1[0], point_2[0]]
        ys = [point_1[1], point_2[1]]
        new_curve.setData(xs, ys)
        self._last_line_point = point_2
        if key != None:
            if key in self._line_elements:
                # remove old curve
                self._line_elements[key][0].detach()
            self._line_elements[key] = (new_curve, xs, ys, properties.copy())
        else:
            self._curves.append(new_curve)
        new_curve.attach(self._widget)
        self._widget.replot()

    def draw_lines(self, points, key=None, **kwargs):
        properties = self._default_line_properties
        properties.update(kwargs)
        new_curve = Qwt.QwtPlotCurve()
        new_curve.setStyle(Qwt.QwtPlotCurve.Lines)
        self._set_curve_line_properties(new_curve, properties)
        xs = points[:,0]
        ys = points[:,1]
        new_curve.setData(xs, ys)
        self._last_line_point = points[-1]
        if key != None:
            if key in self._line_elements:
                # remove old curve
                self._line_elements[key][0].detach()
            self._line_elements[key] = (new_curve, xs, ys, properties.copy())
        else:
            self._curves.append(new_curve)
        new_curve.attach(self._widget)
        self._widget.replot()

    def draw_line_to(self, point, key=None, **kwargs):
        properties = self._default_line_properties
        properties.update(kwargs)
        new_curve = Qwt.QwtPlotCurve()
        new_curve.setStyle(Qwt.QwtPlotCurve.Lines)
        self._set_curve_line_properties(new_curve, properties)
        xs = [self._last_line_point[0], point[0]]
        ys = [self._last_line_point[1], point[1]]
        new_curve.setData(xs, ys)
        self._last_line_point = point
        if key != None:
            if key in self._line_elements:
                # remove old curve
                self._line_elements[key][0].detach()
            self._line_elements[key] = (new_curve, xs, ys, properties.copy())
        else:
            self._curves.append(new_curve)
        new_curve.attach(self._widget)
        self._widget.replot()

    def change_line_data(self, point_1, point_2, key):
        if key in self._line_elements:
            curve = self._line_elements[key][0]
            xs = [point_1[0], point_2[0]]
            ys = [point_1[1], point_2[1]]
            properties = self._line_elements[key][3]
            curve.setData(xs, ys)
            self._line_elements[key] = (curve, xs, ys, properties)
        self._widget.replot()

    def change_lines_data(self, points, key):
        if key in self._line_elements:
            curve = self._line_elements[key][0]
            xs = points[:,0]
            ys = points[:,1]
            properties = self._line_elements[key][3]
            curve.setData(xs, ys)
            self._line_elements[key] = (curve, xs, ys, properties)
        self._widget.replot()

    def change_line_properties(self, key, **kwargs):
        if key in self._line_elements:
            old_curve, xs, ys, properties = self._line_elements[key]
            properties.update(kwargs)
            old_curve.detach()
            new_curve = Qwt.QwtPlotCurve()
            new_curve.setData(xs, ys)
            new_curve.setStyle(Qwt.QwtPlotCurve.Lines)
            self._set_curve_line_properties(new_curve, properties)
            self._line_elements[key] = (new_curve, xs, ys, properties)
            new_curve.attach(self._widget)
            self._widget.replot()

    def start_line(self, point):
        self._last_line_point = point

    def delete_lines(self, *keys):
        for k in keys:
            if k in self._line_elements:
                self._line_elements[k][0].detach()
                del self._line_elements[k]
        self._widget.replot()

    def clear(self):
        for c in self._curves:
            c.detach()
        self._curves = list()
        for c in self._point_elements.itervalues():
            c[0].detach()
        self._point_elements.clear()
        for c in self._line_elements.itervalues():
            c[0].detach()
        self._line_elements.clear()
        self._widget.replot()

    def set_plot_properties(self, **kwargs):
        p = self._widget
        g = self._grid
        if 'background' in kwargs:
            value = kwargs.pop('background')
            p.setCanvasBackground(QtGui.QColor(value))
        if 'margin' in kwargs:
            value = kwargs.pop('margin')
            p.setMargin(value)
        if 'x_auto_scale' in kwargs:
            value = kwargs.pop('x_auto_scale')
            p.setAxisAutoScale(Qwt.QwtPlot.xBottom, value)
        if 'y_auto_scale' in kwargs:
            value = kwargs.pop('y_auto_scale')
            p.setAxisAutoScale(Qwt.QwtPlot.yLeft, value)
        if 'x_scale' in kwargs:
            value = kwargs.pop('x_scale')
            # NEED TO CONVERT VALUE TO THE APPROPRIATE TYPE!!!!!!!!!!!!!!!!!
            p.setAxisScale(Qwt.QwtPlot.xBottom, value)
        if 'y_scale' in kwargs:
            value = kwargs.pop('y_scale')
            # NEED TO CONVERT VALUE TO THE APPROPRIATE TYPE!!!!!!!!!!!!!!!!!
            p.setAxisScale(Qwt.QwtPlot.yLeft, value)
        if 'title' in kwargs:
            value = kwargs.pop('title')
            p.setTitle(value)
        if 'x_title' in kwargs:
            value = kwargs.pop('x_title')
            p.setAxisTitle(Qwt.QwtPlot.xBottom, value)
        if 'y_title' in kwargs:
            value = kwargs.pop('y_title')
            p.setAxisTitle(Qwt.QwtPlot.yLeft, value)
        if 'x_grid' in kwargs:
            value = kwargs.pop('x_grid')
            g.enableX(value)
        if 'y_grid' in kwargs:
            value = kwargs.pop('y_grid')
            g.enableY(value)
        if 'dashed_grid' in kwargs:
            if kwargs.pop('dashed_grid'):
                grid_line = QtGui.QPen(QtCore.Qt.DashLine)
                g.setPen(grid_line)
        # SHOULD RAISE AN EXCEPTION OR AT LEAST A WARNING IF ANY kwargs ARE LEFT
