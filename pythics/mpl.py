# -*- coding: utf-8 -*-
#
# Copyright 2008 - 2019 Brian R. D'Urso
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
import multiprocessing

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

import matplotlib
import matplotlib.figure
from matplotlib.backends.backend_qt5agg import (FigureCanvas, NavigationToolbar2QT as Toolbar)
# the following import is necessary for 3-D plots in matplotlib although it is
#   not directly used
from mpl_toolkits.mplot3d import Axes3D

import pythics.lib
import pythics.libcontrol


class Canvas(pythics.libcontrol.MPLControl):
    """Gives essentially complete acess to the matplotlib object oriented (OO)
    API. Use this control when Plot2D and Chart2D don't give all the features
    you need. All interaction with this control, except configuring the
    callbacks, is done through the following three attributes:

    - mpl.Canvas.figure: the matplotlib Figure

    - mpl.Canvas.canvas: The matplotlib FigureCanvas.

    - mpl.Canvas.toolbar: The matplotlib Toolbar (NavigationToolbar2QTAgg).

    If you need access to the matplotlib library, use the use the `import_module` 
    method of a Main control rather than directly importing the library to allow 
    the objects to be created in the correct process.

    See the examples and matplotlib documentation for details. Configuration
    of the callback functions (if needed) can be done through html parameters
    or python attributes.

    HTML parameters:

      *toolbar*: [ *True* (default) | *False* ]
        Whether to add a matplotlib toolbar below the plot.

      *actions*: dict
        a dictionarly of key:value pairs where the key is the name of a signal
        and value is the function to run when the signal is emitted

        actions in this control:

        =======================    ============================================
        signal                     when emitted
        =======================    ============================================
        'button_press_event'       a mouse button is pressed
        'button_release_event'     a mouse button is released
        'draw_event'               canvas is redrawn
        'key_press_event'          a key is pressed
        'key_release_event'        a key is released
        'motion_notify_event'      the mouse is moved
        'pick_event'               an object in the canvas is selected
        'resize_event'             the figure canvas is resized
        'scroll_event'             the mouse scroll wheel is rolled
        'figure_enter_event'       the mouse enters a new figure
        'figure_leave_event'       the mouse leaves a figure
        'axes_enter_event'         the mouse enters a new axes
        'axes_leave_event'         the mouse leaves an axe
        =======================    ============================================
    """
    def __init__(self, parent, toolbar=True, **kwargs):
        pythics.libcontrol.MPLControl.__init__(self, parent, **kwargs)
        self._widget = QtWidgets.QFrame()
        vbox = QtWidgets.QVBoxLayout()
        # plot
        self.figure = matplotlib.figure.Figure()
        self.canvas = FigureCanvas(self.figure)
        vbox.addWidget(self.canvas)
        # toolbar
        if toolbar:
            pass
            self.toolbar = Toolbar(self.canvas, self._widget)
            vbox.addWidget(self.toolbar)
        self._mpl_widget = self.canvas
        self._widget.setLayout(vbox)


#
# Plot2D: plot panel with multiple plot types
#
class Plot2D(pythics.libcontrol.MPLControl):
    """An easy to use plotting control for 2-dimensional plotting.
    Right click on the plot to save an image of the plot to a file.

    HTML parameters:

      *projection*: [ 'cartesian' (default) | 'polar' ]
        Set to polar for polar plots (not all plot items supported).

      *actions*: dict
        a dictionarly of key:value pairs where the key is the name of a signal
        and value is the function to run when the signal is emitted

        actions in this control:

        =======================    ============================================
        signal                     when emitted
        =======================    ============================================
        'button_press_event'       a mouse button is pressed
        'button_release_event'     a mouse button is released
        'draw_event'               canvas is redrawn
        'key_press_event'          a key is pressed
        'key_release_event'        a key is released
        'motion_notify_event'      the mouse is moved
        'pick_event'               an object in the canvas is selected
        'resize_event'             the figure canvas is resized
        'scroll_event'             the mouse scroll wheel is rolled
        'figure_enter_event'       the mouse enters a new figure
        'figure_leave_event'       the mouse leaves a figure
        'axes_enter_event'         the mouse enters a new axes
        'axes_leave_event'         the mouse leaves an axe
        =======================    ============================================
    """
    def __init__(self, parent, projection='cartesian', **kwargs):
        pythics.libcontrol.MPLControl.__init__(self, parent, **kwargs)
        self._animated = False
        self._animated_artists = list()
        self._x_autoscale = True
        self._y_autoscale = True
        self._tight_autoscale = False
        self._force_rescale = False
        # dictionary of plot objects such as lines, points, etc.
        self._items = dict()
        # use modified matplotlib canvas to redraw correctly on resize
        self._figure = matplotlib.figure.Figure()
        self._canvas = PythicsMPLCanvas(self, self._figure)
        self._widget = self._canvas
        self._mpl_widget = self._canvas
        if projection == 'polar':
            self._axes = self._figure.add_subplot(111, polar=True)
            self._polar = True
        else:
            self._axes = self._figure.add_subplot(111)
            self._polar = False
        # set_tight_layout doesn't seem to exist, so set tight_layout directly
        #self._figure.set_tight_layout(True)
        self._figure.tight_layout()
        # set plot parameters from parameters passed in html
        self._plot_properties = dict()
        self.set_plot_properties(x_limits='auto',
                                 y_limits='auto',
                                 tight_autoscale=False,
                                 x_scale='linear',
                                 y_scale='linear',
                                 aspect_ratio='auto',
                                 dpi=150)
        # handle resize events
        self._canvas.mpl_connect('resize_event', self._resize)

    def _resize(self, event):
        # Don't use canvas.blit() in here to avoid recursive drawing warnings
        if self._animated:
            self._axes.relim()
            self._axes.autoscale_view(self._tight_autoscale,
                                     self._x_autoscale, self._y_autoscale)
            self._figure.tight_layout()
            self._canvas.draw()
            # update animation background artists
            self._animated_background = self._canvas.copy_from_bbox(self._axes.bbox)
            for k in self._animated_artists:
                self._axes.draw_artist(self._items[k]['mpl_item'])
        else:
            self._canvas.draw()

    def _update(self, rescale='auto'):
        if self._animated:
            if rescale == 'auto':
                if self._x_autoscale or self._y_autoscale:
                    self._full_animated_redraw()
                else:
                    self._fast_animated_redraw()
            elif rescale is True:
                self._full_animated_redraw()
            else:
                self._fast_animated_redraw()
        else:
            if rescale == 'auto':
                if self._x_autoscale or self._y_autoscale:
                    self._axes.relim()
                    self._axes.autoscale_view(self._tight_autoscale,
                                             self._x_autoscale, self._y_autoscale)
                    self._figure.tight_layout()
                    self._canvas.draw()
                    self._force_rescale = False
                else:
                    self._canvas.draw()
            elif rescale is True:
                self._axes.relim()
                self._axes.autoscale_view(self._tight_autoscale,
                                         self._x_autoscale, self._y_autoscale)
                self._figure.tight_layout()
                self._canvas.draw()
                self._force_rescale = False
            else:
                self._canvas.draw()

    def _fast_animated_redraw(self):
        self._canvas.restore_region(self._animated_background)
        for k in self._animated_artists:
            self._axes.draw_artist(self._items[k]['mpl_item'])
        # just redraw the region within the axes
        self._canvas.blit(self._axes.bbox)

    def _full_animated_redraw(self):
        self._axes.relim()
        self._axes.autoscale_view(self._tight_autoscale,
                                 self._x_autoscale, self._y_autoscale)
        self._figure.tight_layout()
        self._canvas.draw()
        
        # update animation background artists
        self._animated_background = self._canvas.copy_from_bbox(self._axes.bbox)
        for k in self._animated_artists:
            self._axes.draw_artist(self._items[k]['mpl_item'])
        # blit entire canvas to ensure complete update
        self._canvas.blit(self._figure.bbox)
        self._force_rescale = False

    #---------------------------------------------------
    # methods below used only for access by action proxy

    def clear(self, redraw=True, rescale='auto'):
        """Delete all plot items to clear the plot.

        Optional keyword arguments:

          *redraw*: [ *True*  (default) | *False* ]
            Whether to redraw the plot after applying changes.

          *rescale*: [ 'auto' (default) | *True* | *False* ]
            Whether to rescale the plot. If 'auto', then only rescale if needed.
        """
        self._axes.clear()
        self._items = dict()
        self._animated_artists = list()
        self._animated = False
        if redraw:
            self._update(rescale)

    def new_curve(self, key, memory='array', length=1000, **kwargs):
        """Create a new curve or set of points on the plot.

        Arguments:

          *key*: str
            The name you give to this plot item for future access.

        Optional keyword arguments:

          *memory*: [ 'array' (default) | 'circular' | 'growable' ]
            Format for plot item data storage which determines how future updates
            to the data can be made.

          *length*: int
            if *memory* == 'circular': The number of elements in the circular array.
            if *memory* == 'growable': The initial number of elements in the array.

          *animated*: [ *True* | *False* (default) ]
            If *True*, try to redraw this item without redrawing the whole plot
            whenever it is updated. This is generally faster if the axes do not
            need to be rescaled, and thus is recommended for plot items that
            are changed frequently.

          *alpha*: ``0 <= scalar <= 1``
            The alpha value for the curve. 0.0 is transparent and 1.0 is opaque.

          *line_color*: any valid color, see more information below
            The color used for drawing lines between points.

          *line_style*: [ '-' | '--' | '-.' | ':' | '' ]

            The following format string characters are accepted to control
            the line style:

            ================    ===============================
            character           description
            ================    ===============================
            ``'-'``             solid line style (default)
            ``'--'``            dashed line style
            ``'-.'``            dash-dot line style
            ``':'``             dotted line style
            ``''``              no line
            ================    ===============================

          *line_width*: float value in points
            The width of lines between points.

          *marker_color*: any valid color, see more information below
            The fill color of markers drawn at the specified points.

          *marker_edge_color*: any valid color, see more information below
            The color of the edges of markers or of the whole marker if the
            marker consists of lines only.

          *marker_edge_width*: float value in points
            The width of the edges of markers or of the lines if the marker
            consists of lines only.

          *marker_style*: any valid marker style, see table below
            The shape of the markers drawn.

            The following format string characters are accepted to control
            the marker style:

            ============================== ===============================
            Value                          Description
            ============================== ===============================
            ``''``                         no marker (default)
            ``'.'``                        point marker
            ``','``                        pixel marker
            ``'o'``                        circle marker
            ``'v'``                        triangle_down marker
            ``'^'``                        triangle_up marker
            ``'<'``                        triangle_left marker
            ``'>'``                        triangle_right marker
            ``'1'``                        tri_down marker
            ``'2'``                        tri_up marker
            ``'3'``                        tri_left marker
            ``'4'``                        tri_right marker
            ``'s'``                        square marker
            ``'p'``                        pentagon marker
            ``'*'``                        star marker
            ``'h'``                        hexagon1 marker
            ``'H'``                        hexagon2 marker
            ``'+'``                        plus marker
            ``'x'``                        x marker
            ``'D'``                        diamond marker
            ``'d'``                        thin_diamond marker
            ``'|'``                        vline marker
            ``'_'``                        hline marker
            (*numsides*, *style*, *angle*) see below
            ============================== ===============================

            The marker can also be a tuple (*numsides*, *style*, *angle*),
            which will create a custom, regular symbol.

                *numsides*:
                  the number of sides

                *style*:
                  the style of the regular symbol:

                  =====   =============================================
                  Value   Description
                  =====   =============================================
                  0       a regular polygon
                  1       a star-like symbol
                  2       an asterisk
                  3       a circle (*numsides* and *angle* is ignored)
                  =====   =============================================

                *angle*:
                  the angle of rotation of the symbol

          *marker_width*: float value in points
            The overall size of the markers draw at the data points.

        Colors:

          The following color abbreviations are supported:

            =====  =======
            Value  Color
            =====  =======
            'b'    blue
            'g'    green
            'r'    red
            'c'    cyan
            'm'    magenta
            'y'    yellow
            'k'    black
            'w'    white
            =====  =======

        In addition, you can specify colors in many other ways, including
        full names (``'green'``), hex strings (``'#008000'``), RGB or
        RGBA tuples (``(0,1,0,1)``) or grayscale intensities as a string (``'0.8'``).
        """
        plot_kwargs = dict()
        if 'alpha' in kwargs:
            value = kwargs.pop('alpha')
            plot_kwargs['alpha'] = value
        if 'line_color' in kwargs:
            value = kwargs.pop('line_color')
            plot_kwargs['color'] = value
        if 'line_style' in kwargs:
            value = kwargs.pop('line_style')
            plot_kwargs['linestyle'] = value
        if 'line_width' in kwargs:
            value = kwargs.pop('line_width')
            plot_kwargs['linewidth'] = value
        if 'marker_color' in kwargs:
            value = kwargs.pop('marker_color')
            plot_kwargs['markerfacecolor'] = value
        if 'marker_edge_color' in kwargs:
            value = kwargs.pop('marker_edge_color')
            plot_kwargs['markeredgecolor'] = value
        if 'marker_edge_width' in kwargs:
            value = kwargs.pop('marker_edge_width')
            plot_kwargs['markeredgewidth'] = value
        if 'marker_style' in kwargs:
            value = kwargs.pop('marker_style')
            plot_kwargs['marker'] = value
        if 'marker_width' in kwargs:
            value = kwargs.pop('marker_width')
            plot_kwargs['markersize'] = value
        # check for an old plot item of the same name
        if key in self._items:
            item = self._items.pop(key)
            item['mpl_item'].remove()
            if key in self._animated_artists:
                self._animated_artists.remove(key)
        # create the plot item
        if memory == 'circular':
            data = pythics.lib.CircularArray(cols=2, length=length)
        elif memory == 'growable':
            data = pythics.lib.GrowableArray(cols=2, length=length)
        else:
            data = np.array([])
        if ('animated' in kwargs) and kwargs.pop('animated'):
            self._animated = True
            item, = self._axes.plot(np.array([]), np.array([]), animated=True,
                                   label=key, **plot_kwargs)
            if len(self._animated_artists) == 0:
                # this is the first animated artist, so we need to set up
                self._animated_background = self._canvas.copy_from_bbox(self._axes.bbox)
            self._animated_artists.append(key)
        else:
            item, = self._axes.plot(np.array([]), np.array([]), label=key,
                                   **plot_kwargs)
        self._items[key] = dict(item_type='curve', mpl_item=item, data=data,
                                memory=memory)
        if len(kwargs) != 0:
            logger = multiprocessing.get_logger()
            logger.warning("Unused arguments in 'new_curve': %s."
                            % str(kwargs))

    def new_image(self, key, **kwargs):
        """Create a new image item on the plot.

        Arguments:

          *key*: str
            The name you give to this plot item for future access.

        Optional keyword arguments:

          *animated*: [ *True* | *False* (default) ]
            If *True*, try to redraw this item without redrawing the whole plot
            whenever it is updated. This is generally faster if the axes do not
            need to be rescaled, and thus is recommended for plot items that
            are changed frequently.

          *alpha*: ``0 <= scalar <= 1``
            The alpha value for the image. 0.0 is transparent and 1.0 is opaque.

          *extent*:  [ *None* (default) | scalars (left, right, bottom, top) ]
            Data limits for the axes. The default assigns zero-based row,
            column indices to the x, y centers of the pixels.

          *interpolation*: str
            Acceptable values are 'none', 'nearest', 'bilinear',
            'bicubic', 'spline16', 'spline36', 'hanning', 'hamming',
            'hermite', 'kaiser', 'quadric', 'catrom', 'gaussian',
            'bessel', 'mitchell', 'sinc', 'lanczos'

          *origin*: [ None | 'upper' | 'lower' ]
            Place the [0,0] index of the array in the upper left or lower left
            corner of the axes.

          *colormap*: str
            The name of a matplotlib colormap for mapping the data value to the
            displayed color at each point.

            *colormap* is ignored when *data* has RGB(A) information

          *c_limits*:  [ 'auto' (default) | scalars (vmin, vmax) ]
            Data limits for the colormap.
        """
        # create a new dictionary of options for plotting
        plot_kwargs = dict()
        if 'alpha' in kwargs:
            value = kwargs.pop('alpha')
            plot_kwargs['alpha'] = value
        if 'extent' in kwargs:
            value = kwargs.pop('extent')
            plot_kwargs['extent'] = value
        if 'interpolation' in kwargs:
            value = kwargs.pop('interpolation')
            plot_kwargs['interpolation'] = value
        if 'origin' in kwargs:
            value = kwargs.pop('origin')
            plot_kwargs['origin'] = value
        if 'colormap' in kwargs:
            value = kwargs.pop('colormap')
            plot_kwargs['cmap'] = value
        if 'c_limits' in kwargs:
            value = kwargs.pop('c_limits')
            if value != 'auto':
                plot_kwargs['vmin'] = value[0]
                plot_kwargs['vmax'] = value[1]
        # check for an old plot item of the same name
        if key in self._items:
            item = self._items.pop(key)
            item['mpl_item'].remove()
            if key in self._animated_artists:
                self._animated_artists.remove(key)
        # create the plot item
        data = np.array([[0]])
        #if self._polar:
        #    # THIS DOESN'T WORK??
        if ('animated' in kwargs) and kwargs.pop('animated'):
            self._animated = True
            item = self._axes.imshow(data, animated=True, label=key,
                                    aspect=self._plot_properties['aspect_ratio'],
                                    **plot_kwargs)
            if len(self._animated_artists) == 0:
                # this is the first animated artist, so we need to set up
                self._animated_background = self._canvas.copy_from_bbox(self._axes.bbox)
            self._animated_artists.append(key)
        else:
            item = self._axes.imshow(data, label=key,
                                    aspect=self._plot_properties['aspect_ratio'],
                                    **plot_kwargs)
        self._items[key] = dict(item_type='image', mpl_item=item, shape=(1, 1))
        if len(kwargs) != 0:
            logger = multiprocessing.get_logger()
            logger.warning("Unused arguments in 'new_image': %s." % str(kwargs))

    def new_colormesh(self, key, X, Y, **kwargs):
        """Create a new pseudocolor mesh item on the plot.

        Arguments:

          *key*: str
            The name you give to this plot item for future access.

          *X*: str
            The x coordinates of the colored quadrilaterals.
            *numpy.meshgrid()* may be helpful for making this.

          *Y*: str
            The x coordinates of the colored quadrilaterals.
            *numpy.meshgrid()* may be helpful for making this.

        Optional keyword arguments:

          *animated*: [ *True* | *False* (default) ]
            If *True*, try to redraw this item without redrawing the whole plot
            whenever it is updated. This is generally faster if the axes do not
            need to be rescaled, and thus is recommended for plot items that
            are changed frequently.

          *alpha*: ``0 <= scalar <= 1``
            The alpha value for the image. 0.0 is transparent and 1.0 is opaque.

          *extent*:  [ *None* (default) | scalars (left, right, bottom, top) ]
            Data limits for the axes. The default assigns zero-based row,
            column indices to the x, y centers of the pixels.

          *interpolation*: str
            Acceptable values are 'none', 'nearest', 'bilinear',
            'bicubic', 'spline16', 'spline36', 'hanning', 'hamming',
            'hermite', 'kaiser', 'quadric', 'catrom', 'gaussian',
            'bessel', 'mitchell', 'sinc', 'lanczos'

          *colormap*: str
            The name of a matplotlib colormap for mapping the data value to the
            displayed color at each point.

            *colormap* is ignored when *data* has RGB(A) information

          *c_limits*:  [ 'auto' (default) | scalars (vmin, vmax) ]
            Data limits for the colormap.
        """
        # create a new dictionary of options for plotting
        plot_kwargs = dict()
        if 'alpha' in kwargs:
            value = kwargs.pop('alpha')
            plot_kwargs['alpha'] = value
        if 'extent' in kwargs:
            value = kwargs.pop('extent')
            plot_kwargs['extent'] = value
        if 'interpolation' in kwargs:
            value = kwargs.pop('interpolation')
            plot_kwargs['interpolation'] = value
        if 'colormap' in kwargs:
            value = kwargs.pop('colormap')
            plot_kwargs['cmap'] = value
        if 'c_limits' in kwargs:
            value = kwargs.pop('c_limits')
            if value != 'auto':
                plot_kwargs['clim'] = value
        # check for an old plot item of the same name
        if key in self._items:
            item = self._items.pop(key)
            item['mpl_item'].remove()
            if key in self._animated_artists:
                self._animated_artists.remove(key)
        # create the plot item
        x_len, y_len = X.shape
        zs = np.zeros((x_len-1, y_len-1))
        if ('animated' in kwargs) and kwargs.pop('animated'):
            self._animated = True
            item = self._axes.pcolor(X, Y, zs, animated=True, label=key,
                                    **plot_kwargs)
            if len(self._animated_artists) == 0:
                # this is the first animated artist, so we need to set up
                self._animated_background = self._canvas.copy_from_bbox(self._axes.bbox)
            self._animated_artists.append(key)
        else:
            item = self._axes.pcolor(X, Y, zs, label=key,
                                    **plot_kwargs)
            #self._axes.pcolormesh(X, Y, zs)
            #self._axes.pcolor(X, Y, zs)
            #self._axes.pcolorfast(X, Y, zs)
        self._items[key] = dict(item_type='colormesh', mpl_item=item)
        if len(kwargs) != 0:
            logger = multiprocessing.get_logger()
            logger.warning("Unused arguments in 'new_colormesh': %s." % str(kwargs))

    def delete(self, key, redraw=True, rescale='auto'):
        """Delete a plot item.

        Arguments:

          *key*: str
            The name you gave to the plot item when it was created.

        Optional keyword arguments:

          *redraw*: [ *True*  (default) | *False* ]
            Whether to redraw the plot after applying changes.

          *rescale*: [ 'auto' (default) | *True* | *False* ]
            Whether to rescale the plot. If 'auto', then only rescale if needed.
        """
        item = self._items.pop(key)
        if key in self._animated_artists:
            self._animated_artists.remove(key)
        item['mpl_item'].remove()
        if redraw:
            self._update(rescale)

    def clear_data(self, key, redraw=True, rescale='auto'):
        """Delete all the data of a plot item.

        Arguments:

          *key*: str
            The name you gave to the plot item when it was created.

        Optional keyword arguments:

          *redraw*: [ *True*  (default) | *False* ]
            Whether to redraw the plot after applying changes.

          *rescale*: [ 'auto' (default) | *True* | *False* ]
            Whether to rescale the plot. If 'auto', then only rescale if needed.
        """
        item_value = self._items[key]
        if item_value['item_type'] == 'curve':
            item = item_value['mpl_item']
            memory = item_value['memory']
            old_data = item_value['data']
            if memory == 'circular' or memory == 'growable':
                old_data.clear()
                item.set_data(np.array([]), np.array([]))
            else:
                item.set_data(np.array([]), np.array([]))
        if redraw:
            self._update(rescale)

    def set_data(self, key, data, redraw=True, rescale='auto'):
        """Change the data of a plot item.

        Arguments:

          *key*: str
            The name you gave to the plot item when it was created.

          *data*: two-dimensional numpy array, list, or tuple or a PIL image
            The new data to be assigned to the plot item.

            For curves, *data* should be a series of points
            of the form ((x1, y1), (x2, y2), ...).

            For images, *data* should be a two dimensional float array, a uint8
            array or a PIL image. If *data* is an array, *data* can have the
            following shapes:

            * MxN -- luminance (grayscale, float array only)
            * MxNx3 -- RGB (float or uint8 array)
            * MxNx4 -- RGBA (float or uint8 array)

            The value for each component of MxNx3 and MxNx4 float arrays should be
            in the range 0.0 to 1.0; MxN float arrays may be normalized.

            For colormeshes, *data* is a 2-D array, and the dimensions of *X*
            and *Y* should be one greater than those of *data*.

        Optional keyword arguments:

          *redraw*: [ *True*  (default) | *False* ]
            Whether to redraw the plot after applying changes.

          *rescale*: [ 'auto' (default) | *True* | *False* ]
            Whether to rescale the plot. If 'auto', then only rescale if needed.
        """
        item_value = self._items[key]
        if item_value['item_type'] == 'curve':
            # convert the appended object to an array
            # if it starts as something else
            if type(data) is not np.ndarray:
                data = np.array(data)
            if data.ndim != 2:
                raise ValueError("'data' must be a two-dimensional array.")
            item = item_value['mpl_item']
            memory = item_value['memory']
            old_data = item_value['data']
            if memory == 'circular' or memory == 'growable':
                old_data.clear()
                old_data.append(data)
                item.set_data(old_data[:,0], old_data[:,1])
            else:
                item.set_data(data[:,0], data[:,1])
            if redraw:
                if self._animated:
                    if (rescale is True) or (key not in self._animated_artists):
                        self._force_rescale = True
                    elif rescale == 'auto':
                        if self._x_autoscale:
                            axis_min, axis_max = self._axes.get_xlim()
                            data_min = data[:,0].min()
                            data_max = data[:,0].max()
                            if (data_min < axis_min) or (data_max > axis_max) or (data_max-data_min < 0.5*(axis_max-axis_min)):
                                self._force_rescale = True
                        if self._y_autoscale:
                            axis_min, axis_max = self._axes.get_ylim()
                            data_min = data[:,1].min()
                            data_max = data[:,1].max()
                            if (data_min < axis_min) or (data_max > axis_max) or (data_max-data_min < 0.5*(axis_max-axis_min)):
                                self._force_rescale = True
                    if self._force_rescale:
                        # full update
                        self._full_animated_redraw()
                    else:
                        # only need to update and blit the axes region
                        self._fast_animated_redraw()
                else:
                    if (rescale is True) or ((self._x_autoscale or self._y_autoscale) and (rescale == 'auto')):
                        self._axes.relim()
                        self._axes.autoscale_view(self._tight_autoscale, self._x_autoscale, self._y_autoscale)
                        self._figure.tight_layout()
                        self._canvas.draw()
                        self._force_rescale = False
                    else:
                        self._canvas.draw()
            else:
                # just check if we need to rescale, but don't actually redraw
                if self._animated:
                    if (rescale is True) or (key not in self._animated_artists):
                        self._force_rescale = True
                    elif rescale == 'auto':
                        if self._x_autoscale:
                            axis_min, axis_max = self._axes.get_xlim()
                            data_min = data[:,0].min()
                            data_max = data[:,0].max()
                            if (data_min < axis_min) or (data_max > axis_max) or (data_max-data_min < 0.5*(axis_max-axis_min)):
                                self._force_rescale = True
                        if self._y_autoscale:
                            axis_min, axis_max = self._axes.get_ylim()
                            data_min = data[:,1].min()
                            data_max = data[:,1].max()
                            if (data_min < axis_min) or (data_max > axis_max) or (data_max-data_min < 0.5*(axis_max-axis_min)):
                                self._force_rescale = True
        elif item_value['item_type'] == 'image':
            if data.ndim != 2:
                raise ValueError("'data' must be a two-dimensional array.")
            item = item_value['mpl_item']
            shape = item_value['shape']
            item.set_data(data)
            if self._animated:
                #if rescale or (data.shape[0] != shape) or (data.shape[1] != shape):
                #    self._axes.relim()
                #    item.autoscale()
                #self._full_animated_redraw()
                # PROBLEMS WITH VIEW RANGE IN ABOVE CODE
                # BELOW WORKS BUT IS STILL NOT EFFICIENT
                # SHOULD REWRITE FOR SPEED                
                if rescale or (data.shape[0] != shape) or (data.shape[1] != shape):
                    self._axes.relim()
                    item.autoscale()
                self._figure.tight_layout()
                self._canvas.draw()
                # update animation background artists
                self._animated_background = self._canvas.copy_from_bbox(self._axes.bbox)
                for k in self._animated_artists:
                    self._axes.draw_artist(self._items[k]['mpl_item'])
                # blit entire canvas to ensure complete update
                self._canvas.blit(self._figure.bbox)
            else:
                self._axes.relim()
                item.autoscale()
                self._figure.tight_layout()
                self._canvas.draw()
        elif item_value['item_type'] == 'colormesh':
            item = item_value['mpl_item']
            item.set_array(data.ravel())
            item.autoscale()
            if self._animated:
                if rescale:
                    self._axes.relim()
                    item.autoscale()
                self._full_animated_redraw()
            else:
                self._axes.relim()
                item.autoscale()
                self._figure.tight_layout()
                self._canvas.draw()

    def append_data(self, key, data, redraw=True, rescale='auto'):
        """Append data to a plot item.

        Only works with curves which were created with
        *memory* = 'circular' or *memory* = 'growable'.

        Arguments:

          *key*: str
            The name you gave to the plot item when it was created.

          *data*: one or two-dimensional numpy array, list, or tuple
            The new data to be appended to the previous data of the plot item.
            *data* should be a single point of the form (x, y) or a series of
            points of the form ((x1, y1), (x2, y2), ...).

        Keyword arguments:

          *redraw*: [ *True*  (default) | *False* ]
            Whether to redraw the plot after applying changes.

          *rescale*: [ 'auto' (default) | *True* | *False* ]
            Whether to rescale the plot. If 'auto', then only rescale if needed.
        """
        item_value = self._items[key]
        if item_value['item_type'] == 'curve':
            # convert the appended object to an array if it starts as something else
            if type(data) is not np.ndarray:
                data = np.array(data)
            if data.ndim == 1:
                data = np.array([data])
            item = item_value['mpl_item']
            memory = item_value['memory']
            old_data = item_value['data']
            old_data_length = len(old_data)
            if memory == 'circular' or memory == 'growable':
                old_data.append(data)
                item.set_data(old_data[:,0], old_data[:,1])
            else:
                raise ValueError("Cannot append to curve item with memory == '%s'." % memory)
            if redraw:
                if self._animated:
                    if (rescale is True) or (key not in self._animated_artists):
                        self._force_rescale = True
                    else:
                        if self._x_autoscale:
                            if old_data_length < 2:
                                # there may not have been enough to set the scale before
                                self._force_rescale = True
                            else:
                                axis_min, axis_max = self._axes.get_xlim()
                                data_min = data[:,0].min()
                                data_max = data[:,0].max()
                                if (data_min < axis_min) or (data_max > axis_max):
                                    self._force_rescale = True
                        if self._y_autoscale:
                            if old_data_length < 2:
                                # there may not have been enough to set the scale before
                                self._force_rescale = True
                            else:
                                axis_min, axis_max = self._axes.get_ylim()
                                data_min = data[:,1].min()
                                data_max = data[:,1].max()
                                if (data_min < axis_min) or (data_max > axis_max):
                                    self._force_rescale = True
                    if self._force_rescale:
                        # full update
                        self._full_animated_redraw()
                    else:
                        # only need to update and blit the axes region
                        self._fast_animated_redraw()
                else:
                    if self._x_autoscale or self._y_autoscale:
                        self._axes.relim()
                        self._axes.autoscale_view(self._tight_autoscale,
                                                 self._x_autoscale, self._y_autoscale)
                        self._figure.tight_layout()
                        self._canvas.draw()
                        self._force_rescale = False
                    else:
                        self._canvas.draw()
            else:
                # just check if we need to rescale, but don't actually redraw
                if self._animated:
                    if (rescale is True) or (key not in self._animated_artists):
                        self._force_rescale = True
                    else:
                        if self._x_autoscale:
                            axis_min, axis_max = self._axes.get_xlim()
                            data_min = data[:,0].min()
                            data_max = data[:,0].max()
                            if (data_min < axis_min) or (data_max > axis_max):# or (data_max-data_min < 0.5*(axis_max-axis_min)):
                                self._force_rescale = True
                        if self._y_autoscale:
                            axis_min, axis_max = self._axes.get_ylim()
                            data_min = data[:,1].min()
                            data_max = data[:,1].max()
                            if (data_min < axis_min) or (data_max > axis_max):# or (data_max-data_min < 0.5*(axis_max-axis_min)):
                                self._force_rescale = True
        else:
            raise ValueError("Cannot append to plot item type '%s'." % item_value['item_type'])


    def set_properties(self, key, redraw=True, rescale='auto', **kwargs):
        """Set the graphical properties of a plot item.

        Arguments:

          *key*: str
            The name you gave to the plot item when it was created.

        Optional keyword arguments:

          Any of the the keyword arguments describing the graphical representation
          of the plot item that can be given when the item is created.

          *redraw*: [ *True*  (default) | *False* ]
            Whether to redraw the plot after applying changes.

          *rescale*: [ 'auto' (default) | *True* | *False* ]
            Whether to rescale the plot. If 'auto', then only rescale if needed.
        """
        item_value = self._items[key]
        if item_value['item_type'] == 'curve':
            item = item_value['mpl_item']
            if 'alpha' in kwargs:
                value = kwargs.pop('alpha')
                item.set_alpha(value)
            if 'line_color' in kwargs:
                value = kwargs.pop('line_color')
                item.set_color(value)
            if 'line_style' in kwargs:
                value = kwargs.pop('line_style')
                item.set_linestyle(value)
            if 'line_width' in kwargs:
                value = kwargs.pop('line_width')
                item.set_linewidth(value)
            if 'marker_color' in kwargs:
                value = kwargs.pop('marker_color')
                item.set_markerfacecolor(value)
            if 'marker_edge_color' in kwargs:
                value = kwargs.pop('marker_edge_color')
                item.set_markeredgecolor(value)
            if 'marker_edge_width' in kwargs:
                value = kwargs.pop('marker_edge_width')
                item.set_markeredgewidth(value)
            if 'marker_style' in kwargs:
                value = kwargs.pop('marker_style')
                item.set_marker(value)
            if 'marker_width' in kwargs:
                value = kwargs.pop('marker_width')
                item.set_markersize(value)
        elif item_value['item_type'] == 'image':
            item = item_value['mpl_item']
            if 'c_limits' in kwargs:
                value = kwargs.pop('c_limits')
                item.set_clim(value[0], value[1])
        elif item_value['item_type'] == 'colormesh':
            item = item_value['mpl_item']
            if 'c_limits' in kwargs:
                value = kwargs.pop('c_limits')
                item.set_clim(value[0], value[1])
        if len(kwargs) != 0:
            logger = multiprocessing.get_logger()
            logger.warning("Unused arguments in 'set_properties': %s."
                            % str(kwargs))
        if redraw:
            self._update(rescale)

    def set_plot_properties(self, redraw=True, rescale='auto', **kwargs):
        """Set the graphical properties of a plot.

        Optional keyword arguments:

          *aspect_ratio*: ['auto' (default) | 'equal' | a number ]

          *x_limits*: ['auto' (default) | scalars (x_min, x_max)]

          *y_limits*: ['auto' (default) | scalars (y_min, y_max)]

          *tight_autoscale*: [*True* | *False* (default)]

          *x_scale*: ['linear' (default) | 'log']
            Scaling of the x-axis.

          *y_scale*: ['linear' (default) | 'log']
            Scaling of the y-axis.

          *title*: str
            Title to be drawn above the plot.

          *x_label*: str
            Label to be drawn on the x-axis of the plot.

          *y_label*: str
            Label to be drawn on the y-axis of the plot.

          *dpi*: int
            Resolution (dots per inch) of plots saved to files.

          *redraw*: [ *True*  (default) | *False* ]
            Whether to redraw the plot after applying changes.

          *rescale*: [ 'auto' (default) | *True* | *False* ]
            Whether to rescale the plot. If 'auto', then only rescale if needed.
        """
        self._plot_properties.update(kwargs)
        if 'background' in kwargs:
            value = kwargs.pop('background')
        if 'aspect_ratio' in kwargs:
            # 'auto', 'equal', or a number
            value = kwargs.pop('aspect_ratio')
            self._axes.set_aspect(value)
        if 'x_limits' in kwargs:
            value = kwargs.pop('x_limits')
            if value == 'auto':
                self._axes.set_xlim(auto=True)
                self._x_autoscale = True
            else:
                self._axes.set_xlim(value, auto=False)
                self._x_autoscale = False
        if 'y_limits' in kwargs:
            value = kwargs.pop('y_limits')
            if value == 'auto':
                self._axes.set_ylim(auto=True)
                self._y_autoscale = True
            else:
                self._axes.set_ylim(value, auto=False)
                self._y_autoscale = False
        if 'tight_autoscale' in kwargs:
            value = kwargs.pop('tight_autoscale')
            self._tight_autoscale = value
        if 'x_scale' in kwargs:
            value = kwargs.pop('x_scale')
            self._axes.set_xscale(value)
        if 'y_scale' in kwargs:
            value = kwargs.pop('y_scale')
            self._axes.set_yscale(value)
        if 'title' in kwargs:
            value = kwargs.pop('title')
            self._axes.set_title(value)
        if 'x_label' in kwargs:
            value = kwargs.pop('x_label')
            self._axes.set_xlabel(value)
        if 'y_label' in kwargs:
            value = kwargs.pop('y_label')
            self._axes.set_ylabel(value)
        if 'x_grid' in kwargs:
            value = kwargs.pop('x_grid')
            self._axes.xaxis.grid(value)
        if 'y_grid' in kwargs:
            value = kwargs.pop('y_grid')
            self._axes.yaxis.grid(value)
        if 'x_ticks' in kwargs:
            value = kwargs.pop('x_ticks')
            self._axes.set_xticks(value)
            if 'x_ticks_label' in kwargs:
                value = kwargs.pop('x_ticks_label')
                self._axes.xaxis.set_ticklabels(value)
        if 'y_ticks' in kwargs:
            value = kwargs.pop('y_ticks')
            self._axes.set_yticks(value)
            if 'y_ticks_label' in kwargs:
                value = kwargs.pop('y_ticks_label')
                self._axes.yaxis.set_ticklabels(value)
        if 'dpi' in kwargs:
            self._plot_properties['dpi'] = kwargs.pop('dpi')
        if len(kwargs) != 0:
            logger = multiprocessing.get_logger()
            logger.warning("Unused arguments in 'set_plot_properties': %s."
                            % str(kwargs))
        if redraw:
            self._update(rescale)

    def save_figure(self, filename=None, rescale='auto'):
        """Save an image of the plot to a file.

        Optional keyword arguments:

          *filename*: str
            The name of the file to save to. If no filename is given, a dialog
            box in which to choose a filname will be presented.

          *rescale*: [ 'auto' (default) | *True* | *False* ]
            Whether to rescale the plot. If 'auto', then only rescale if needed.
        """
        if filename is None:
            filetypes = self._canvas.get_supported_filetypes_grouped()
            sorted_filetypes = list(filetypes.items())
            sorted_filetypes.sort()
            default_filetype = self._canvas.get_default_filetype()
            start = "image." + default_filetype
            filters = []
            selected_filter = None
            for name, exts in sorted_filetypes:
                exts_list = " ".join(['*.%s' % ext for ext in exts])
                filter = '%s (%s)' % (name, exts_list)
                if default_filetype in exts:
                    selected_filter = filter
                filters.append(filter)
            filters = ';;'.join(filters)
            filename = QtWidgets.QFileDialog.getSaveFileName(None, 'Save Plot Image', start, 
                                             filters, selected_filter)[0]
        if filename:
            try:
                if self._animated:
                    for k in self._animated_artists:
                        item = self._items[k]['mpl_item']
                        item.set_animated(False)
                    self._animated = False
                    self._update(rescale)
                    self._canvas.print_figure(str(filename),
                                             bbox_inches='tight',
                                             dpi=self._plot_properties['dpi'])
                    for k in self._animated_artists:
                        item = self._items[k]['mpl_item']
                        item.set_animated(True)
                    self._animated = True
                else:
                    self._canvas.print_figure(str(filename),
                                             bbox_inches='tight',
                                             dpi=self._plot_properties['dpi'])
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    None, "Error saving file", str(e),
                    QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.NoButton)


#
# Chart2D: scrolled plot panel with multiple line plots
#
class Chart2D(pythics.libcontrol.MPLControl):
    """Make a strip chart like plot of data with multiple y values for a given
    x value. Additional data can be added efficiently and the user can scroll
    through the chart history with a built-in scrollbar. Right click on the
    plot to save an image of the plot to a file.

    HTML parameters:

      *plots*: int (default 1)
        The number of plots to draw, stacked vertically with a common x axis.
        Note that each plot may have multiple curves, as set with the
        *curves_per_plot* property.

      *memory*: int [ 'circular' (default) | 'growable' ]
        Speicifies how data will be stored, and what happens when the
        orginally allocated memory is full. See the *length* parameter for more
        information.

      *length*: int (default 1000)
        The maximum number of points for the plot to store. Additional points
        will force earlier points to scroll out of range (if *memory* = 'circular')
        or grow the memory (if *memory* = 'growable').

      *fast_scroll*: [ *True* | *False* (default) ]
        Whether to accelerate scrolling by not drawing axes while scrolling.

      *actions*: dict
        a dictionarly of key:value pairs where the key is the name of a signal
        and value is the function to run when the signal is emitted

        actions in this control:

        =======================    ============================================
        signal                     when emitted
        =======================    ============================================
        'button_press_event'       a mouse button is pressed
        'button_release_event'     a mouse button is released
        'draw_event'               canvas is redrawn
        'key_press_event'          a key is pressed
        'key_release_event'        a key is released
        'motion_notify_event'      the mouse is moved
        'pick_event'               an object in the canvas is selected
        'resize_event'             the figure canvas is resized
        'scroll_event'             the mouse scroll wheel is rolled
        'figure_enter_event'       the mouse enters a new figure
        'figure_leave_event'       the mouse leaves a figure
        'axes_enter_event'         the mouse enters a new axes
        'axes_leave_event'         the mouse leaves an axe
        =======================    ============================================
    """
    def __init__(self, parent, plots=1, memory='circular', length=1000,
                 fast_scroll=False, **kwargs):
        pythics.libcontrol.MPLControl.__init__(self, parent, **kwargs)
        # initialize parameters that only depend on the number of plots
        self._n_plots = plots
        self._n_plot_range = list(range(self._n_plots))
        self._memory = memory
        self._history_length = length
        self._fast_scroll = fast_scroll
        self._requested_span = self._history_length
        self._span = self._requested_span
        self._span_choice = 'autoscale span'
        # setup the layout and plot widget
        self._widget = QtWidgets.QFrame()
        self._sizer = QtWidgets.QVBoxLayout()
        self._figure = matplotlib.figure.Figure()
        self._canvas = PythicsMPLCanvas(self, self._figure)
        self._sizer.addWidget(self._canvas)
        self._mpl_widget = self._canvas
        # row of controls below the plot
        self._row_sizer = QtWidgets.QHBoxLayout()
        self._sizer.addLayout(self._row_sizer)
        # set up scoll bar
        self._scroll_to_end = True
        self._pressed = False
        self._scrollbar = QtWidgets.QScrollBar(QtCore.Qt.Horizontal)
        self._scrollbar.setTracking(True)
        self._row_sizer.addWidget(self._scrollbar)
        self._scrollbar.valueChanged.connect(self._scroll)
        self._scrollbar.sliderPressed.connect(self._pressed_start)
        self._scrollbar.sliderReleased.connect(self._pressed_end)
        # choice of autoscale or fixed span
        self._choice_widget = QtWidgets.QComboBox()
        self._choice_widget.insertItem(2, 'autoscale span')
        self._choice_widget.insertItem(2, 'fixed span')
        self._choice_widget.setFixedWidth(150)
        self._choice_widget.activated.connect(self._change_span_choice)
        self._row_sizer.addWidget(self._choice_widget)
        # box to hold fixed span
        self._span_widget = QtWidgets.QSpinBox()
        self._span_widget.setSingleStep(1)
        self._span_widget.setMinimum(2)
        self._span_widget.setMaximum(self._history_length)
        self._span_widget.setFixedWidth(150)
        self._span_widget.setValue(self._history_length)
        self._span_widget.valueChanged.connect(self._change_span)
        self._row_sizer.addWidget(self._span_widget)
        self._widget.setLayout(self._sizer)
        # initialize parameters that depend on the number of lines
        self._n_curves_per_plot = list([1])*self._n_plots
        # set up plots
        self._plot_axes = list()
        self._y_autoscales = list()
        self._plot_properties = list()
        default_plot_properties = dict(x_limits='auto',
                                       y_limits='auto',
                                       x_scale='linear',
                                       y_scale='linear',
                                       aspect_ratio='auto',
                                       dpi=150)
        for i in self._n_plot_range:
            if i == 0:
                self._plot_axes.append(self._figure.add_subplot(self._n_plots, 1, i+1))
            else:
                self._plot_axes.append(self._figure.add_subplot(self._n_plots, 1, i+1, sharex=self._plot_axes[0]))
            self._plot_properties.append(default_plot_properties.copy())
            self._y_autoscales.append(True)
            self._set_plot_properties(i, **default_plot_properties)
        self._fast_requested = False
        self._fast = False
        self.clear()
        # need to update plot on resize
        self._canvas.mpl_connect('resize_event', self._resize)

    def _change_span(self, *args):
        self._requested_span = int(self._span_widget.value())
        if self._span_choice == 'fixed span':
            self._set_span(self._requested_span)

    def _change_span_choice(self, *args):
        self._span_choice = self._choice_widget.currentText()
        if self._span_choice == 'fixed span':
            self._set_span(self._requested_span)
        else:
            self._set_span(self._history_length)

    def _set_span(self, span):
        self._span = span
        length = len(self._data)
        self._scroll_page_size = min(span, length)
        self._scroll_position = min(self._scroll_position,
                                   length - self._scroll_page_size)
        self._update_scrollbar()
        self._update_plot()

    def _resize(self, event):
        # Don't use canvas.blit() in here to avoid recursive drawing warnings
        if self._fast:
            self._canvas.draw()
            self._animated_background = self._canvas.copy_from_bbox(self._figure.bbox)
            k = 0
            for i in range(self._n_plots):
                for j in range(self._n_curves_per_plot[i]):
                    self._plot_axes[i].draw_artist(self.curves[k])
                    k += 1
        else:
            self._figure.tight_layout()
            self._canvas.draw()
            k = 0
            for i in range(self._n_plots):
                for j in range(self._n_curves_per_plot[i]):
                    self._plot_axes[i].draw_artist(self.curves[k])
                    k += 1
        
    def _scroll(self):
        self._scroll_position = self._scrollbar.value()
        self._update_plot()

    def _pressed_start(self):
        self._pressed = True
        if self._fast_scroll:
            self._start_fast()
            self._full_redraw(False)

    def _pressed_end(self):
        self._pressed = False
        if self._fast_scroll:
            self._stop_fast()

    def _go_to_end(self):
        return self._scroll_to_end and (not self._pressed)

    def _update_scrollbar(self):
        self._scrollbar.setMaximum(len(self._data)-self._scroll_page_size)
        self._scrollbar.setPageStep(self._scroll_page_size)
        self._scrollbar.setValue(self._scroll_position)

    def _update_plot(self, layout=True):
        start = self._scroll_position
        stop = self._scroll_position + self._scroll_page_size
        # update data
        data_x_ys = self._data[start:stop]
        # all share the same x values
        data_x = data_x_ys[:,0]
        for i in range(self.n_curves_total):
            data_y = data_x_ys[:,i+1]
            self.curves[i].set_data(data_x, data_y)
        # replot
        for i in range(self._n_plots):
            axes = self._plot_axes[i]
            axes.relim()
            axes.autoscale_view(True, True, self._y_autoscales[i])
            # Eliminate margnins in x, should add this to properties?
            axes.margins(x=0.0)            
        if self._fast:
            self._fast_redraw()
        else:
            self._full_redraw(layout)

    def _start_fast(self):
        if not self._fast:
            for i in range(self._n_plots):
                self._plot_axes[i].get_xaxis().set_visible(False)
                self._plot_axes[i].get_yaxis().set_visible(False)
            self._canvas.draw()
            self._animated_background = self._canvas.copy_from_bbox(self._figure.bbox)
            self._fast = True

    def _fast_redraw(self):
        self._canvas.restore_region(self._animated_background)
        k = 0
        for i in range(self._n_plots):
            for j in range(self._n_curves_per_plot[i]):
                self._plot_axes[i].draw_artist(self.curves[k])
                k += 1
            # redraw the region in each axes
            self._canvas.blit(self._plot_axes[i].bbox)

    def _stop_fast(self):
        if (not self._fast_scroll or not self._pressed) and (not self._fast_requested):
            self._fast = False
            for i in range(self._n_plots):
                self._plot_axes[i].get_xaxis().set_visible(True)
                self._plot_axes[i].get_yaxis().set_visible(True)
            self._full_redraw()

    def _full_redraw(self, layout=True):
        if layout:
            self._figure.tight_layout()
        self._canvas.draw()
        k = 0
        for i in range(self._n_plots):
            for j in range(self._n_curves_per_plot[i]):
                self._plot_axes[i].draw_artist(self.curves[k])
                k += 1
        # blit entire canvas to ensure complete update
        self._canvas.blit(self._figure.bbox)

    def _set_plot_properties(self, n, **kwargs):
        axes = self._plot_axes[n]
        if 'background' in kwargs:
            value = kwargs.pop('background')
        if 'aspect_ratio' in kwargs:
            # 'auto', 'equal', or a number
            value = kwargs.pop('aspect_ratio')
            axes.set_aspect(value)
        if 'x_limits' in kwargs:
            value = kwargs.pop('x_limits')
            if value == 'auto':
                axes.set_xlim(auto=True)
                self._x_autoscale = True
            else:
                axes.set_xlim(value, auto=False)
                self._x_autoscale = False
        if 'y_limits' in kwargs:
            value = kwargs.pop('y_limits')
            if value == 'auto':
                axes.set_ylim(auto=True)
                self._y_autoscales[n] = True
            else:
                axes.set_ylim(value, auto=False)
                self._y_autoscales[n] = False
        if 'x_scale' in kwargs:
            value = kwargs.pop('x_scale')
            axes.set_xscale(value)
        if 'y_scale' in kwargs:
            value = kwargs.pop('y_scale')
            axes.set_yscale(value)
        if 'title' in kwargs:
            value = kwargs.pop('title')
            axes.set_title(value)
        if 'x_label' in kwargs:
            value = kwargs.pop('x_label')
            axes.set_xlabel(value)
        if 'y_label' in kwargs:
            value = kwargs.pop('y_label')
            axes.set_ylabel(value)
        if 'x_grid' in kwargs:
            value = kwargs.pop('x_grid')
        if 'y_grid' in kwargs:
            value = kwargs.pop('y_grid')
        if 'dpi' in kwargs:
            self.dpi = kwargs.pop('dpi')
        if len(kwargs) != 0:
            logger = multiprocessing.get_logger()
            logger.warning("Unused arguments in 'set_plot_properties': %s."
                            % str(kwargs))

    #---------------------------------------------------
    # methods below used only for access by action proxy

    def append_data(self, data):
        """Append data to the plot.

        Arguments:

          *data*: one or two-dimensional numpy array, list, or tuple
            The new data to be appended to the previous data of the plot item.
            *data* should be a single point of the form [x, y_1, y_2, ...] or a
            series of points of the form:
            [[x_0, y_01, y_02, ...], [x_1, y_11, y_12, ...], ...].
        """
        self._data.append(data)
        length = len(self._data)
        self._scroll_page_size = min(self._span, length)
        if self._go_to_end():
            self._scroll_position = length - self._scroll_page_size
        self._update_scrollbar()
        self._update_plot(layout=False)

    def clear(self):
        """Clear all data and labels from the plot.
        """
        # initialize all curve properties when the number of curves is changed
        # first clear out old curves
        for i in self._n_plot_range:
            self._plot_axes[i].clear()
        self.n_curves_total = sum(self._n_curves_per_plot)
        # list of curves (points or lines)
        self.curves = list()
        for i in range(self._n_plots):
            for j in range(self._n_curves_per_plot[i]):
                item, = self._plot_axes[i].plot(np.array([]), np.array([]),
                                                animated=True)
                self.curves.append(item)
        for i in self._n_plot_range[0:-1]:
            for label in self._plot_axes[i].get_xticklabels():
                label.set_visible(False)
        # clear out the data
        if self._memory == 'growable':
            self._data = pythics.lib.GrowableArray(cols=self.n_curves_total+1,
                                                  length=self._history_length)
        else:
            self._data = pythics.lib.CircularArray(cols=self.n_curves_total+1,
                                                  length=self._history_length)
        self._scroll_page_size = 0
        self._scroll_position = 0
        self._update_scrollbar()
        self._update_plot()

    def clear_data(self):
        """Clear all data from the plot.
        """
        self._data.clear()
        self._scroll_page_size = 0
        self._scroll_position = 0
        self._update_scrollbar()
        self._update_plot()

    def update(self):
        """Force the plot to update. This should not normally be necessary.
        """
        self._update_plot()

    def set_data(self, data):
        """Set the data displayed on the plot, replacing the old data.

        Arguments:

          *data*: one or two-dimensional numpy array, list, or tuple
            The new data to be appended to the previous data of the plot item.
            *data* should be a single point of the form [x, y_1, y_2, ...] or a
            series of points of the form:
            [[x_0, y_01, y_02, ...], [x_1, y_11, y_12, ...], ...].
        """
        self._data.clear()
        self._data.append(data)
        length = len(self._data)
        self._scroll_page_size = min(self._span, length)
        if self._go_to_end():
            self._scroll_position = length - self._scroll_page_size
        self._update_scrollbar()
        self._update_plot(layout=False)

    def _get_scroll_to_end(self):
        """Whether to scroll to the right as new data is added to the plot.
        [ *True* (default) | *False* ]
        """
        return self._scroll_to_end

    def _set_scroll_to_end(self, value):
        self._scroll_to_end = value
        if value == True:
            self._scroll_position = len(self._data) - self._scroll_page_size
            self._update_scrollbar()
            self._update_plot()

    scroll_to_end = property(_get_scroll_to_end, _set_scroll_to_end)

    def _get_fast(self):
        """Whether to skip drawing the axes to accelerate drawing. Set to
        *False* when done with updates to force a full redraw.
        [ *True* (default) | *False* ]
        """
        return self._fast_requested

    def _set_fast(self, value):
        if value is not self._fast_requested:
            self._fast_requested = value
            # change requested
            if value:
                self._start_fast()
            else:
                self._stop_fast()

    fast = property(_get_fast, _set_fast)

    def _get_curves_per_plot(self):
        """A list integers specifying how many curves are to be drawn in each
        plot. [ 1, 1, 2 ] would specify 1 curve in the first plot, 1 in the
        second, and two in the third. These curves would be numbered 0 through
        3 for access in other methods.
        """
        return self._n_curves_per_plot

    def _set_curves_per_plot(self, value):
        self._n_curves_per_plot = value
        self.clear()

    curves_per_plot = property(_get_curves_per_plot, _set_curves_per_plot)

    def set_plot_properties(self, n, **kwargs):
        """Set the graphical properties of a plot.
        Arguments:

          *n*: int
            The index of the plot of which to set the properties.

        Optional keyword arguments:

          *y_limits*: [ 'auto' (default) | scalars (y_min, y_max) ]

          *x_scale*: [ 'linear' (default) | 'log' ]
            Scaling of the x-axis.

          *y_scale*: [ 'linear' (default) | 'log' ]
            Scaling of the y-axis.

          *title*: str
            Title to be drawn above the plot.

          *x_label*: str
            Label to be drawn on the x-axis of the plot.

          *y_label*: str
            Label to be drawn on the y-axis of the plot.

          *dpi*: int
            Resolution (dots per inch) of plots saved to files.
        """
        self._set_plot_properties(n, **kwargs)
        self._update_plot()

    def set_curve_properties(self, n, **kwargs):
        """Set the graphical properties of a curve item.

        Arguments:

          *n*: int
            The index of the plot of which to set the properties.

        Optional keyword arguments:

          Any of the the keyword arguments that can be given to specify the
          properties of a curve in Plot2D (listed under *new_curve*).
        """
        item = self.curves[n]
        if 'alpha' in kwargs:
            value = kwargs.pop('alpha')
            item.set_alpha(value)
        if 'line_color' in kwargs:
            value = kwargs.pop('line_color')
            item.set_color(value)
        if 'line_style' in kwargs:
            value = kwargs.pop('line_style')
            item.set_linestyle(value)
        if 'line_width' in kwargs:
            value = kwargs.pop('line_width')
            item.set_linewidth(value)
        if 'marker_color' in kwargs:
            value = kwargs.pop('marker_color')
            item.set_markerfacecolor(value)
        if 'marker_edge_color' in kwargs:
            value = kwargs.pop('marker_edge_color')
            item.set_markeredgecolor(value)
        if 'marker_edge_width' in kwargs:
            value = kwargs.pop('marker_edge_width')
            item.set_markeredgewidth(value)
        if 'marker_style' in kwargs:
            value = kwargs.pop('marker_style')
            item.set_marker(value)
        if 'marker_width' in kwargs:
            value = kwargs.pop('marker_width')
            item.set_markersize(value)
        if len(kwargs) != 0:
            logger = multiprocessing.get_logger()
            logger.warning("Unused arguments in 'set_properties': %s."
                            % str(kwargs))
        self._update_plot()

    def save_figure(self, filename=None):
        """Save an image of the plot to a file.

        Optional keyword arguments:

          *filename*: str
            The name of the file to save to. If no filename is given, a dialog
            box in which to choose a filname will be presented.

          *rescale*: [ 'auto' (default) | *True* | *False* ]
            Whether to rescale the plot. If 'auto', then only rescale if needed.
        """
        if filename is None:
            filetypes = self._canvas.get_supported_filetypes_grouped()
            sorted_filetypes = list(filetypes.items())
            sorted_filetypes.sort()
            default_filetype = self._canvas.get_default_filetype()
            start = "image." + default_filetype
            filters = []
            selected_filter = None
            for name, exts in sorted_filetypes:
                exts_list = " ".join(['*.%s' % ext for ext in exts])
                filter = '%s (%s)' % (name, exts_list)
                if default_filetype in exts:
                    selected_filter = filter
                filters.append(filter)
            filters = ';;'.join(filters)
            filename = QtWidgets.QFileDialog.getSaveFileName(None, 'Save Plot Image', start, 
                                             filters, selected_filter)[0]
        if filename:
            try:
                for item in self.curves:
                    item.set_animated(False)
                self._animated = False
                self._canvas.draw()
                self._canvas.print_figure(str(filename),
                                         bbox_inches='tight',
                                         dpi=self.dpi)
                for item in self.curves:
                    item.set_animated(True)
                self._animated = True
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    None, "Error saving file", str(e),
                    QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.NoButton)


class PythicsMPLCanvas(FigureCanvas):
    def __init__(self, pythics_control, *args, **kwargs):
        self._pythics_control = pythics_control
        FigureCanvas.__init__(self, *args, **kwargs)
        # setup context menu on right-click
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._popup)

    def _popup(self, pos):
        menu = QtWidgets.QMenu()
        save_action = menu.addAction('Save...')
        action = menu.exec_(self.mapToGlobal(pos))
        if action == save_action:
            self._pythics_control.save_figure()
            
    def draw_idle(self, *args, **kwargs):
        # Block these calls to avoid redraws missing actors when
        #  resizing with animated actors. Blocking does not cause problems
        #  if resize is handled correctly.
        pass
