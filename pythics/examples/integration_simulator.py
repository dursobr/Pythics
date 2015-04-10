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
import random
import numpy as np


#
# basic functionality: initialize, start, stop, clear
#
def initialize(shell, **kwargs):
    shell.interact(kwargs.copy())
    clear(**kwargs)


def clear(messages, plot, **kwargs):
    plot.clear()
    messages.clear()
    plot.set_plot_properties(
        title='Numerical Integration',
        x_label='x',
        y_label='y',
        x_scale='linear',
        y_scale='linear',
        aspect_ratio='auto')
    plot.new_curve('box counting', memory='growable', length=100, animated=True, 
                   line_style='-', line_color='violet')
    plot.new_curve('trapezoid rule', memory='growable', length=100, animated=True, 
                   line_style='-', line_color='blue')
    plot.new_curve('Simpsons rule', memory='growable', length=100, animated=True, 
                   line_style='-', line_color='green')
    plot.new_curve('Monte Carlo', memory='growable', length=100, animated=True, 
                   line_style='-', line_color='red')


#
# evaluate the function
#
def f(x, s):
    return eval(s)


#
# run: the simulation
#
def run(function, algorithm, range_min, range_max, N, stop, messages, plot, **kwargs):
    # put simulation stuff here
    a = algorithm.value
    x_min = range_min.value
    x_max = range_max.value
    x_span = x_max - x_min
    f_string = function.value
    N_steps = N.value
    dx = x_span/N_steps
    if a == 'box counting':
        messages.write('Integrating by box counting...\n')
        integral = 0.0
        xs = np.linspace(x_min+0.5*dx, x_max-0.5*dx, N_steps)
        for x in xs:
            y = f(x, f_string)
            plot.append_data(a, np.array([[x-0.5*dx, 0], [x-0.5*dx, y], 
                                          [x+0.5*dx, y], [x+0.5*dx, 0]]))
            integral += y*dx
            if stop.value: break
        messages.write('The integral of %s from %g to %g is %g.\n' % (f_string, x_min, x_max, integral))
    elif a == 'trapezoid rule':
        messages.write('Integrating by trapezoid rule...\n')
        integral = 0.0
        for i in range(N_steps):
            x_1 = x_min + i*dx
            x_2 = x_min + (i+1.0)*dx
            y_1 = f(x_1, f_string)
            y_2 = f(x_2, f_string)
            plot.append_data(a, np.array([[x_1, 0.0], [x_1, y_1], 
                                          [x_2, y_2], [x_2, 0.0]]))
            integral += 0.5*dx*(y_1 + y_2)
            if stop.value: break
        messages.write('The integral of %s from %g to %g is %g.\n' % (f_string, x_min, x_max, integral))
    elif a == 'Simpsons rule':
        messages.write('Integrating by Simpsons rule...\n')
        integral = 0.0
        for i in range(N_steps):
            x_1 = x_min + i*dx
            x_2 = x_min + (i+0.5)*dx
            x_3 = x_min + (i+1.0)*dx
            y_1 = f(x_1, f_string)
            y_2 = f(x_2, f_string)
            y_3 = f(x_3, f_string)
            plot.append_data(a, np.array([[x_1, 0.0], [x_1, y_1], [x_2, y_2], 
                                          [x_3, y_3], [x_3, 0.0]]))
            integral += 0.333333333*0.5*dx*(y_1 + 4.0*y_2 + y_3)
            if stop.value: break
        messages.write('The integral of %s from %g to %g is %g.\n' % (f_string, x_min, x_max, integral))
    elif a == 'Monte Carlo':
        messages.write('Integrating by Monte Carlo...\n')
        y_sum = 0.0
        for i in range(N_steps):
            x = random.random()*x_span + x_min
            y = f(x, f_string)
            #plot.draw_line((x, 0), (x, y), line_color=color)
            plot.append_data(a, np.array([[x-0.5*dx, 0.0], [x-0.5*dx, y], 
                                          [x+0.5*dx, y], [x+0.5*dx, 0.0]]))
            y_sum += y
            if stop.value: break
        integral = x_span*y_sum/N_steps
        messages.write('The integral of %s from %g to %g is %g.\n' % (f_string, x_min, x_max, integral))
    else:
        messages.write('Integration method not recognized.\n')
    stop.value = False
    messages.write('Done.\n')
