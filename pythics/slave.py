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
import imp
import multiprocessing
import sys


#
# Slave holds the slave process data within the slave process itself
#
class Slave(object):
    def __init__(self, process_id, call_queue, return_queue,
                 slave_to_master_call_queue_semaphore,
                 master_to_slave_call_queue,
                 path, module_names, control_proxies):
        self.process_id = process_id
        self.slave_to_master_call_queue = call_queue
        self.slave_to_master_call_return_queue = return_queue
        self.slave_to_master_call_queue_semaphore = slave_to_master_call_queue_semaphore
        self.master_to_slave_call_queue = master_to_slave_call_queue
        self.path = path
        self.module_names = module_names
        self.modules = dict()
        self.control_proxies = control_proxies

    def process_loop(self):
        logger = multiprocessing.get_logger()
        logger.info("Starting new slave process '%s'." % self.process_id)
        # pull out a few attributes for fastest access
        control_proxies = self.control_proxies
        master_to_slave_call_queue = self.master_to_slave_call_queue
        # reinitialize control proxies to give them access to master_to_slave_call_queue
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
                    master_to_slave_call_queue.get()
                if called_module_name is not None:
                    try:
                        called_module = self.modules[called_module_name]
                        f = getattr(called_module, called_function_name)
                        logger.debug("Slave process executing '%s.%s'." % \
                                     (called_module_name,
                                     called_function_name))
                        f(**control_proxies)
                    except:
                        logger.exception('Error in slave_process_loop while executing call request from a control in master process.')
                elif called_function_name is not None:
                    # None, ProxyMessge is the signal to call a proxy method
                    m = called_function_name
                    getattr(control_proxies[m.proxy_id], m.method)(*m.args, **m.kwargs)
                else:
                    # None, None is the signal to stop the loop and exit the process
                    break
            except:
                logger.exception('Error in action process loop.')
        # shutting down, so cleanup
        for proxy in control_proxies.values():
            if hasattr(proxy, '_stop'):
                proxy._stop()
        # delete the control_proxy dict, so proxies can clean up
        del control_proxies
