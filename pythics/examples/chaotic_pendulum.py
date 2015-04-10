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


#
# basic functionality: initialize, start, stop, clear
#
def initialize(shell, **kwargs):
    shell.interact(kwargs.copy())
    clear(**kwargs)


def clear(messages, plot_1, plot_2, plot_3, **kwargs):
    plot_1.clear()
    plot_2.clear()
    plot_3.clear()
    messages.clear()
    plot_1.set_plot_properties(
        title='Pendulum',
        x_label='x',
        y_label='y',
        x_limits=(-1.2, 1.2),
        y_limits=(-1.2, 1.2),
        x_scale='linear',
        y_scale='linear',
        aspect_ratio='equal')
    plot_2.set_plot_properties(
        title='Phase Space',
        x_label='angle',
        y_label='velocity',
        x_scale='linear',
        y_scale='linear',
        aspect_ratio='auto')
    plot_3.set_plot_properties(
        title='Time Series',
        x_label='time',
        y_label='angle',
        x_scale='linear',
        y_scale='linear',
        aspect_ratio='auto')        
    plot_1.new_curve('rod', animated=True, line_color='black')
    plot_1.new_curve('bob', animated=True, line_style='', 
                     marker_style='o', marker_width=20, marker_edge_width=1)
    plot_2.new_curve('trajectory', memory='growable', animated=True, 
                     line_color='red')
    plot_3.new_curve('ts', memory='growable', animated=True, 
                     line_color='green')


#
# run: the simulation
#

n_depvars = 2
f_return = np.zeros((n_depvars), dtype=np.float)
y_temp = np.zeros((n_depvars), dtype=np.float);
k1 = np.zeros((n_depvars), dtype=np.float)
k2 = np.zeros((n_depvars), dtype=np.float)
k3 = np.zeros((n_depvars), dtype=np.float)
k4 = np.zeros((n_depvars), dtype=np.float)


def Euler(f, dt, t, y):
    f(t, y, f_return)
    y += f_return*dt


def Euler_symplectic(f, dt, t, y):
    f(t, y, f_return)
    y[0] += f_return[0]*dt
    f(t, y, f_return)
    y[1] += f_return[1]*dt


def RK2(f, dt, t, y):
    f(t, y, f_return)
    k1[:] = dt*f_return
    y_temp[:] = y + k1/2. 
    f(t + dt/2., y_temp, f_return) 
    k2[:] = dt*f_return 
    y += k2


def RK4(f, dt, t, y):
    f(t, y, f_return)
    k1[:] = dt*f_return 
    y_temp[:] = y + k1/2. 
    f(t + dt/2., y_temp, f_return) 
    k2[:] = dt*f_return 
    y_temp[:] = y + k2/2. 
    f(t + dt/2., y_temp, f_return)
    k3[:] = dt*f_return  
    y_temp[:] = y + k3 
    f(t+dt, y_temp, f_return) 
    k4[:] = dt*f_return  
    y += (k1+2.*(k2+k3)+k4)/6.


def run(prob_dt, algorithm, prob_v0, prob_omega, prob_alpha, prob_f, 
        stop, messages, plot_1, plot_2, plot_3, **kwargs):
    dt = prob_dt.value
    a = algorithm.value
    v0 = prob_v0.value
    omega = prob_omega.value
    alpha = prob_alpha.value
    f = prob_f.value
    # the function to integrate
    def F(t, y, f_return):
        f_return[0] = y[1]
        f_return[1] = -math.sin(y[0])-alpha*y[1]+f*math.cos(omega*t)
    # initial t value
    t = 0.0
    # initial dependent variable values [x0, v0]
    y = np.array([0.0, v0])
    messages.write('Starting integration.\n')
    # draw pendulum
    xy_point = (math.sin(y[0]), -math.cos(y[0]))
    plot_1.set_data('rod', [[0.0, 0.0], xy_point])
    plot_1.set_data('bob', [xy_point])
    plot_2.append_data('trajectory', [y[0], y[1]])
    plot_3.append_data('ts', [t, y[0]])
    n = 0
    while True:
        if a == 'Euler':
            Euler(F, dt, t, y)
        elif a == 'Euler_symplectic':
            Euler_symplectic(F, dt, t, y)
        elif a == 'RK2':
            RK2(F, dt, t, y)
        elif a == 'RK4':
            RK4(F, dt, t, y)
        t += dt
        if n % 2 == 0:
            # pendulum animation
            xy_point = (math.sin(y[0]), -math.cos(y[0]))
            plot_1.set_data('rod', [[0.0, 0.0], xy_point])
            plot_1.set_data('bob', [xy_point])
            # phase space plot
            plot_2.append_data('trajectory', [y[0], y[1]])
            # position
            plot_3.append_data('ts', [t, y[0]])
            if stop.value: break
        n += 1
    # reset the stop button in case it was pushed
    stop.value = False
    messages.write('Done.\n')
