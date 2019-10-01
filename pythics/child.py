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
import imp
import multiprocessing
import sys
import weakref


#
# Child holds the child process data within the child process itself
#
class Child(object):
    def __init__(self, process_id, call_queue, return_queue,
                 child_to_parent_call_queue_semaphore,
                 parent_to_child_call_queue,
                 path, module_names, control_proxies):
        self.process_id = process_id
        self.child_to_parent_call_queue = call_queue
        self.child_to_parent_call_return_queue = return_queue
        self.child_to_parent_call_queue_semaphore = child_to_parent_call_queue_semaphore
        self.parent_to_child_call_queue = parent_to_child_call_queue
        self.path = path
        self.module_names = module_names
        self.modules = dict()
        self.control_proxies = control_proxies

    def process_loop(self):
        self.weak_proxy_refs = weakref.WeakSet()
        logger = multiprocessing.get_logger()
        logger.info("Starting new child process '%s'." % self.process_id)
        # pull out a few attributes for fastest access
        control_proxies = self.control_proxies
        parent_to_child_call_queue = self.parent_to_child_call_queue
        # reinitialize control proxies to give them access to parent_to_child_call_queue
        for proxy in control_proxies.values():
            if hasattr(proxy, '_start'):
                proxy._start(self)
        # load required modules
        if self.path not in sys.path:
            sys.path.append(self.path)
        for module_name in self.module_names:
            fp, pathname, description = imp.find_module(module_name)
            try:
                self.modules[module_name] = imp.load_module(module_name, fp,
                                                        pathname, description)
            finally:
                if fp:
                    fp.close()
        # the event loop in the action process
        while True:
            try:
                called_module_name, called_function_name = \
                    parent_to_child_call_queue.get()
                if called_module_name is not None:
                    try:
                        called_module = self.modules[called_module_name]
                        f = getattr(called_module, called_function_name)
                        logger.debug("Child process executing '%s.%s'." % \
                                     (called_module_name,
                                     called_function_name))
                        f(**control_proxies)
                    except:
                        logger.exception('Error in child_process_loop while executing call request from a control in parent process.')
                elif called_function_name is not None:
                    # None, ProxyMessge is the signal to call a proxy method
                    m = called_function_name
                    getattr(control_proxies[m.proxy_id], m.method)(*m.args, **m.kwargs)
                else:
                    # None, None is the signal to stop the loop and exit the process
                    break
            except:
                logger.exception('Error in action process loop.')
        logger.info("Shutting down child process '%s'." % self.process_id)
        # shutting down, so cleanup
        for proxy in control_proxies.values():
            if hasattr(proxy, '_stop'):
                proxy._stop()
        logger.debug("Called _stop() on Control proxies in child process '%s'." % self.process_id)
        while len(self.weak_proxy_refs) > 0:
            proxy = self.weak_proxy_refs.pop()
            if hasattr(proxy, '_mark_deleted'):
                proxy._mark_do_not_delete_original()
        logger.debug("Called _mark_deleted() on AutoProxies in child process '%s'." % self.process_id)
