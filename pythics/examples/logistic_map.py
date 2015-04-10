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
    clear(**kwargs)


def clear(messages, plot_1, plot_2, multiple_mu_initial, multiple_mu_final, **kwargs):
    plot_1.clear()
    messages.clear()
    plot_1.set_plot_properties(
        title='Logistic Map',
        x_label='time',
        y_label='x',
        x_scale='linear',
        y_scale='linear',
        aspect_ratio='auto')
    plot_2.set_plot_properties(
        title='Logistic Map',
        x_label='mu',
        y_label='x',
        x_scale='linear',
        y_scale='linear',
        tight_autoscale=True,
        aspect_ratio='auto',
        dpi=300)
    plot_1.new_curve('tx', memory='growable', animated=True, line_color='blue')
    plot_2.new_image('map', colormap='Greys', animated=False, 
                     extent=(0, multiple_mu_final.value, 0.0, 1.0))


#
# run: the simulation
#

def run_single(single_x0, single_mu, single_N, stop, messages, plot_1, plot_2, **kwargs):
    x0 = single_x0.value
    mu = single_mu.value
    N = single_N.value
    # allocate data arrays   
    xs = np.zeros(N)
    ts = np.arange(N)
    # the calculation
    messages.write('Starting calculation.\n')
    xs[0] = x0
    for i in range(N-1):
        xs[i+1] = mu*xs[i]*(1-xs[i])
    # plot all the data at the end
    data = np.column_stack((ts, xs))
    plot_1.set_data('tx', data, rescale=True)
    # reset the stop button in case it was pushed
    stop.value = False
    messages.write('Done.\n')


def run_multiple(multiple_mu_initial, multiple_mu_final, multiple_mu_N_steps, 
                 multiple_N_used, multiple_N_total, multiple_N_bins, multiple_x0, 
                 stop, messages, plot_1, plot_2, **kwargs):
    x0 = multiple_x0.value
    mu_initial = multiple_mu_initial.value
    mu_final = multiple_mu_final.value
    N_mu = multiple_mu_N_steps.value
    N_total = multiple_N_total.value
    N_used = multiple_N_used.value
    N_bins = multiple_N_bins.value
    # allocate data arrays   
    xs = np.zeros(N_total)
    ts = np.arange(N_total)
    image_data = np.zeros((N_bins, N_mu), dtype=np.uint8)
    plot_2.set_data('map', image_data)
    # the calculation
    messages.write('Starting calculation.\n')
    data = np.column_stack((ts, xs))
    plot_1.set_data('tx', data, rescale=True)
    mus = np.linspace(mu_initial, mu_final, N_mu)
    for n in range(N_mu):
        mu = mus[n]
        xs[0] = x0
        for i in range(N_total-1):
            xs[i+1] = mu*xs[i]*(1-xs[i])
        mu_data = np.histogram(xs[-N_used:], bins=N_bins, range=(0.0, 1.0))[0]
        mu_data = np.clip(mu_data, 0, 1)
        image_data[::-1,n] += mu_data
        if (n % 10) == 0:
            # update plot
            data = np.column_stack((ts, xs))
            plot_1.set_data('tx', data)
            # update image
            plot_2.set_data('map', image_data)
        if stop.value: break
    # update plot
    data = np.column_stack((ts, xs))
    plot_1.set_data('tx', data)
    # update image
    plot_2.set_data('map', image_data)
    # reset the stop button in case it was pushed5
    stop.value = False
    messages.write('Done.\n')
