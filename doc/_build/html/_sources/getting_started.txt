.. _getting_started:


***************
Getting started
***************

This is the primary documentation for the Python Instrument Control System, 
also known as Pythics.

Pythics is an application for running Python code intended to be used for simple 
interfaces to laboratory instruments or numerical simulations. It features a 
simple system for making graphical user interfaces (GUIs) with useful controls 
and indicators, including plotting functionality. There is a clean separation 
between the GUI and application code with multithreading and multiprocessing 
support. In this way backend code does not interfere with the functionality of 
the GUI. Pythics attempts to robustly handle all of the complex details of 
writing a program with a GUI for you, allowing you to concentrate on the 
functionality of your program.

The key goals of Pythics are:

- Provide a framework which provides a highly multiprocessing environment 
  without requiring any extra effort by the user/developer.

- Provide a simple method for specifying a GUI for typical scientific 
  applications.

- Be as Pythonic as possible.

  * Use standard library functions whenever possible.

  * Minimize introduction of new special keywords, functions, or calling 
    conventions.
    

Requirements
============

The following programs and libraries are required for Pythics to run:

- `Python 2.6`_ 2.6.2 or later preferred; earlier versions lack the 
  multiprocessing package

- PyQt_ widget toolkit for GUI, version 4.5.4 or later


The following libraries are strongly recommended for basic functionality in 
Pythics:

- NumPy_ array support

- matplotlib_ plotting library


The following libraries are optional for full functionality in Pythics:

- PIL_ python Imaging Library - for image display support, (1.1.7 or later 
  preferred)

- PyQwt_ widgets for scientific and engineering applications  


The following additional packages may be helpful for writing scientific code 
for Pythics:

- PyVISA_ for communicating with VISA laboratory instruments

- pySerial_ for communicating with laboratory instruments by RS-232

- SciPy_ for additional numerical processing routines


Installation
============

Pythics uses Python Distutils for installation. Installers are available for 
some platforms. 

On Windows, run the installer (.exe). It will install Pythics and place a 
shortcut on your desktop to launch Pythics.

If an installer is not available for your platform, you can install from a 
source distribution (.tar.gz or .zip):

- Unpack the archive file.

- run `python setup.py install`


Running
=======

To start Pythics:

- On Linux, go to the `pythics/pythics` directory and type 
  `python pythics-run.py`.

- On Windows, double-click on the shortcut created on your desktop by the 
  installer or go to the `pythics/pythics` directory and double-click on 
  `pythics-run.py`.

- You can also start pythics from the command line with options as:
    Usage: pythics-run.py [options]

    Options: 

    -h         show help text then exit
    -a         selects startup html file
    -v         selects verbose mode
    -d         selects debug mode
    --help     same as -h
    --app      same as -a
    --verbose  same as -v
    --debug    same as -d


Using Pythics
-------------

Once Pythics is running, virtual instruments (VIs) can be opened and controlled 
though a combination of the Pythics menus and the VI's GUI. Interaction with an 
individual VI's GUI is not covered here, because it depends on the details of 
VI. Here we describe the operation of Pythics through the menus, which provide
basic control of VI operations.

File Menu

- Open...
- Close
- Close All
- Reload

- Open Workspace...
- Save Workspace
- Save Workspace As...

- Page Setup...
- Print Preview
- Print...

- Exit

Edit Menu

- Cut 
- Copy
- Paste
- Delete

Parameters

- Load Defaults
- Load..._pySerial
- Save As Defaults
- Save As...




.. _`Python 2.6`: http://www.python.org/download/releases/2.6/

.. _PyQt: http://www.riverbankcomputing.co.uk/software/pyqt/intro

.. _PyQwt: http://pyqwt.sourceforge.net/

.. _NumPy: http://numpy.scipy.org/

.. _PIL: http://www.pythonware.com/products/pil/

.. _matplotlib: http://matplotlib.sourceforge.net/

.. _PyVISA: http://pyvisa.sourceforge.net/

.. _pySerial: http://pyserial.sourceforge.net/

.. _SciPy: http://www.scipy.org/

