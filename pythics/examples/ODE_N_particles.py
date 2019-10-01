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
import logging
import math
import numpy as np


# setup the logger
logger = logging.getLogger('log')
#logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)


#
# basic functionality: initialize, start, stop, clear
#
def initialize(shell, **kwargs):
    # setup the logger
    sh = logging.StreamHandler(kwargs['messages'])
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    # setup the python shell
    shell.interact(kwargs.copy())
    # clear plot
    clear(**kwargs)


def clear(messages, plot_1, **kwargs):
    plot_1.clear()
    plot_1.set_plot_properties(
        aspect_ratio='equal',
        x_limits=(-1.15, 1.15),
        y_limits=(-1.15, 1.15))
    # the particles
    plot_1.new_curve('particles', memory='array', animated=True,
        line_style='', marker_style='o', marker_width=20, marker_edge_width=1)
    messages.clear()


#
# run: the simulation
#

def run(prob_m, prob_N_particles, prob_epsilon, prob_r_zero, prob_v_max, prob_g, prob_dt, 
        steps_per_update, algorithm, start_stop, plot_1, **kwargs):
    N_particles = prob_N_particles.value
    m = prob_m.value
    v_max = prob_v_max.value
    # setup
    n_depvars = 4*N_particles
    f_return = np.zeros((n_depvars), dtype=np.float)
    y_temp = np.zeros((n_depvars), dtype=np.float);
    k1 = np.zeros((n_depvars), dtype=np.float)
    k2 = np.zeros((n_depvars), dtype=np.float)
    k3 = np.zeros((n_depvars), dtype=np.float)
    k4 = np.zeros((n_depvars), dtype=np.float)
    temp_1 = np.zeros((N_particles), dtype=np.float)
    
    def Euler(f, dt, t, y, *args):
        f(t, y, f_return, *args)
        y += f_return*dt
    
    def Euler_symplectic(f, dt, t, y, *args):
        f(t, y, f_return, *args)
        y[0::2] += f_return[0::2]*dt
        f(t, y, f_return, *args)
        y[1::2] += f_return[1::2]*dt
        
    def velocity_Verlet(f, dt, t, y, *args):
        y[1::2] += 0.5*f_return[1::2]*dt
        y[0::2] += y[1::2]*dt
        f(t, y, f_return, *args)
        y[1::2] += 0.5*f_return[1::2]*dt

    def RK2(f, dt, t, y, *args):
        f(t, y, f_return, *args)
        k1[:] = dt*f_return
        y_temp[:] = y + k1/2. 
        f(t + dt/2., y_temp, f_return, *args) 
        k2[:] = dt*f_return 
        y += k2
    
    def RK4(f, dt, t, y, *args):
        f(t, y, f_return, *args)
        k1[:] = dt*f_return 
        y_temp[:] = y + k1/2. 
        f(t + dt/2., y_temp, f_return, *args) 
        k2[:] = dt*f_return 
        y_temp[:] = y + k2/2. 
        f(t + dt/2., y_temp, f_return, *args)
        k3[:] = dt*f_return  
        y_temp[:] = y + k3 
        f(t+dt, y_temp, f_return, *args) 
        k4[:] = dt*f_return  
        y += (k1+2.*(k2+k3)+k4)/6.

    # the function to integrate
    def f(t, y, f_return, g, epsilon, r_zero):
        # interaction with walls and gravity
        f_return[0::4] = y[1::4]
        f_return[1::4] = -y[0::4]**(m-1)
        f_return[2::4] = y[3::4]
        f_return[3::4] = -y[2::4]**(m-1) - g
        # interactions between particles
        if abs(epsilon) > 1e-6:
            for i in range(N_particles):
                x_i = y[4*i]
                y_i = y[4*i+2]
                temp_1[:] = (y[0::4]-x_i)**2 + (y[2::4]-y_i)**2
                # set the distance from the particle to itself to 1 to avoid division by zero
                #   then it should not contribute to the final sums
                temp_1[i] = 1.0
                f_return[4*i+1] += 12*epsilon*(-r_zero**12*np.sum((y[0::4]-x_i)/temp_1**7) + r_zero**6*np.sum((y[0::4]-x_i)/temp_1**4))
                f_return[4*i+3] += 12*epsilon*(-r_zero**12*np.sum((y[2::4]-y_i)/temp_1**7) + r_zero**6*np.sum((y[2::4]-y_i)/temp_1**4))

    # initial t value
    t = 0.0
    # initial dependent variable values [x, vx, y, vy]
    y = np.random.uniform(-1.0, 1.0, 4*N_particles)
    # start particles on a uniform grid
    N_particles_sqrt = int(math.ceil(np.sqrt(N_particles)))
    grid = np.linspace(-0.8, 0.8, N_particles_sqrt)
    for i in range(N_particles_sqrt):
        for j in range(N_particles_sqrt):
            if (i*N_particles_sqrt + j) > (N_particles - 1): break
            y[4*N_particles_sqrt*i+4*j] = grid[j]
            y[4*N_particles_sqrt*i+4*j+2] = grid[i]
    y[1::4] *= v_max/np.sqrt(y[1::4]**2 + y[3::4]**2)
    y[3::4] *= v_max/np.sqrt(y[1::4]**2 + y[3::4]**2)
    logger.info('starting integration')
    # plot initial positions of particles
    plot_data = np.zeros((N_particles, 2))
    # x positions
    plot_data[:,0] = y[0::4]
    # y positions
    plot_data[:,1] = y[2::4]
    plot_1.set_data('particles', plot_data)
    a = algorithm.value
    dt = prob_dt.value
    g = prob_g.value
    epsilon = prob_epsilon.value
    r_zero = prob_r_zero.value
    # initialization for velocity Verlet
    if a == 'velocity_Verlet':
        f(t, y, f_return, g, epsilon, r_zero)
    step_N = 0
    run = True
    update_N = steps_per_update.value
    while run:
        if a == 'Euler':
            Euler(f, dt, t, y, g, epsilon, r_zero)
        elif a == 'Euler_symplectic':
            Euler_symplectic(f, dt, t, y, g, epsilon, r_zero)
        elif a == 'velocity_Verlet':
            velocity_Verlet(f, dt, t, y, g, epsilon, r_zero)
        elif a == 'RK2':
            RK2(f, dt, t, y, g, epsilon, r_zero)
        elif a == 'RK4':
            RK4(f, dt, t, y, g, epsilon, r_zero)
        t += dt
        if step_N % update_N == 0:
            # x postions
            plot_data[:,0] = y[0::4]
            # y positions
            plot_data[:,1] = y[2::4]
            plot_1.set_data('particles', plot_data)
            # grab any new values from GUI
            g = prob_g.value
            epsilon = prob_epsilon.value
            r_zero = prob_r_zero.value
            update_N = steps_per_update.value
            run = start_stop.value
            yield 0.01
        step_N += 1
    # reset the stop button in case it was pushed
    logger.info('done, t = %g' % t)
