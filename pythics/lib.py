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
import time

import numpy as np


#
# A buffer for appending data to plots in chunks instead of one point at a time
#
class AppendBuffer(object):
    def __init__(self, plot, cols, length, key=None):
        self.plot = plot
        self.data = np.zeros([length, cols])
        self.length = length
        self.key = key
        self.n = 0

    def append(self, data):
        self.data[self.n] = data
        self.n += 1
        if self.n == self.length:
            if self.key is None:
                self.plot.append(self.data)
            else:
                self.plot.append(self.key, self.data)
            self.n = 0

    def flush(self):
        if self.n != 0:
            if self.key is None:
                self.plot.append(self.data[0:self.n])
            else:
                self.plot.append(self.key, self.data[0:self.n])
            self.n = 0

    def clear(self):
        self.n = 0


#
# A simple timer useful for updating the GUI every dt seconds
#
class UpdateTimer(object):
    def __init__(self, dt=1.0):
        self.dt = dt
        self.force = False
        self.last_time = time.time()

    def check(self):
        t = time.time()
        if ((t - self.last_time) >= self.dt) or self.force:
            self.last_time = t
            self.force = False
            return True
        else:
            return False

    def trigger(self):
        self.force = True


def save_array(data, filename, separator=', ', format='%e', header=None):
    with open(filename, 'w') as file:
        if header != None:
            file.write('%s\n' % header)
        for row in data:
            file.write('%s\n' % separator.join([format % val for val in row]))


def read_array(filename, separator=', ', comment='#', dtype='float'):
    with open(filename, "r") as file:
        data = []
        for line in file:
            stripped_line = line.strip()
            if len(stripped_line) != 0 and stripped_line[0] != comment:
                items = stripped_line.split(separator)
                data.append(map(np.cast[dtype], items))
        a = np.array(data, dtype=dtype)
    return(a)


#
# Writes array data to file one row at a time
#
class ArrayFile(object):
    def __init__(self, filename, separator=', ', format='%e', header=None, mode='w'):
        self.__file = open(filename, mode)
        self.separator = separator
        self.format = format
        if mode == 'w' and header != None:
            self.__file.write('%s\n' % header)

    def write(self, data):
        self.__file.write('%s\n' % self.separator.join([self.format % val for val in data]))

    def write_array(self, data):
        for row in data:
            self.__file.write('%s\n' % self.separator.join([self.format % val for val in row]))

    def flush(self):
        self.__file.flush()

    def close(self):
        self.__file.close()


#
# Circular array for storing and retrieving time series data
#
class RingBuffer(object):
    def __init__(self, length, width=1, value=0, dtype=np.float64):
        self.__width = width
        # actual array size is twice the requested
        self.__N = int(length)
        # the next place to put a value in the buffer
        self.__n = 0
        self.__data = value*np.ones((2*self.__N, self.__width), dtype=dtype)

    def clear(self, value=0):
        self.__data = 0 * self.__data + value

    def read(self, start=-1, stop=0):
        # choose the copy of the data which is guaranteed to be contiguous
        n = ((self.__n - 1) % self.__N) + self.__N + 1
        return self.__data[n+start:n+stop]

    def write(self, value):
        # put data in two places so we can always slice out a contiguous array
        n = self.__n
        m = n + self.__N
        self.__data[n] = value
        self.__data[m] = value
        self.__n = (self.__n + 1) % self.__N

    def write_array(self, value):
        # for small arrays, it may be faster to just loop over written array,
        #   for example
        #for i in range(value.shape[0]):
        #    self.write(value[i])
        # for large arrays, we can avoid loops
        n = self.__n
        m = n + self.__N
        L = value.shape[0]
        # grab only last N elements if value array is too long
        if L > self.__N:
            L = self.__N
            value = value[-L:]
        # n is smaller, so writing is contiguous starting at n
        self.__data[n:n+L] = value
        # writing at m must generally be broken up into two parts
        #   the second part must be wrapped around
        wrapped_L = m + L - 2*self.__N
        if wrapped_L <= 0:
            # no need for wrapping
            self.__data[m:m+L] = value
        else:
            unwrapped_L = L - wrapped_L
            self.__data[m:m+unwrapped_L] = value[0:unwrapped_L]
            self.__data[0:wrapped_L] = value[unwrapped_L:L]
        self.__n = (self.__n + L) % self.__N


#
# Circular array for storing and retrieving time series data
#
class CircularArray(object):
    def __init__(self, length, cols=1, dtype=np.float64):
        self.__cols = cols
        # actual array size is twice the requested
        self.__N = int(length)
        # the next place to put a value in the buffer
        self.__n_next = 0
        self.__data = np.zeros((2*self.__N, self.__cols), dtype=dtype)
        # the number of rows that have been filled, max is self.__N
        self.__n_filled = 0
        # properties of arrays
        self.ndim = 2

    def clear(self):
        self.__n_filled = 0

    def append(self, value):
        # convert the appended object to an array if it starts as something else
        if type(value) is not np.ndarray:
            value = np.array(value)
        # add the data
        if value.ndim == 1:
            # adding a single row of data
            # put data in two places so we can always find a contiguous array
            n = self.__n_next
            m = n + self.__N
            self.__data[n] = value
            self.__data[m] = value
            self.__n_next = (self.__n_next + 1) % self.__N
            self.__n_filled = min(self.__n_filled+1, self.__N)
        elif value.ndim == 2:
            # adding multiple rows of data
            # avoid loops for appending large arrays
            n = self.__n_next
            m = n + self.__N
            L = value.shape[0]
            # grab only last N elements if value array is too long
            if L > self.__N:
                L = self.__N
                value = value[-L:]
            # n is smaller, so writing is contiguous starting at n
            self.__data[n:n+L] = value
            # writing at m must generally be broken up into two parts
            #   the second part must be wrapped around
            wrapped_L = m + L - 2*self.__N
            if wrapped_L <= 0:
                # no need for wrapping
                self.__data[m:m+L] = value
            else:
                unwrapped_L = L - wrapped_L
                self.__data[m:m+unwrapped_L] = value[0:unwrapped_L]
                self.__data[0:wrapped_L] = value[unwrapped_L:L]
            self.__n_next = (self.__n_next + L) % self.__N
            self.__n_filled = min(self.__n_filled+L, self.__N)

    def __as_array(self):
        # choose the copy of the data which is guaranteed to be contiguous
        n = ((self.__n_next - 1) % self.__N) + self.__N + 1
        return self.__data[n-self.__n_filled:n]

    # some standard array methods

    @property
    def shape(self):
        return (self.__n_filled, self.__cols)

    def __getitem__(self, key):
        return self.__as_array().__getitem__(key)

    def __iter__(self):
        return self.__as_array().__iter__()

    def __len__(self):
        return self.__n_filled

    def __repr__(self):
        return self.__as_array().__repr__()

    def __setitem__(self, key, value):
        # this is inefficient but simple
        # rewrite the whole array for any change
        a = self.__as_array()
        a.__setitem__(key, value)
        self.clear()
        self.append(a)

    def __str__(self):
        return self.__as_array().__str__()

    def sum(self, *args, **kwargs):
        return self.__as_array().sum(*args, **kwargs)


class GrowableArray(object):
    def __init__(self, length, cols=1, dtype=np.float64):
        self.__cols = cols
        self.__initial_length = int(length)
        # number of rows to grow by if we run out of space
        self.__n_grow = self.__initial_length
        self.__dtype = dtype
        self.clear()
        # properties of arrays
        self.ndim = 2

    def clear(self):
        # actual array size
        self.__N = self.__initial_length
        # the next place to put a value in the buffer
        #   also the number of rows that have been filled
        self.__n = 0
        # allocate the initial data
        self.__data = np.zeros((self.__N, self.__cols), dtype=self.__dtype)

    def append(self, value):
        # convert the appended object to an array if it starts as something else
        if type(value) is not np.ndarray:
            value = np.array(value)
        # add the data
        if value.ndim == 1:
            # adding a single row of data
            n = self.__n
            if n + 1 > self.__N:
                # need to allocate more memory
                self.__N += self.__n_grow
                self.__data = np.resize(self.__data, (self.__N, self.__cols))
            self.__data[n] = value
            self.__n = n + 1
        elif value.ndim == 2:
            # adding multiple rows of data
            # avoid loops for appending large arrays
            n = self.__n
            L = value.shape[0]
            N_needed = n + L - self.__N
            if N_needed > 0:
                # need to allocate more memory
                self.__N += (N_needed / self.__n_grow + 1) * self.__n_grow
                self.__data = np.resize(self.__data, (self.__N, self.__cols))
            self.__data[n:n+L] = value
            self.__n += L

    def __as_array(self):
        return self.__data[:self.__n]

    # some standard array methods

    @property
    def shape(self):
        return (self.__n, self.__cols)

    def __getitem__(self, key):
        return self.__as_array().__getitem__(key)

    def __iter__(self):
        return self.__as_array().__iter__()

    def __len__(self):
        return self.__n

    def __repr__(self):
        return self.__as_array().__repr__()

    def __setitem__(self, key, value):
        return self.__as_array().__setitem__(key, value)

    def __str__(self):
        return self.__as_array().__str__()

    def sum(self, *args, **kwargs):
        return self.__as_array().sum(*args, **kwargs)

