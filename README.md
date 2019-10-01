Pythics README
==============

Pythics is an application for running Python code intended to be used for 
simple interfaces to laboratory instrument or numerical simulations. It 
features a simple system for making graphical user interfaces (GUIs), useful 
controls including plotting, clean separation between GUI and application code, 
and multithreading and multiprocessing so running backend code does not 
interfere with the functionality of the GUI. Pythics attempts to robustly 
handle all of the complex details of writing a program with a GUI for you, 
allowing you to concentrate on the functionality of your program.

This is the first major public release of Pythics for several years, with
updates from the last public release including a port to Python3, Qt5, and 
Matplotlib 3. Almost all user code will have to be updated to be used with this
new version of Pythics, both because of the new Python version and the new 
consolidated Main control.


Documentation:
--------------
The documentation and many examples are built in to pythics under the help 
menu. The code used to generate the help is in the pythics/help directory,
and many further examples are in pythics/examples.


Notes:
------
Pythics makes heavy use of matplotlib http://matplotlib.org/ 
and numpy http://www.numpy.org/.


Contributors:
-------------
Thomas Fechner, who added command-line launching of Pythics.
Ilana Gat, who contributed several feature enhancements.
Alex Arsenovic, who wrote the initial Distutils installer setup for Pythics.
Richard Graham, who reorganized and greatly improved the docs.


Installation Requirements
-------------------------

The following programs and libraries are required for Pythics to run:

- Python 3.x.

- PyQt5 or PySide2 widget toolkit for GUI.


The following libraries are strongly recommended for basic functionality in 
Pythics:

- NumPy array support

- matplotlib (3.0.x or later) plotting library.

- lxml for better XML error reporting.


The following additional packages may be helpful for writing scientific code 
for Pythics:

- PyVISA for communicating with VISA laboratory instruments

- pySerial for communicating with laboratory instruments by RS-232

- SciPy for additional numerical processing routines


Installation
------------

Pythics uses Python Distutils for installation. Installers are available for 
some platforms. 

On Windows, run the installer (.exe). It will install Pythics and place a 
shortcut on your desktop to launch Pythics.

If an installer is not available for your platform, you can install from a 
source distribution (.tar.gz or .zip):

- Unpack the archive file.

- run `python3 setup.py install`


Running
-------

To start Pythics:

- On Linux, go to the `pythics/pythics` directory and type 
  `python3 start.py`.

- On Windows, double-click on the shortcut created on your desktop by the 
  installer or go to the `pythics/pythics` directory and double-click on 
  `start.py`.

- You can also start pythics from the command line with options as:
    Usage: python start.py [options]

    Options: 

    -h         show help text then exit
    -a         selects startup html file
    -v         selects verbose mode
    -d         selects debug mode
    --help     same as -h
    --app      same as -a
    --verbose  same as -v
    --debug    same as -d