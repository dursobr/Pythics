# -*- coding: utf-8 -*-
#
#  Copyright 2012 - 2013 Brian R. D'Urso
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
import math
import numpy as np


def initialize(shell, **kwargs):
    shell.interact(kwargs.copy())
    clear(**kwargs)


def clear(messages, plot, **kwargs):
    plot.clear()
    messages.clear()
    plot.set_plot_properties(
        title='Plot of f(x)',
        x_label='x',
        y_label='f(x)',
        x_scale='linear',
        y_scale='linear',
        aspect_ratio='auto')
    # plot with lines and point markers
    plot.new_curve('f', memory='growable', length=100, animated=True, 
                   line_style='-', line_color='blue', 
                   marker_style='o', marker_color='green')
#    # just lines
#    plot.new_curve('f', memory='growable', length=100, animated=True, 
#                   line_style='-', line_color='blue')


#
# run: the simulation
#
def run(function, x_min, x_max, N_plot_steps, messages, plot, **kwargs):
    # setup the parameters
    x_1 = x_min.value
    x_2 = x_max.value
    f_string = function.value
    N_plot = N_plot_steps.value

    # generate an array of x values at which we will evalute and plot f(x)
    xs = np.linspace(x_1, x_2, N_plot)
    
    # definition of f(x), which evaluates the function written in the GUI
    #   normally you would code a fixed f(x)
    def f(x):
        return eval(f_string)

    # slow version, draw one point at a time
    for x in xs:
        y = f(x)
        plot.append_data('f', (x, y))
        
#    # faster version, calculate one point at a time but plot all at the end
#    ys = np.zeros(N_plot)
#    for i in range(N_plot):
#        ys[i] = f(xs[i])
#    plot.set_data('f', np.column_stack([xs, ys]))
    
#    # fastest version, vectorize everything - use numpy functions in f(x)
#    ys = f(xs)
#    plot.set_data('f', np.column_stack([xs, ys]))    
    
    messages.write('Done.\n')
