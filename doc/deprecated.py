#
#  Copyright 2011 - 2013 Brian R. D'Urso
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

# this file is used to generate documentation with Sphinx and autodoc

from pythics.deprecated_mpl_proxy import *

keys = globals().keys()

for k in keys:
    # rename classes and make them look like they came from this module
    #   for sphinx autodoc
    if 'Proxy' in k:
        cls = globals()[k]
        #print cls
        old_name = cls.__name__
        # strip the string 'Proxy' off the end of each name
        new_name = old_name[0:-5]
        cls.__name__ = new_name
        cls.__module__ = 'deprecated'
        globals().pop(old_name)
        globals()[new_name] = cls

del keys, k, cls, old_name, new_name
