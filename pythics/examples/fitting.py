#
#  Physics 1321: Computational Methods in Physics
#  University of Pittsburgh
#  by Brian R. D'Urso
#

#
# load libraries
#
import math

import numpy as np
import scipy.optimize


def initialize(shell, **kwargs):
    shell.interact(kwargs.copy())
    clear(**kwargs)


def clear(messages, plot, **kwargs):
    plot.clear()
    messages.clear()
    plot.set_plot_properties(
        title='Fit',
        x_label='x',
        y_label='y',
        x_scale='linear',
        y_scale='linear',
        aspect_ratio='auto')
    plot.new_curve('data', line_style='', marker_style='o', marker_color='blue')
    plot.new_curve('fit', memory='growable', length=100, animated=True, 
                   line_style='-', line_color='red')


def load(file_picker, messages, plot, **kwargs):
    # load and plot the data
    global data
    filename = file_picker.value
    data = np.loadtxt(filename, delimiter=',')
    plot.set_data('data', data)


def plot_guess(function, fit_type, initial_guess, messages, plot, **kwargs):
    global data
    xs = data[:,0]
    initial_fit_parameters = np.array(eval(initial_guess.value))
    # the function we are trying to fit to the data
    function_string = function.value
    def f(x, *p):
        y = eval(function_string)
        plot.set_data('fit', np.column_stack((x, y)))
        return y
    f(xs, *initial_fit_parameters)
    

def run(function, fit_type, initial_guess, messages, plot, **kwargs):
    global data
    xs = data[:,0]
    ys = data[:,1]
    initial_fit_parameters = np.array(eval(initial_guess.value))
    # the function we are trying to fit to the data
    function_string = function.value
    def f(x, *p):
        y = eval(function_string)
        plot.set_data('fit', np.column_stack((x, y)))
        return y
    # the actual fitting
    if fit_type.value == 'linear':
        A = np.column_stack([xs, np.ones(len(xs))])
        m, c = np.linalg.lstsq(A, ys)[0]
        messages.write('slope = %g, intercept = %g\n' % (m, c))
        plot.set_data('fit', np.column_stack((xs, m*xs+c)))
    else:
        plot.set_data('fit', np.column_stack((xs, f(xs, *initial_fit_parameters))))
        fit, cov = scipy.optimize.curve_fit(f, xs, ys, p0=initial_fit_parameters)
        plot.set_data('fit', np.column_stack((xs, f(xs, *fit))), rescale=True)
        messages.write('Fit p = %s.\n' % str(fit))
        messages.write('Uncertainties eps = %s.\n' % str(np.sqrt(np.diag(cov))))
