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


Documentation:
--------------
The documentation is located in the pythics doc directory. The documentation 
was built with Sphinx, and can be accessed in html or pdf form.
The pdf manual is located in the pythics directory as:
Pythics.pdf
The html docs can be read with a browser by opening:
doc/_build/html/index.html 


Notes:
------
Pythics makes heavy use of matplotlib http://matplotlib.org/ 
and numpy http://www.numpy.org/.


Contributors:
-------------
Thomas Fechner, who added command-line lauching of Pythics.
Ilana Gat, who contributed several feature enhancements.
Alex Arsenovic, who wrote the initial Distutils intaller setup for Pythics.
Richard Graham, who reorganized and greatly improved the docs.


Installation Requirements
-------------------------

The following programs and libraries are required for Pythics to run:

- Python 2.6.2 or later preferred; earlier versions lack the 
  multiprocessing package

- PyQt widget toolkit for GUI, version 4.5.4 or later


The following libraries are strongly recommended for basic functionality in 
Pythics:

- NumPy array support

- matplotlib plotting library


The following libraries are optional for full functionality in Pythics:

- python Imaging Library (PIL) - for image display support, (1.1.7 or later 
  preferred)

- PyQwt widgets for scientific and engineering applications  


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

- run `python setup.py install`


Running
-------

To start Pythics:

- On Linux, go to the `pythics/pythics` directory and type 
  `python start.py`.

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
