#!/usr/bin/env python

import os, os.path
import sys
import distutils.sysconfig as sysconfig

# use this to install a shortcut on the desktop of the installer only
#desktop = get_special_folder_path("CSIDL_DESKTOPDIRECTORY")

# use this to install a shortcut on the desktop of all users
desktop = get_special_folder_path("CSIDL_COMMON_DESKTOPDIRECTORY")

shortcut = os.path.join(desktop, 'Pythics.lnk')
examples = os.path.join(sysconfig.get_python_lib(True), 'pythics', 'start.py')

if sys.argv[1] == '-install':
    create_shortcut(examples, 'Start Pythics', shortcut)
    print 'Created Pythics shortcut on desktop.'
elif os.path.exists(shortcut):
    os.remove(shortcut)
