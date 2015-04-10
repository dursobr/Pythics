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
import numpy as np


#
# basic functionality: initialize, start, stop, clear
#
def initialize(shell, **kwargs):
    shell.interact(kwargs.copy())


def clear(messages, plot_1, plot_2, **kwargs):
    plot_1.clear()
    plot_2.clear()
    messages.clear()


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


def run(prob_dt, prob_N, algorithm, stop, messages, plot_1, plot_2, **kwargs):
    a = algorithm.value
    N = prob_N.value
    dt = prob_dt.value
    plot_1.set_plot_properties(
        title='Motion',
        x_label='t',
        y_label='x or v',
        x_scale='linear',
        y_scale='linear',
        aspect_ratio='auto')
    plot_2.set_plot_properties(
        title='Phase Space',
        x_label='x',
        y_label='v',
        x_scale='linear',
        y_scale='linear',
        aspect_ratio='auto')
    plot_1.new_curve('Euler-x', memory='growable', animated=True, line_style='', 
               marker_style='+', marker_edge_color='blue', marker_width=3.0)
    plot_1.new_curve('Euler-v', memory='growable', animated=True, line_style='', 
               marker_style='+', marker_edge_color='red', marker_width=3.0)
    plot_2.new_curve('Euler-xv', memory='growable', animated=True, line_style='', 
               marker_style='+', marker_edge_color='green', marker_width=3.0)
    plot_1.new_curve('Euler_symplectic-x', memory='growable', animated=True, 
               line_style='', marker_style='d', marker_color='blue', 
               marker_edge_color='blue', marker_width=3.0)
    plot_1.new_curve('Euler_symplectic-v', memory='growable', animated=True, 
               line_style='', marker_style='d', marker_color='red', 
               marker_edge_color='red', marker_width=3.0)
    plot_2.new_curve('Euler_symplectic-xv', memory='growable', animated=True, 
               line_style='', marker_style='d', marker_color='green', 
               marker_edge_color='green', marker_width=3.0)
    plot_1.new_curve('RK2-x', memory='growable', animated=True, line_style='', 
               marker_style='*', marker_color='blue', 
               marker_edge_color='blue', marker_width=3.0)
    plot_1.new_curve('RK2-v', memory='growable', animated=True, line_style='', 
               marker_style='*', marker_color='red', 
               marker_edge_color='red', marker_width=3.0)
    plot_2.new_curve('RK2-xv', memory='growable', animated=True, line_style='', 
               marker_style='*', marker_color='green', 
               marker_edge_color='green', marker_width=3.0)
    plot_1.new_curve('RK4-x', memory='growable', animated=True, line_style='', 
               marker_style='x', marker_edge_color='blue', marker_width=3.0)
    plot_1.new_curve('RK4-v', memory='growable', animated=True, line_style='', 
               marker_style='x', marker_edge_color='red', marker_width=3.0)
    plot_2.new_curve('RK4-xv', memory='growable', animated=True, line_style='', 
               marker_style='x', marker_edge_color='green', marker_width=3.0)
    # the function to integrate
    def f(t, y, f_return):
        f_return[0] = y[1]
        f_return[1] = -y[0]
    # initial t value
    t = 0.0
    # initial dependent variable values [x0, v0]
    y = np.array([1.0, 0.0])
    messages.write('Starting integration.\n')
    if a == 'Euler':
        for n in range(N):
            Euler(f, dt, t, y)
            t += dt
            # position
            plot_1.append_data('Euler-x', (t, y[0]))
            # velocity
            plot_1.append_data('Euler-v', (t, y[1]))
            # phase space plot
            plot_2.append_data('Euler-xv', (y[0], y[1]))
            if stop.value: break         
    elif a == 'Euler_symplectic':
        for n in range(N):
            Euler_symplectic(f, dt, t, y)
            t += dt           
            # position
            plot_1.append_data('Euler_symplectic-x', (t, y[0]))
            # velocity
            plot_1.append_data('Euler_symplectic-v', (t, y[1]))
            # phase space plot
            plot_2.append_data('Euler_symplectic-xv', (y[0], y[1]))
            if stop.value: break         
    elif a == 'RK2':
        for n in range(N):
            RK2(f, dt, t, y)
            t += dt           
            # position
            plot_1.append_data('RK2-x', (t, y[0]))
            # velocity
            plot_1.append_data('RK2-v', (t, y[1]))
            # phase space plot
            plot_2.append_data('RK2-xv', (y[0], y[1]))
            if stop.value: break         
    elif a == 'RK4':
        for n in range(N):
            RK4(f, dt, t, y)
            t += dt           
            # position
            plot_1.append_data('RK4-x', (t, y[0]))
            # velocity
            plot_1.append_data('RK4-v', (t, y[1]))
            # phase space plot
            plot_2.append_data('RK4-xv', (y[0], y[1]))
            if stop.value: break
    # reset the stop button in case it was pushed
    stop.value = False
    messages.write('Done.\n')
