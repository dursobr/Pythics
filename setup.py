#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright 2010 - 2015 Brian R. D'Urso
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
# The module can be installed by typing
#   python setup.py install
#
# Relevant files:
#   setup.py        - controls the whole build
#   MANIFEST.in     - adds additional files/dirs added to the source build
#
# More information at:
#   http://docs.python.org/distutils/index.html
#
# Make the source package with:
#   python setup.py sdist
#
# Make the windows exe with:
#   python setup.py bdist_wininst --user-access-control='force'
#

from distutils.core import setup

setup(name='pythics',
        version='0.7.3',
        description='Python Instrument Control System',
        author='Brian R. D\'Urso',
        author_email='dursobr@gmail.com',
        url='http://code.google.com/p/pythics/',
        packages=['pythics', 'pythics.help', 'pythics.examples', 
                  'pythics.instruments', 'pythics.schema'],
        package_dir={'pythics': 'pythics'},
        package_data={'pythics': ['pythics_icon.ico', '*.txt'], 
                      'pythics.help':['*.xml', '*.png', '*.jpg', '*.txt'],
                      'pythics.examples':['*.xml', '*.png', '*.jpg', '*.txt', '*.csv'],
                      'pythics.schema':['*.xsd', '*.xml']},
        scripts=['scripts/postinstall.py'],
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Intended Audience :: Science/Research',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: GNU General Public License (GPL)',
            'Operating System :: MacOS :: MacOS X',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: POSIX',
            'Programming Language :: Python',
            'Topic :: Scientific/Engineering',
            'Topic :: Software Development',
        ],
)
