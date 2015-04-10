# -*- coding: utf-8 -*-
#
# Copyright 2008 - 2014 Brian R. D'Urso
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
import types
import multiprocessing


#
# Object to send method call requests to proxies
#
class ProxyMessage(object):
    def __init__(self, proxy_id, method, *args, **kwargs):
        self.proxy_id = proxy_id
        self.method = method
        self.args = args
        self.kwargs = kwargs


#
# used to transfer proxy keys
#
class ProxyKey(object):
    def __init__(self, key, cache=False):
        # SPEED UP USING __slots__ ???????????????????????????????????????????
        self.key = key
        self.cache = cache


#
# use to transfer callback functions from slave to master process
#
class FunctionProxy(object):
    def __init__(self, f):
        self.name = f.__module__ + '.' + f.__name__


#
# classes to signal exceptions across threads
#
class CrossProcessExceptionProxy(object):
    def __init__(self, message):
        self.message = message


class CrossProcessException(Exception):
    pass


#
# base class for control proxies
#
class ControlProxy(object):
    def __init__(self, key):
        self._key = key

    def _start(self, process):
        self._process = process
        self._process_id = self._process.process_id
        self._slave_to_master_call_queue = self._process.slave_to_master_call_queue
        self._slave_to_master_call_return_queue = self._process.slave_to_master_call_return_queue
        self._slave_to_master_call_queue_semaphore = self._process.slave_to_master_call_queue_semaphore

    def _call_method(self, f, *args, **kwargs):
        # wait until this process has few enough requests left in the queue
        #  semaphore is released by GUI process once request has executed
        self._slave_to_master_call_queue_semaphore.acquire()
        self._slave_to_master_call_queue.put((self._process_id, f, args, kwargs))
        r = self._slave_to_master_call_return_queue.get()
        # check if r is an exception
        #  if it is and exception, re-raise it in slave process (here)
        if type(r) == CrossProcessExceptionProxy:
            message = "An exception '%s' was raised in the master process." % r.message
            raise CrossProcessException(message)
        else:
            return r

    def _call_method_no_return(self, f, *args, **kwargs):
        # wait until this process has few enough requests left in the queue
        #  semaphore is released by master process once request has executed
        self._slave_to_master_call_queue_semaphore.acquire()
        self._slave_to_master_call_queue.put((self._process_id, f, args, kwargs))

    def _get_class(self):
        return None


class AutoProxy(ControlProxy):
    def __init__(self, key, enable_cache=False):
        ControlProxy.__init__(self, key)
        self._enable_cache = enable_cache

    def _start(self, *args, **kwargs):
        ControlProxy._start(self, *args, **kwargs)
        self._start_args = args
        self._start_kwargs = kwargs

    def __getattr__(self, name):
        if name.startswith('_'):
            # SHOULD RAISE ATTRIBUTE ERROR?
            #return object.__getattribute__(self, name)
            # shouldn't have gotten here if it is defined
            raise AttributeError("'%s' is not defined." % name)
        else:
            r = self._call_method('get_Proxy_attr',
                                  self._key, name)
            ret = self._keys_to_proxies(r)
            if self._enable_cache and (type(r) == ProxyKey) and (r.cache):
                # cache the ProxyKey for future use
                object.__setattr__(self, name, ret)
            return ret

    def __setattr__(self, name, value):
        if name.startswith('_'):
            object.__setattr__(self, name, value)
        else:
            v = self._proxies_to_keys(value)
            self._call_method_no_return('set_Proxy_attr',
                                        self._key, name, v)

    def __del__(self):
        # tell master process to delete original object
        # catch Exceptions since other parts may have already been destroyed
        try:
            self._call_method_no_return('delete_Proxy', self._key)
        except Exception as e:
            logger = multiprocessing.get_logger()
            logger.debug('Exception during AutoProxy __del__:' + str(e))

    def __call__(self, *args, **kwargs):
        # this is here for AutoProxies of functions
        a = self._proxies_to_keys(args)
        kwa = self._proxies_to_keys(kwargs)
        r = self._call_method('call_Proxy', self._key, *a, **kwa)
        return self._keys_to_proxies(r)

    def _to_key(self):
        return self._key

    def _proxies_to_keys(self, value):
        # convert proxies to keys to send to master process
        t = type(value)
        if t is AutoProxy:
            # some other type that has to be accessed by proxy
            #  because it may not be picklable
            return value._to_key()
        elif t is list:
            r = list()
            for v in value:
                r.append(self._proxies_to_keys(v))
            return r
        elif t is tuple:
            r = list()
            for v in value:
                r.append(self._proxies_to_keys(v))
            return tuple(r)
        elif t is dict:
            r = dict()
            for k, v in value.iteritems():
                r[k] = self._proxies_to_keys(v)
            return r
        elif t is types.FunctionType:
            return FunctionProxy(value)
        else:
            # hopefully just a picklable type
            return value

    def _keys_to_proxies(self, value):
        # convert keys from master process to proxies
        t = type(value)
        if t is ProxyKey:
            # some other type that has to be accessed by proxy
            #  because it may not be picklable
            r = AutoProxy(value)
            r._start(*self._start_args, **self._start_kwargs)
            return r
        elif t is list:
            # have to check for ProxyKeys in the list
            r = list()
            for v in value:
                r.append(self._keys_to_proxies(v))
            return r
        elif t is tuple:
            # have to check for ProxyKeys in the tuple
            r = list()
            for v in value:
                r.append(self._keys_to_proxies(v))
            return tuple(r)
        elif t is dict:
            # have to check for ProxyKeys in the dict
            r = dict()
            for k, v in value.iteritems():
                r[k] = self._keys_to_proxies(v)
            return r
        else:
            # hopefully just a picklable type
            return value

    def __dir__(self):
        c_dir = self._call_method('call_Proxy_method', self._key, '_dir')
        p_dir = vars(self).keys()
        return c_dir + p_dir

    def _get__doc__(self):
        return self._call_method('get_Proxy_attr', self._key, '__doc__')

    __doc__ = property(_get__doc__)

    def _get_class(self):
        # useful for getting information about the original class,
        #  used for extracting help information
        r = self._call_method('get_Proxy_attr', self._key, '__class__')
        return self._keys_to_proxies(r)

    ###########################################################################
    # EXTRA METHODS THAT NEED WORK

    def __len__(self):
        r = self._call_method('call_Proxy_method', self._key, '__len__')
        return r

    def __getitem__(self, key):
        r = self._call_method('call_Proxy_method', self._key, '__getitem__', key)
        return r

    def __setitem__(self, key, value):
        r = self._call_method('call_Proxy_method', self._key, '__setitem__', key, value)
        return r

    def __delitem__(self, key):
        r = self._call_method('call_Proxy_method', self._key, '__delitem__', key)
        return r

    # __iter__ UNTESTED!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    def _get__iter__(self):
        r = self._call_method('get_Proxy_attr', self._key, '__iter__')
        return self._keys_to_proxies(r)

    __iter__ = property(_get__iter__)

#    # __name__ UNTESTED!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#    def _get__name__(self):
#        r = self._call_method('get_Proxy_attr', self._key, '__name__')
#        return r
#
#    __name__ = property(_get__name__)

    def __repr__(self):
        r = self._call_method('call_Proxy_method', self._key, '__repr__')
        return r

    def __str__(self):
        r = self._call_method('call_Proxy_method', self._key, '__str__')
        return r


class PartialAutoProxy(AutoProxy):
    def __init__(self, local_attrs, *args, **kwargs):
        AutoProxy.__init__(self, *args, **kwargs)
        self._local_attrs = local_attrs

    def __setattr__(self, name, value):
        # must check in this order - self.local_attrs may not have been set yet
        if name.startswith('_') or (name in self._local_attrs):
            object.__setattr__(self, name, value)
        else:
            v = self._proxies_to_keys(value)
            self._call_method_no_return('set_Proxy_attr',
                                        self._key, name, v)
