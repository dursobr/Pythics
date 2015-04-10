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
import logging, multiprocessing
import inspect
import random, time

try:
    import PIL.Image
except:
    logger = multiprocessing.get_logger()
    logger.warning("'Python Imaging Library (PIL)' is not available.")
try:
    import numpy as np
    import numpy.random as npr
    from numpy import pi
except:
    logger = multiprocessing.get_logger()
    logger.warning("'numpy' is not available.")

# these is only needed for help generation, you should not normally import them
import pythics.controls, pythics.proxies


#
# private data shared among functions
#
class Private(object):
    pass

private = Private()


#
# Extract and display help for an object
#
def help_dynamic(inspect_master, ob):
    # start with the __doc__ from the original object
    cls = ob._get_class()
    members = inspect_master.getmembers(cls)
    text = inspect_master.getdoc(cls)
    text = ''.join([text, '\n\n', 'Methods and attributes:'])
    for k, v in members:
        if not k.startswith('_'):
            doc = inspect_master.getdoc(v)
            if inspect_master.ismethod(v):
                argspec = inspect_master.getargspec(v)
                k = ''.join(['*', k, '*', inspect_master.formatargspec(argspec[0], argspec[1], argspec[2], argspec[3])])
            else:
                k = ''.join(['*', k, '*'])
            # now indent all lines in k by 4 spaces
            d = str(doc).replace('\n', '\n    ')
            text = ''.join([text, '\n\n  ', k, ':\n    ', d])
    # now get proxy data
    members = inspect.getmembers(ob.__class__)
    for k, v in members:
        if not k.startswith('_'):
            doc = inspect.getdoc(v)
            if inspect.ismethod(v):
                argspec = inspect.getargspec(v)
                k = ''.join(['*', k, '*', inspect.formatargspec(*argspec)])
            else:
                k = ''.join(['*', k, '*'])
            # now indent all lines in k by 4 spaces
            d = str(doc).replace('\n', '\n    ')
            text = ''.join([text, '\n\n  ', k, ':\n    ', d])
    return text


def help_static(cls, proxy_cls):
    # start with the __doc__ from the original object
    members = inspect.getmembers(cls)
    text = inspect.getdoc(cls)
    text = ''.join([text, '\n\n', 'Methods and attributes:'])
    for k, v in members:
        if not k.startswith('_'):
            doc = inspect.getdoc(v)
            if inspect.ismethod(v):
                argspec = inspect.getargspec(v)
                k = ''.join(['*', k, '*', inspect.formatargspec(*argspec)])
            else:
                k = ''.join(['*', k, '*'])
            # now indent all lines in k by 4 spaces
            d = str(doc).replace('\n', '\n    ')
            text = ''.join([text, '\n\n  ', k, ':\n    ', d])
    # now get proxy data
    if proxy_cls is not None:
        members = inspect.getmembers(proxy_cls)
        for k, v in members:
            if not k.startswith('_'):
                doc = inspect.getdoc(v)
                if inspect.ismethod(v):
                    argspec = inspect.getargspec(v)
                    k = ''.join(['*', k, '*', inspect.formatargspec(*argspec)])
                else:
                    k = ''.join(['*', k, '*'])
                # now indent all lines in k by 4 spaces
                d = str(doc).replace('\n', '\n    ')
                text = ''.join([text, '\n\n  ', k, ':\n    ', d])
    return text


#
# Initialize on startup
#
def Initialize(**kwargs):
    logger = multiprocessing.get_logger()
    logger.info('Initialized demo.py')
    kwargs['globals'].test_global = 1
    # display help

    kwargs['introduction'].value = \
    """***************
Getting Started
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


***********
Programming
***********

Overview
========

While the underlying architecture of Pythics is generally hidden from the user,
some knowledge of the structure may be helpful in understanding how to build and
run programs under Pythics. When running user code, Pythics runs as a primary
process which controls the GUI, and an additional process for each loaded user
*program*, which we will refer to as a virtual instrument (VI). The GUI process
itself uses multiple threads to handle the GUI and communication with the VI
subprocess, while each VI has one primary thread and possibly additional timer
threads in a subprocess.

Each VI subprocess is actually a true separate process handled with the Python
multiprocessing package. As a result, the VI subprocesses and GUI can generally
run without blocking each other, and the VI subprocesses can even be
distributed over multiple processors or cores as supported by the operating
system. Additionally, even if one VI subprocess crashes, for example due to an
error accessing low-level hardware, the Pythics GUI and other VIs should be
undisturbed. Pythics handles all communication between the VI subprocesses and
the GUI process, and provides means of sharing data between VIs.

Writing code for a new VI in Pythics generally consists of writing two
components:

#. A single XML file (a subset of XHTML) to layout the graphical user interface.

#. One or more text files containing Python code. These give functionality to
   the VI.

The XML file is loaded by the GUI process in order to set up the interface,
while the Python code files are loaded and ultimately executed in a VI
subprocess. For each XML file loaded a new tab will be created in the
Pythics window which holds the corresponding VI GUI and a VI subprocess which
handles the associated functionality.

The XML file specifies the layout for the controls in the GUI with a structure
very similar to that used to describe the layout of a web page. Simple tables,
styles, alignments, etc. of text and controls are supported. In the XML file,
parameters may also be passed to controls to setup the behavior of the
controls. The XML file can also direct Pythics to load files which contain
Python code, for example in order to respond to a button press.

The second VI component is one or more text files which contain Python code
and are loaded based on requests in the XML file. The Python code typically
takes the form of a series of Python functions with a particular format. Each
function to be called from the GUI should take an indefinite number of keyword
arguments. In practice, when a GUI control calls a function from one of these
files, Pythics passes the function an object for each control in the GUI with
a `id` attribute. The `id` attribute is used as the name of the
corresponding keyword argument. Additional functions or other code may be
included in the Python code files for use within a VI subprocess. It may sound
complex, but the examples show that this actually a simple and effective
protocol.


XML/HTML File Format
====================

The file format which describes the GUI layout in Pythics is an XML-compliant
HTML format, similar to a subset of XHTML. Elements (text, controls, etc.)
within the XML file are controlled by up to three sources within the XML file
in addition to the document structure itself: a cascading style sheet (CSS)
which specifies element *properties* and element *attributes*. The
CSS is located in a `<style type='text/css'>` element in the document
`<head>` , and will be described in the section below.

A nearly minimal XML document for Pythics has a `head` with `title` and `style`
elements, and a `body` which contains the controls and other GUI layout
elements:

<html>
    <head>
        <title>Hello World</title>
        <style type='text/css'>
            <!-- Style Sheet (CSS) goes here -->
        </style>
    </head>
    <body>
        <h1>Hello World</h1>
        <!-- more elements go here for GUI layout -->
    </body>
</html>

The `head` is actually optional, although the defaults that are used without a
`head` are typically not desirable.


HTML Elements
-------------

Described below under `Basic Elements`.


Cascading Style Sheets (CSS)
----------------------------

A VI's appearance can be specified in a Cascading Style Sheet (CSS), enclosed
between `<style type='text/css'>` and  `</style>` tags within the document
`head`. The style sheet consist of a series of entries separated by white space
(new lines or spaces) of the form:
*selector{property1:value1; property2:value2}*
where there may be an arbitrary number of *property:value* pairs separated
by semicolons. The available properties and example values are given below.

The *selector* in a CSS entry may take one of five forms. In order of increasing
specificity, these are:  *tag*, .*class*, *tag*.*class*, *#id*, and
*tag#id*. When Pythics encounter an Pythics encounters an XML element in the
body of the document, it searches for a style *property* of a given *element*
as follows, where the first match encountered is used:

#. If the element has a `id` attribute: An entry in the style sheet of the form
   *tag#id*, where *tag* is replaced with the element's *tag*, and *id* is
   replaced with the element's `id` attribute.

#. If the element has a `id` attribute: An entry in the style sheet of the form
   *#id*, where *id* is replaced with the element's `id` attribute.

#. If the element has a `class` attribute: An entry in the style sheet of the
   form *tag.class*, where *tag* is replaced with the element's *tag*, and
   *class* is replaced with the element's *class* attribute.

#. If the element has a `class` attribute: An entry in the style sheet of the
   form *.class*, where *class* is replaced with the element's *class*
   attribute.

#. An entry matching the element *tag*.

#. If no entry has been found, the process stated above is repeated for the
   parent element containing the original element. As long as no entry is found,
   the search keeps proceeding to parent elements until the `body` tag is
   reached, which contains a default value for every property.


The following properties can be set in style sheets. Not all properties have
meaning for all element types.

==================  ===============================  ===========  ==============
Property            Description                      Default      Applies to
==================  ===============================  ===========  ==============
`align`             Alignment of element             `left`       all elements
`background-color`  RGB background color             `#eeeeee`    body only
`margin`            Margin on left and right side    `10px`       body only
`padding`           Space around element             `5px`        all elements
`color`             Text color                       `black`      text elements
`font-size`         Text size                        `12pt`       text elements
`font-family`       Family                           `default`    text elements
`font-style`        Style                            `normal`     text elements
`font-weight`       Weight                           `normal`     text elements
==================  ===============================  ===========  ==============

Here is an example style sheet:

<style type='text/css'>
body {background-color: #eeeeee; margin: 10px; padding: 5px}
a {align: left; color: black; font-size: 8pt; font-family: default; font-style: normal; font-weight: normal}
p {align: left; color: black; font-size: 8pt; font-family: default; font-style: normal; font-weight: normal}
h1 {align: center; font-size: 22pt; font-family: default; font-style: normal; font-weight: bold}
h2 {align: left; font-size: 18pt; font-family: default; font-style: normal; font-weight: normal}
h3 {align: left; font-size: 14pt; font-family: default; font-style: normal; font-weight: normal}
h4 {align: left; font-size: 12pt; font-family: default; font-style: normal; font-weight: normal}
h5 {align: left; font-size: 10pt; font-family: default; font-style: normal; font-weight: normal}
h6 {align: left; font-size: 8pt; font-family: default; font-style: normal; font-weight: normal}
object {align: left}
table {align: center}
.cells {align: left; padding: 1px}
.compact {padding: 0px}
</style>


Controls
========

object *parameters* (for controls (`object`) elements only)

A quick example illustrates the differences between object attributes and
parameters::

    <object classid='NumBox' id='voltage' width='200'>
        <param name='digits' value='3'/>
        <param name='read_only' value='True'/>
    </object>

In this case, we refer to `id`, `classid`, `width` as `attributes` of `object`,
while we refer to `digits` and `read_only` as `parameters` of `object`, since
they are in `param` elements. Note that `param` elements can only be present
inside of `object` elements.


Common Attributes
-----------------

Attributes:

- `classid`: A string indicating the type of control to be inserted. For
  standard controls, only the name of the control is needed. For custom
  controls, it should be of the form 'module.class', where `module` is the name
  of the module to be imported to find the control class.

- `id`: A string used for identifying the control in the html style sheet and
  used as the name of the keyword argument when the control is passed to VI
  Python code.

- `width`: A string giving the width of the control in pixels (default) or in
  percent of the window width if the string ends in `%`.

- `height`: A string giving the height of the control in pixels. Many controls
  have a reasonable default height so this attribute may not be needed for all
  controls.
"""

    kwargs['element_help'].value = \
    """HTML Elements
-------------

- `<html>`:
    begin and end `html` tags should surround the whole document

- `<head>`:
    used to surround the header of the document, which contains `title` and
    `style` elements

- `<style type='text/css'>`:
    Contains style information, such as fonts and colors, in CSS format.

- `<title>`:
    The text between `title` start and end tags will be used as the tab title
    and the Pythics window title when the tab is selected

- `<body>`:
    surrounds the main body of the html document (everything but the document
    header)

- `<h1>`, `<h2>`, ... `<h6>`:
    text placed on its own line, typically used for titles or section names

- `<a>`:
    anchor: With parameter 'href', a link to another part of your document.
    With paramenter 'id', a location in your document that can be linked to.

- `<p>`:
    fixed text which is not on its own line

- `<hr/>`:
    insert a horizontal line, typeically as a separator between sections (no
    closing tag needed)

- `<br/>`:
    insert a line break to start the next elements on a new line (no closing
    tag needed)

- `<table>`:
    use a table to arrange elements

- `<tr>`:
    table row: surrounds a table row.

- `<td>`:
    table column: surrounds a table column.

- `<object>`:
    used to include widgets such as buttons, text boxes, etc.

- `<param>`:
    Used within an object to pass additional parameters."""

    kwargs['QWidgets_help'].value = \
    """Arbitrary PyQt-compatible widgets can be used within Pythics. They are
included with the `classid` parameter of an `object`, as with other controls.
The full include name must be specified, e.g.:
<object classid='PyQt4.QtGui.QCalendarWidget' id='calendar' width='500' height='300'></object>

All methods and attributes normally accesible from Python are accessible in
Pythics. If you need access to a library to create objects to be passed to the
control, use an `Import` control rather than directly importing the library to
allow the objects to be created in the correct process.

This capability can be useful for PyQt controls that are not specifially
supported by Pythics, or for external libraries such as pyqtgraph, a fast
ploting library that could be useful for real-time plotting."""

    kwargs['copying'].value = \
    """                    GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007

 Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.

                            Preamble

  The GNU General Public License is a free, copyleft license for
software and other kinds of works.

  The licenses for most software and other practical works are designed
to take away your freedom to share and change the works.  By contrast,
the GNU General Public License is intended to guarantee your freedom to
share and change all versions of a program--to make sure it remains free
software for all its users.  We, the Free Software Foundation, use the
GNU General Public License for most of our software; it applies also to
any other work released this way by its authors.  You can apply it to
your programs, too.

  When we speak of free software, we are referring to freedom, not
price.  Our General Public Licenses are designed to make sure that you
have the freedom to distribute copies of free software (and charge for
them if you wish), that you receive source code or can get it if you
want it, that you can change the software or use pieces of it in new
free programs, and that you know you can do these things.

  To protect your rights, we need to prevent others from denying you
these rights or asking you to surrender the rights.  Therefore, you have
certain responsibilities if you distribute copies of the software, or if
you modify it: responsibilities to respect the freedom of others.

  For example, if you distribute copies of such a program, whether
gratis or for a fee, you must pass on to the recipients the same
freedoms that you received.  You must make sure that they, too, receive
or can get the source code.  And you must show them these terms so they
know their rights.

  Developers that use the GNU GPL protect your rights with two steps:
(1) assert copyright on the software, and (2) offer you this License
giving you legal permission to copy, distribute and/or modify it.

  For the developers' and authors' protection, the GPL clearly explains
that there is no warranty for this free software.  For both users' and
authors' sake, the GPL requires that modified versions be marked as
changed, so that their problems will not be attributed erroneously to
authors of previous versions.

  Some devices are designed to deny users access to install or run
modified versions of the software inside them, although the manufacturer
can do so.  This is fundamentally incompatible with the aim of
protecting users' freedom to change the software.  The systematic
pattern of such abuse occurs in the area of products for individuals to
use, which is precisely where it is most unacceptable.  Therefore, we
have designed this version of the GPL to prohibit the practice for those
products.  If such problems arise substantially in other domains, we
stand ready to extend this provision to those domains in future versions
of the GPL, as needed to protect the freedom of users.

  Finally, every program is threatened constantly by software patents.
States should not allow patents to restrict development and use of
software on general-purpose computers, but in those that do, we wish to
avoid the special danger that patents applied to a free program could
make it effectively proprietary.  To prevent this, the GPL assures that
patents cannot be used to render the program non-free.

  The precise terms and conditions for copying, distribution and
modification follow.

                       TERMS AND CONDITIONS

  0. Definitions.

  "This License" refers to version 3 of the GNU General Public License.

  "Copyright" also means copyright-like laws that apply to other kinds of
works, such as semiconductor masks.

  "The Program" refers to any copyrightable work licensed under this
License.  Each licensee is addressed as "you".  "Licensees" and
"recipients" may be individuals or organizations.

  To "modify" a work means to copy from or adapt all or part of the work
in a fashion requiring copyright permission, other than the making of an
exact copy.  The resulting work is called a "modified version" of the
earlier work or a work "based on" the earlier work.

  A "covered work" means either the unmodified Program or a work based
on the Program.

  To "propagate" a work means to do anything with it that, without
permission, would make you directly or secondarily liable for
infringement under applicable copyright law, except executing it on a
computer or modifying a private copy.  Propagation includes copying,
distribution (with or without modification), making available to the
public, and in some countries other activities as well.

  To "convey" a work means any kind of propagation that enables other
parties to make or receive copies.  Mere interaction with a user through
a computer network, with no transfer of a copy, is not conveying.

  An interactive user interface displays "Appropriate Legal Notices"
to the extent that it includes a convenient and prominently visible
feature that (1) displays an appropriate copyright notice, and (2)
tells the user that there is no warranty for the work (except to the
extent that warranties are provided), that licensees may convey the
work under this License, and how to view a copy of this License.  If
the interface presents a list of user commands or options, such as a
menu, a prominent item in the list meets this criterion.

  1. Source Code.

  The "source code" for a work means the preferred form of the work
for making modifications to it.  "Object code" means any non-source
form of a work.

  A "Standard Interface" means an interface that either is an official
standard defined by a recognized standards body, or, in the case of
interfaces specified for a particular programming language, one that
is widely used among developers working in that language.

  The "System Libraries" of an executable work include anything, other
than the work as a whole, that (a) is included in the normal form of
packaging a Major Component, but which is not part of that Major
Component, and (b) serves only to enable use of the work with that
Major Component, or to implement a Standard Interface for which an
implementation is available to the public in source code form.  A
"Major Component", in this context, means a major essential component
(kernel, window system, and so on) of the specific operating system
(if any) on which the executable work runs, or a compiler used to
produce the work, or an object code interpreter used to run it.

  The "Corresponding Source" for a work in object code form means all
the source code needed to generate, install, and (for an executable
work) run the object code and to modify the work, including scripts to
control those activities.  However, it does not include the work's
System Libraries, or general-purpose tools or generally available free
programs which are used unmodified in performing those activities but
which are not part of the work.  For example, Corresponding Source
includes interface definition files associated with source files for
the work, and the source code for shared libraries and dynamically
linked subprograms that the work is specifically designed to require,
such as by intimate data communication or control flow between those
subprograms and other parts of the work.

  The Corresponding Source need not include anything that users
can regenerate automatically from other parts of the Corresponding
Source.

  The Corresponding Source for a work in source code form is that
same work.

  2. Basic Permissions.

  All rights granted under this License are granted for the term of
copyright on the Program, and are irrevocable provided the stated
conditions are met.  This License explicitly affirms your unlimited
permission to run the unmodified Program.  The output from running a
covered work is covered by this License only if the output, given its
content, constitutes a covered work.  This License acknowledges your
rights of fair use or other equivalent, as provided by copyright law.

  You may make, run and propagate covered works that you do not
convey, without conditions so long as your license otherwise remains
in force.  You may convey covered works to others for the sole purpose
of having them make modifications exclusively for you, or provide you
with facilities for running those works, provided that you comply with
the terms of this License in conveying all material for which you do
not control copyright.  Those thus making or running the covered works
for you must do so exclusively on your behalf, under your direction
and control, on terms that prohibit them from making any copies of
your copyrighted material outside their relationship with you.

  Conveying under any other circumstances is permitted solely under
the conditions stated below.  Sublicensing is not allowed; section 10
makes it unnecessary.

  3. Protecting Users' Legal Rights From Anti-Circumvention Law.

  No covered work shall be deemed part of an effective technological
measure under any applicable law fulfilling obligations under article
11 of the WIPO copyright treaty adopted on 20 December 1996, or
similar laws prohibiting or restricting circumvention of such
measures.

  When you convey a covered work, you waive any legal power to forbid
circumvention of technological measures to the extent such circumvention
is effected by exercising rights under this License with respect to
the covered work, and you disclaim any intention to limit operation or
modification of the work as a means of enforcing, against the work's
users, your or third parties' legal rights to forbid circumvention of
technological measures.

  4. Conveying Verbatim Copies.

  You may convey verbatim copies of the Program's source code as you
receive it, in any medium, provided that you conspicuously and
appropriately publish on each copy an appropriate copyright notice;
keep intact all notices stating that this License and any
non-permissive terms added in accord with section 7 apply to the code;
keep intact all notices of the absence of any warranty; and give all
recipients a copy of this License along with the Program.

  You may charge any price or no price for each copy that you convey,
and you may offer support or warranty protection for a fee.

  5. Conveying Modified Source Versions.

  You may convey a work based on the Program, or the modifications to
produce it from the Program, in the form of source code under the
terms of section 4, provided that you also meet all of these conditions:

    a) The work must carry prominent notices stating that you modified
    it, and giving a relevant date.

    b) The work must carry prominent notices stating that it is
    released under this License and any conditions added under section
    7.  This requirement modifies the requirement in section 4 to
    "keep intact all notices".

    c) You must license the entire work, as a whole, under this
    License to anyone who comes into possession of a copy.  This
    License will therefore apply, along with any applicable section 7
    additional terms, to the whole of the work, and all its parts,
    regardless of how they are packaged.  This License gives no
    permission to license the work in any other way, but it does not
    invalidate such permission if you have separately received it.

    d) If the work has interactive user interfaces, each must display
    Appropriate Legal Notices; however, if the Program has interactive
    interfaces that do not display Appropriate Legal Notices, your
    work need not make them do so.

  A compilation of a covered work with other separate and independent
works, which are not by their nature extensions of the covered work,
and which are not combined with it such as to form a larger program,
in or on a volume of a storage or distribution medium, is called an
"aggregate" if the compilation and its resulting copyright are not
used to limit the access or legal rights of the compilation's users
beyond what the individual works permit.  Inclusion of a covered work
in an aggregate does not cause this License to apply to the other
parts of the aggregate.

  6. Conveying Non-Source Forms.

  You may convey a covered work in object code form under the terms
of sections 4 and 5, provided that you also convey the
machine-readable Corresponding Source under the terms of this License,
in one of these ways:

    a) Convey the object code in, or embodied in, a physical product
    (including a physical distribution medium), accompanied by the
    Corresponding Source fixed on a durable physical medium
    customarily used for software interchange.

    b) Convey the object code in, or embodied in, a physical product
    (including a physical distribution medium), accompanied by a
    written offer, valid for at least three years and valid for as
    long as you offer spare parts or customer support for that product
    model, to give anyone who possesses the object code either (1) a
    copy of the Corresponding Source for all the software in the
    product that is covered by this License, on a durable physical
    medium customarily used for software interchange, for a price no
    more than your reasonable cost of physically performing this
    conveying of source, or (2) access to copy the
    Corresponding Source from a network server at no charge.

    c) Convey individual copies of the object code with a copy of the
    written offer to provide the Corresponding Source.  This
    alternative is allowed only occasionally and noncommercially, and
    only if you received the object code with such an offer, in accord
    with subsection 6b.

    d) Convey the object code by offering access from a designated
    place (gratis or for a charge), and offer equivalent access to the
    Corresponding Source in the same way through the same place at no
    further charge.  You need not require recipients to copy the
    Corresponding Source along with the object code.  If the place to
    copy the object code is a network server, the Corresponding Source
    may be on a different server (operated by you or a third party)
    that supports equivalent copying facilities, provided you maintain
    clear directions next to the object code saying where to find the
    Corresponding Source.  Regardless of what server hosts the
    Corresponding Source, you remain obligated to ensure that it is
    available for as long as needed to satisfy these requirements.

    e) Convey the object code using peer-to-peer transmission, provided
    you inform other peers where the object code and Corresponding
    Source of the work are being offered to the general public at no
    charge under subsection 6d.

  A separable portion of the object code, whose source code is excluded
from the Corresponding Source as a System Library, need not be
included in conveying the object code work.

  A "User Product" is either (1) a "consumer product", which means any
tangible personal property which is normally used for personal, family,
or household purposes, or (2) anything designed or sold for incorporation
into a dwelling.  In determining whether a product is a consumer product,
doubtful cases shall be resolved in favor of coverage.  For a particular
product received by a particular user, "normally used" refers to a
typical or common use of that class of product, regardless of the status
of the particular user or of the way in which the particular user
actually uses, or expects or is expected to use, the product.  A product
is a consumer product regardless of whether the product has substantial
commercial, industrial or non-consumer uses, unless such uses represent
the only significant mode of use of the product.

  "Installation Information" for a User Product means any methods,
procedures, authorization keys, or other information required to install
and execute modified versions of a covered work in that User Product from
a modified version of its Corresponding Source.  The information must
suffice to ensure that the continued functioning of the modified object
code is in no case prevented or interfered with solely because
modification has been made.

  If you convey an object code work under this section in, or with, or
specifically for use in, a User Product, and the conveying occurs as
part of a transaction in which the right of possession and use of the
User Product is transferred to the recipient in perpetuity or for a
fixed term (regardless of how the transaction is characterized), the
Corresponding Source conveyed under this section must be accompanied
by the Installation Information.  But this requirement does not apply
if neither you nor any third party retains the ability to install
modified object code on the User Product (for example, the work has
been installed in ROM).

  The requirement to provide Installation Information does not include a
requirement to continue to provide support service, warranty, or updates
for a work that has been modified or installed by the recipient, or for
the User Product in which it has been modified or installed.  Access to a
network may be denied when the modification itself materially and
adversely affects the operation of the network or violates the rules and
protocols for communication across the network.

  Corresponding Source conveyed, and Installation Information provided,
in accord with this section must be in a format that is publicly
documented (and with an implementation available to the public in
source code form), and must require no special password or key for
unpacking, reading or copying.

  7. Additional Terms.

  "Additional permissions" are terms that supplement the terms of this
License by making exceptions from one or more of its conditions.
Additional permissions that are applicable to the entire Program shall
be treated as though they were included in this License, to the extent
that they are valid under applicable law.  If additional permissions
apply only to part of the Program, that part may be used separately
under those permissions, but the entire Program remains governed by
this License without regard to the additional permissions.

  When you convey a copy of a covered work, you may at your option
remove any additional permissions from that copy, or from any part of
it.  (Additional permissions may be written to require their own
removal in certain cases when you modify the work.)  You may place
additional permissions on material, added by you to a covered work,
for which you have or can give appropriate copyright permission.

  Notwithstanding any other provision of this License, for material you
add to a covered work, you may (if authorized by the copyright holders of
that material) supplement the terms of this License with terms:

    a) Disclaiming warranty or limiting liability differently from the
    terms of sections 15 and 16 of this License; or

    b) Requiring preservation of specified reasonable legal notices or
    author attributions in that material or in the Appropriate Legal
    Notices displayed by works containing it; or

    c) Prohibiting misrepresentation of the origin of that material, or
    requiring that modified versions of such material be marked in
    reasonable ways as different from the original version; or

    d) Limiting the use for publicity purposes of names of licensors or
    authors of the material; or

    e) Declining to grant rights under trademark law for use of some
    trade names, trademarks, or service marks; or

    f) Requiring indemnification of licensors and authors of that
    material by anyone who conveys the material (or modified versions of
    it) with contractual assumptions of liability to the recipient, for
    any liability that these contractual assumptions directly impose on
    those licensors and authors.

  All other non-permissive additional terms are considered "further
restrictions" within the meaning of section 10.  If the Program as you
received it, or any part of it, contains a notice stating that it is
governed by this License along with a term that is a further
restriction, you may remove that term.  If a license document contains
a further restriction but permits relicensing or conveying under this
License, you may add to a covered work material governed by the terms
of that license document, provided that the further restriction does
not survive such relicensing or conveying.

  If you add terms to a covered work in accord with this section, you
must place, in the relevant source files, a statement of the
additional terms that apply to those files, or a notice indicating
where to find the applicable terms.

  Additional terms, permissive or non-permissive, may be stated in the
form of a separately written license, or stated as exceptions;
the above requirements apply either way.

  8. Termination.

  You may not propagate or modify a covered work except as expressly
provided under this License.  Any attempt otherwise to propagate or
modify it is void, and will automatically terminate your rights under
this License (including any patent licenses granted under the third
paragraph of section 11).

  However, if you cease all violation of this License, then your
license from a particular copyright holder is reinstated (a)
provisionally, unless and until the copyright holder explicitly and
finally terminates your license, and (b) permanently, if the copyright
holder fails to notify you of the violation by some reasonable means
prior to 60 days after the cessation.

  Moreover, your license from a particular copyright holder is
reinstated permanently if the copyright holder notifies you of the
violation by some reasonable means, this is the first time you have
received notice of violation of this License (for any work) from that
copyright holder, and you cure the violation prior to 30 days after
your receipt of the notice.

  Termination of your rights under this section does not terminate the
licenses of parties who have received copies or rights from you under
this License.  If your rights have been terminated and not permanently
reinstated, you do not qualify to receive new licenses for the same
material under section 10.

  9. Acceptance Not Required for Having Copies.

  You are not required to accept this License in order to receive or
run a copy of the Program.  Ancillary propagation of a covered work
occurring solely as a consequence of using peer-to-peer transmission
to receive a copy likewise does not require acceptance.  However,
nothing other than this License grants you permission to propagate or
modify any covered work.  These actions infringe copyright if you do
not accept this License.  Therefore, by modifying or propagating a
covered work, you indicate your acceptance of this License to do so.

  10. Automatic Licensing of Downstream Recipients.

  Each time you convey a covered work, the recipient automatically
receives a license from the original licensors, to run, modify and
propagate that work, subject to this License.  You are not responsible
for enforcing compliance by third parties with this License.

  An "entity transaction" is a transaction transferring control of an
organization, or substantially all assets of one, or subdividing an
organization, or merging organizations.  If propagation of a covered
work results from an entity transaction, each party to that
transaction who receives a copy of the work also receives whatever
licenses to the work the party's predecessor in interest had or could
give under the previous paragraph, plus a right to possession of the
Corresponding Source of the work from the predecessor in interest, if
the predecessor has it or can get it with reasonable efforts.

  You may not impose any further restrictions on the exercise of the
rights granted or affirmed under this License.  For example, you may
not impose a license fee, royalty, or other charge for exercise of
rights granted under this License, and you may not initiate litigation
(including a cross-claim or counterclaim in a lawsuit) alleging that
any patent claim is infringed by making, using, selling, offering for
sale, or importing the Program or any portion of it.

  11. Patents.

  A "contributor" is a copyright holder who authorizes use under this
License of the Program or a work on which the Program is based.  The
work thus licensed is called the contributor's "contributor version".

  A contributor's "essential patent claims" are all patent claims
owned or controlled by the contributor, whether already acquired or
hereafter acquired, that would be infringed by some manner, permitted
by this License, of making, using, or selling its contributor version,
but do not include claims that would be infringed only as a
consequence of further modification of the contributor version.  For
purposes of this definition, "control" includes the right to grant
patent sublicenses in a manner consistent with the requirements of
this License.

  Each contributor grants you a non-exclusive, worldwide, royalty-free
patent license under the contributor's essential patent claims, to
make, use, sell, offer for sale, import and otherwise run, modify and
propagate the contents of its contributor version.

  In the following three paragraphs, a "patent license" is any express
agreement or commitment, however denominated, not to enforce a patent
(such as an express permission to practice a patent or covenant not to
sue for patent infringement).  To "grant" such a patent license to a
party means to make such an agreement or commitment not to enforce a
patent against the party.

  If you convey a covered work, knowingly relying on a patent license,
and the Corresponding Source of the work is not available for anyone
to copy, free of charge and under the terms of this License, through a
publicly available network server or other readily accessible means,
then you must either (1) cause the Corresponding Source to be so
available, or (2) arrange to deprive yourself of the benefit of the
patent license for this particular work, or (3) arrange, in a manner
consistent with the requirements of this License, to extend the patent
license to downstream recipients.  "Knowingly relying" means you have
actual knowledge that, but for the patent license, your conveying the
covered work in a country, or your recipient's use of the covered work
in a country, would infringe one or more identifiable patents in that
country that you have reason to believe are valid.

  If, pursuant to or in connection with a single transaction or
arrangement, you convey, or propagate by procuring conveyance of, a
covered work, and grant a patent license to some of the parties
receiving the covered work authorizing them to use, propagate, modify
or convey a specific copy of the covered work, then the patent license
you grant is automatically extended to all recipients of the covered
work and works based on it.

  A patent license is "discriminatory" if it does not include within
the scope of its coverage, prohibits the exercise of, or is
conditioned on the non-exercise of one or more of the rights that are
specifically granted under this License.  You may not convey a covered
work if you are a party to an arrangement with a third party that is
in the business of distributing software, under which you make payment
to the third party based on the extent of your activity of conveying
the work, and under which the third party grants, to any of the
parties who would receive the covered work from you, a discriminatory
patent license (a) in connection with copies of the covered work
conveyed by you (or copies made from those copies), or (b) primarily
for and in connection with specific products or compilations that
contain the covered work, unless you entered into that arrangement,
or that patent license was granted, prior to 28 March 2007.

  Nothing in this License shall be construed as excluding or limiting
any implied license or other defenses to infringement that may
otherwise be available to you under applicable patent law.

  12. No Surrender of Others' Freedom.

  If conditions are imposed on you (whether by court order, agreement or
otherwise) that contradict the conditions of this License, they do not
excuse you from the conditions of this License.  If you cannot convey a
covered work so as to satisfy simultaneously your obligations under this
License and any other pertinent obligations, then as a consequence you may
not convey it at all.  For example, if you agree to terms that obligate you
to collect a royalty for further conveying from those to whom you convey
the Program, the only way you could satisfy both those terms and this
License would be to refrain entirely from conveying the Program.

  13. Use with the GNU Affero General Public License.

  Notwithstanding any other provision of this License, you have
permission to link or combine any covered work with a work licensed
under version 3 of the GNU Affero General Public License into a single
combined work, and to convey the resulting work.  The terms of this
License will continue to apply to the part which is the covered work,
but the special requirements of the GNU Affero General Public License,
section 13, concerning interaction through a network will apply to the
combination as such.

  14. Revised Versions of this License.

  The Free Software Foundation may publish revised and/or new versions of
the GNU General Public License from time to time.  Such new versions will
be similar in spirit to the present version, but may differ in detail to
address new problems or concerns.

  Each version is given a distinguishing version number.  If the
Program specifies that a certain numbered version of the GNU General
Public License "or any later version" applies to it, you have the
option of following the terms and conditions either of that numbered
version or of any later version published by the Free Software
Foundation.  If the Program does not specify a version number of the
GNU General Public License, you may choose any version ever published
by the Free Software Foundation.

  If the Program specifies that a proxy can decide which future
versions of the GNU General Public License can be used, that proxy's
public statement of acceptance of a version permanently authorizes you
to choose that version for the Program.

  Later license versions may give you additional or different
permissions.  However, no additional obligations are imposed on any
author or copyright holder as a result of your choosing to follow a
later version.

  15. Disclaimer of Warranty.

  THERE IS NO WARRANTY FOR THE PROGRAM, TO THE EXTENT PERMITTED BY
APPLICABLE LAW.  EXCEPT WHEN OTHERWISE STATED IN WRITING THE COPYRIGHT
HOLDERS AND/OR OTHER PARTIES PROVIDE THE PROGRAM "AS IS" WITHOUT WARRANTY
OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO,
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE.  THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE PROGRAM
IS WITH YOU.  SHOULD THE PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF
ALL NECESSARY SERVICING, REPAIR OR CORRECTION.

  16. Limitation of Liability.

  IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING
WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MODIFIES AND/OR CONVEYS
THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY
GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE
USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED TO LOSS OF
DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD
PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER PROGRAMS),
EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF
SUCH DAMAGES.

  17. Interpretation of Sections 15 and 16.

  If the disclaimer of warranty and limitation of liability provided
above cannot be given local legal effect according to their terms,
reviewing courts shall apply local law that most closely approximates
an absolute waiver of all civil liability in connection with the
Program, unless a warranty or assumption of liability accompanies a
copy of the Program in return for a fee.

                     END OF TERMS AND CONDITIONS

            How to Apply These Terms to Your New Programs

  If you develop a new program, and you want it to be of the greatest
possible use to the public, the best way to achieve this is to make it
free software which everyone can redistribute and change under these terms.

  To do so, attach the following notices to the program.  It is safest
to attach them to the start of each source file to most effectively
state the exclusion of warranty; and each file should have at least
the "copyright" line and a pointer to where the full notice is found.

    <one line to give the program's name and a brief idea of what it does.>
    Copyright (C) <year>  <name of author>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

Also add information on how to contact you by electronic and paper mail.

  If the program does terminal interaction, make it output a short
notice like this when it starts in an interactive mode:

    <program>  Copyright (C) <year>  <name of author>
    This program comes with ABSOLUTELY NO WARRANTY; for details type `show w'.
    This is free software, and you are welcome to redistribute it
    under certain conditions; type `show c' for details.

The hypothetical commands `show w' and `show c' should show the appropriate
parts of the General Public License.  Of course, your program's commands
might be different; for a GUI interface, you would use an "about box".

  You should also get your employer (if you work as a programmer) or school,
if any, to sign a "copyright disclaimer" for the program, if necessary.
For more information on this, and how to apply and follow the GNU GPL, see
<http://www.gnu.org/licenses/>.

  The GNU General Public License does not permit incorporating your program
into proprietary programs.  If your program is a subroutine library, you
may consider it more useful to permit linking proprietary applications with
the library.  If this is what you want to do, use the GNU Lesser General
Public License instead of this License.  But first, please read
<http://www.gnu.org/philosophy/why-not-lgpl.html>."""

    # Control help
    inspect_master = kwargs['inspect_master']
    kwargs['Button_help'].value = help_dynamic(inspect_master, kwargs['button_1'])
    kwargs['CheckBox_help'].value = help_dynamic(inspect_master, kwargs['check_box_1'])
    kwargs['ChoiceBox_help'].value = help_dynamic(inspect_master, kwargs['choice_box_1'])
    kwargs['ChoiceButton_help'].value = help_dynamic(inspect_master, kwargs['choice_button_1'])
    kwargs['EventButton_help'].value = help_dynamic(inspect_master, kwargs['event_button_1'])
    kwargs['FileDialog_help'].value = help_dynamic(inspect_master, kwargs['file_dialog_1'])
    kwargs['FilePicker_help'].value = help_dynamic(inspect_master, kwargs['file_picker_1'])
    kwargs['GlobalNamespace_help'].value = help_static(pythics.controls.GlobalNamespace, None)
    kwargs['GlobalAction_help'].value = help_static(pythics.controls.GlobalAction, None)
    kwargs['GlobalTrigger_help'].value = help_dynamic(inspect_master, kwargs['global_trigger'])
    kwargs['Image_help'].value = help_dynamic(inspect_master, kwargs['image_1'])
    kwargs['ImageButton_help'].value = help_dynamic(inspect_master, kwargs['image_button_2'])
    kwargs['InputDialog_help'].value = help_dynamic(inspect_master, kwargs['input_dialog_1'])
    kwargs['Knob_help'].value = help_dynamic(inspect_master, kwargs['knob_1'])
    kwargs['MessageDialog_help'].value = help_dynamic(inspect_master, kwargs['message_dialog_1'])
    kwargs['Meter_help'].value = help_dynamic(inspect_master, kwargs['meter_1'])
    kwargs['NumBox_help'].value = help_dynamic(inspect_master, kwargs['num_box_1'])
    kwargs['RadioButtonBox_help'].value = help_dynamic(inspect_master, kwargs['radio_button_box_1'])
    kwargs['RunButton_help'].value = help_static(pythics.controls.RunButton, pythics.proxies.RunButtonProxy)
    kwargs['ScrollBar_help'].value = help_dynamic(inspect_master, kwargs['scroll_bar_1'])
    kwargs['Shell_help'].value = help_dynamic(inspect_master, kwargs['shell_1'])
    kwargs['SubWindow_help'].value = help_static(pythics.controls.SubWindow, None)
    kwargs['TextBox_help'].value = help_dynamic(inspect_master, kwargs['text_box_1'])
    kwargs['TextIOBox_help'].value = help_dynamic(inspect_master, kwargs['text_io_box_1'])
    kwargs['Timer_help'].value = help_static(pythics.controls.Timer, pythics.proxies.TimerProxy)
    kwargs['ScriptLoader_help'].value = help_static(pythics.controls.ScriptLoader, None)
    kwargs['ParameterLoader_help'].value = help_static(pythics.controls.ParameterLoader, None)
    if 'mpl_canvas_1' in kwargs:
        kwargs['mplCanvas_help'].value = help_dynamic(inspect_master, kwargs['mpl_canvas_1'])
    if 'mpl_plot_2d_1' in kwargs:
        kwargs['mplPlot2D_help'].value = help_dynamic(inspect_master, kwargs['mpl_plot_2d_1'])
    if 'mpl_chart_2d_1' in kwargs:
        kwargs['mplChart2D_help'].value = help_dynamic(inspect_master, kwargs['mpl_chart_2d_1'])
    if 'qwt_chart_1' in kwargs:
        kwargs['qwtChart_help'].value = help_dynamic(inspect_master, kwargs['qwt_chart_1'])
    if 'qwt_gauge_1' in kwargs:
        kwargs['qwtGauge_help'].value = help_dynamic(inspect_master, kwargs['qwt_gauge_1'])
    if 'qwt_knob_1' in kwargs:
        kwargs['qwtKnob_help'].value = help_dynamic(inspect_master, kwargs['qwt_knob_1'])
    if 'qwt_plot_1' in kwargs:
        kwargs['qwtPlot_help'].value = help_dynamic(inspect_master, kwargs['qwt_plot_1'])
    if 'qwt_point_plot_1' in kwargs:
        kwargs['qwtPointLinePlot_help'].value = help_dynamic(inspect_master, kwargs['qwt_point_plot_1'])
    if 'qwt_slider_1' in kwargs:
        kwargs['qwtSlider_help'].value = help_dynamic(inspect_master, kwargs['qwt_slider_1'])


def Terminate(globals, **kwargs):
    logger = multiprocessing.get_logger()
    logger.info('Terminated demo.py')


#
# Button
#
def test_button_1(button_1, **kwargs):
    button_1.label = button_1.label[::-1]

def test_button_2A(button_2, **kwargs):
    button_2.actions = {'clicked': 'help.test_button_2B'}
    button_2.label = 'execute Test B'

def test_button_2B(button_2, **kwargs):
    button_2.actions = {'clicked': 'help.test_button_2A'}
    button_2.label = 'execute Test A'

def test_toggle_button(toggle_button_1, toggle_button_result, **kwargs):
    toggle_button_result.value = toggle_button_1.value


#
# CheckBox
#
def test_check_box_1(check_box_1, check_box_2, **kwargs):
    check_box_2.enabled = check_box_1.value

def test_check_box_2(check_box_2, check_box_result, **kwargs):
    check_box_result.value = str(check_box_2.value)


#
# ChoiceBox
#
def test_choice_box_1(choice_box_1, choice_box_result_1, **kwargs):
    choice_box_result_1.value = choice_box_1.value

def test_choice_box_2(choice_box_2, choice_box_result_2, **kwargs):
    choice_box_result_2.value = choice_box_2.value

def test_choice_box_3(choice_box_3, choice_box_result_3, **kwargs):
    choice_box_result_3.value = choice_box_3.value


#
# ChoiceButton
#
def test_choice_button(choice_button_1, choice_button_result, **kwargs):
    choice_button_result.value = choice_button_1.value


#
# ColorPicker
#
def test_color_picker(color_picker_1, color_picker_result, **kwargs):
    color_picker_result.value = str(color_picker_1.value)


#
# DatePicker
#
def test_date_picker(date_picker_1, date_picker_result, **kwargs):
    date_picker_result.value = str(date_picker_1.value)


#
# Dial
#
def test_dial_1(dial_1, **kwargs):
    dial_1.value = random.randrange(0,11)


#
# FileDialog
#
def test_file_dialog_1(file_dialog_1, file_dialog_result, **kwargs):
    file_dialog_result.value = file_dialog_1.get_open()

def test_file_dialog_2(file_dialog_1, file_dialog_result, **kwargs):
    file_dialog_result.value = file_dialog_1.get_save()


#
# FileBrowseButton
#
def test_file_picker(file_picker_1, file_picker_result, **kwargs):
    file_picker_result.value = file_picker_1.value


#
# Gauge
#
def test_qwt_gauge_1(qwt_gauge_1, **kwargs):
    qwt_gauge_1.pulse()

def test_qwt_gauge_2(qwt_gauge_2, **kwargs):
    qwt_gauge_2.value = random.randrange(0,11)


#
# GlobalNamespace
#
def test_global_retrieve(globals, global_namespace_result, **kwargs):
    global_namespace_result.value = globals.test

def test_global_store(globals, global_namespace_result, **kwargs):
    globals.test = global_namespace_result.value
    global_namespace_result.value = ''


#
# GlobalTrigger and GlobalAction
#
def test_global_trigger(global_trigger, **kwargs):
    global_trigger.trigger()

def test_global_action(global_action_result, **kwargs):
    global_action_result.value = 'Triggered!'


#
# Image
#
def test_image_left_down(image_1, image_left_down_result, **kwargs):
    image_left_down_result.value = str(image_1.left_press_position)

def test_image_left_up(image_1, image_left_up_result, **kwargs):
    image_left_up_result.value = str(image_1.left_release_position)

def test_image_right_down(image_1, image_right_down_result, **kwargs):
    image_right_down_result.value = str(image_1.right_press_position)

def test_image_right_up(image_1, image_right_up_result, **kwargs):
    image_right_up_result.value = str(image_1.right_release_position)

def test_image(image_1, image_2, image_image_filename, **kwargs):
    filename = image_image_filename.value
    im = PIL.Image.open(filename)
    image_1.image = im
    image_2.image = im

def image_get_loop(image_1, **kwargs):
    for i in range(10):
        temp = image_1.image
        image_1.image = temp

def test_image_with_shared(image_3, image_with_shared_image_filename, **kwargs):
    filename = image_with_shared_image_filename.value
    im = PIL.Image.open(filename)
    #image_3.setup_shared_memory(im.size[0], im.size[1])
    image_3.image = im

def image_with_shared_get_loop(image_3, **kwargs):
    for i in range(10):
        temp = image_3.image
        image_3.image = temp


#
# ImageButton
#
def test_image_button_1(image_button_result_1, **kwargs):
    image_button_result_1.value = 'clicked'

def test_image_button_2(image_button_2, image_button_result_2, **kwargs):
    image_button_result_2.value = image_button_2.value


#
# InputDialog
#

def test_input_dialog_1_1(input_dialog_1, input_dialog_result_1, **kwargs):
    input_dialog_1.input_type = int
    input_dialog_1.int_default_value = 4
    input_dialog_1.int_min = 0
    input_dialog_1.int_max = 100
    input_dialog_1.int_step = 2
    input_dialog_result_1.value = input_dialog_1.open()

def test_input_dialog_1_2(input_dialog_1, input_dialog_result_1, **kwargs):
    input_dialog_1.input_type = float
    input_dialog_1.float_default_value = -5.0
    input_dialog_1.float_min = -10.0
    input_dialog_1.float_max = 1000.0
    input_dialog_1.float_decimals = 2
    input_dialog_result_1.value = input_dialog_1.open()

def test_input_dialog_1_3(input_dialog_1, input_dialog_result_1, **kwargs):
    input_dialog_1.input_type = list
    input_dialog_1.list_items = ['item 1', 'item 2', 'item 3', 'item 4']
    input_dialog_1.list_default_item = 1
    input_dialog_1.list_editable = True
    input_dialog_result_1.value = input_dialog_1.open()

def test_input_dialog_1_4(input_dialog_1, input_dialog_result_1, **kwargs):
    input_dialog_1.input_type = str
    input_dialog_1.str_default_value = 'default text'
    input_dialog_result_1.value = input_dialog_1.open()


#
# Knob
#
def test_knob(knob_1, knob_result, knob_meter, **kwargs):
    knob_result.value = knob_1.value
    knob_meter.value = knob_1.value


#
# ListBox
#
def test_list_box_1(list_box_1, **kwargs):
    list_box_1.value = list([['first_1', 'second_1', 'third_1'],
                             ['first_2', 'second_2', 'third_2'],
                             ['first_3', 'second_3', 'third_3'],
                             ['first_4', 'second_4', 'third_4'],
                             ['first_5', 'second_5', 'third_5']])

def test_select_list_box_1(list_box_1, list_box_select_result_1, **kwargs):
    list_box_select_result_1.value = str(list_box_1.selection)

def test_edit_list_box_1(list_box_1, list_box_edit_result_1, **kwargs):
    list_box_edit_result_1.value = str(list_box_1.value)


#
# MessageDialog
#
def test_message_dialog_1(message_dialog_1, message_dialog_result_1, **kwargs):
    #message_dialog_1.message = message_dialog_1.message + '1'
    message_dialog_result_1.value = message_dialog_1.open()

#
# Meter
#
def test_meter_1(meter_1, **kwargs):
    meter_1.value = np.random.random()*200.0
    

#
# NumBox
#
def test_num_box_1(num_box_1, num_box_result_1, **kwargs):
    num_box_result_1.value = num_box_1.value

def test_num_box_2(num_box_2, num_box_result_2, **kwargs):
    num_box_result_2.value = num_box_2.value

def test_num_box_3(num_box_3, num_box_result_3, **kwargs):
    num_box_result_3.value = num_box_3.value


#
# NumGrid
#
def test_num_grid_1(num_grid_1, **kwargs):
    a = npr.rand(20, 10)
    num_grid_1.value = a


#
# RadioButtonBox
#
def test_radio_button_box(radio_button_box_1, radio_button_box_result, **kwargs):
    radio_button_box_result.value = radio_button_box_1.value


#
# RunButton
#
def test_run_button(run_button_1, run_button_result, **kwargs):
    t0 = time.time()
    run_button_result.value = 0
    while run_button_1.value:
        t = time.time() - t0
        run_button_result.value = t
        # repeat with 0.1 second interval
        yield 0.1
    run_button_result.value = -1.0


#
# ScrollBar
#
def test_scroll_bar_button(scroll_bar_1, **kwargs):
    scroll_bar_1.ranges = (10, 100)
    scroll_bar_1.value = 30

def test_scroll_bar(scroll_bar_1, scroll_bar_result, **kwargs):
    ranges = scroll_bar_1.ranges
    scroll_bar_result.value = '%d %d %d' % (scroll_bar_1.value,
                                          ranges[0], ranges[1])


#
# Shell
#
def initialize_shell_1(shell_1, **kwargs):
    local_dict = kwargs.copy()
    #local_dict.update(globals())
    #local_dict.update(locals())
    shell_1.interact(local_dict, 'Pythics Demo!')


#
# Slider
#
def test_qwt_slider_1(qwt_slider_1, slider_result, **kwargs):
    slider_result.value = qwt_slider_1.value

def test_slider_2(slider_2, slider_result, **kwargs):
    slider_result.value = slider_2.value


#
# EventButton
#
def test_event_button_1(event_button_1, event_button_result, **kwargs):
    event_button_1.clear()
    while True:
        event_button_result.value = time.time()
        time.sleep(0.5)
        if event_button_1.wait_interval(5.0): break
    event_button_result.value = 'Stopped.'

#
# SubWindow
#
def test_sub_window(sub_window_1, sub_window_result, **kwargs):
    sub_window_result.value = sub_window_1['choice_box_1'].value
    sub_window_1['num_box_1'].value = random.randint(0, 1000000)


#
# TextBox
#
def test_text_box(text_box_1, text_box_result, **kwargs):
    text_box_result.value = text_box_1.value


#
# TextIOBox
#
def setup_text_io_box(text_io_box_1, **kwargs):
    private.logger = logging.getLogger('demo')
    private.logger.setLevel(logging.DEBUG)
    sh = logging.StreamHandler(text_io_box_1)
    sh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    sh.setFormatter(formatter)
    private.logger.addHandler(sh)
    text_io_box_1.write('SETUP COMPLETE.\n')
    text_io_box_1.flush()

def test_text_io_box(**kwargs):
    private.logger.debug('This is a debug message')
    private.logger.info('This is an info message')
    private.logger.warning('This is a warning message')
    private.logger.error('This is an error message')
    private.logger.critical('This is a critical error message')


#
# TimeBox
#
def test_time_box(time_box_1, time_box_result, **kwargs):
    time_box_result.value = str(time_box_1.value)


#
# Timer
#
def start_timer(timer_1, timer_result, **kwargs):
    global timer_t0
    timer_t0 = time.time()
    timer_result.value = 0
    timer_1.start(0.1, require_retrigger=True)

def test_timer(timer_1, timer_result, **kwargs):
    global timer_t0
    t = time.time() - timer_t0
    timer_result.value = t
    timer_1.retrigger()

def stop_timer(timer_1, timer_result, **kwargs):
    global timer_t0
    timer_1.stop()
    timer_result.value = -1.0


#
# qWidget
#
def test_qwidgets(qwidget_1, qwidget_2, **kwargs):
    #qwidget_1.display(qwidget_1.intValue() + 1)
    qwidget_1.setDigitCount(8)
    qwidget_2.clicked.connect(test_calendar)

def test_calendar(qwidget_1, qwidget_2, **kwargs):
    day = qwidget_2.selectedDate().toJulianDay()
    qwidget_1.display(day)


#
# mpl.Canvas
#
def test_mpl_canvas_1(mpl_canvas_1, mpl_canvas_choices, matplotlib, **kwargs):
    choice = mpl_canvas_choices.value
    if choice == 'simple plot':
        mpl_canvas_1.figure.clear()
        axes = mpl_canvas_1.figure.add_subplot(111)
        t = np.arange(0.0, 2.0, 0.01)
        s = np.sin(2*pi*t)
        axes.plot(t, s, linewidth=1.0)
        axes.set_xlabel('time (s)')
        axes.set_ylabel('voltage (mV)')
        axes.set_title('Simple Plot')
        axes.grid(True)
        mpl_canvas_1.canvas.draw()
    elif choice == 'polar plot':
        mpl_canvas_1.figure.clear()
        N = 150
        r = 2*npr.rand(N)
        theta = 2*pi*npr.rand(N)
        area = 200*r**2*npr.rand(N)
        colors = theta
        axes = mpl_canvas_1.figure.add_subplot(111, projection='polar')
        axes.scatter(theta, r, c=colors, s=area)
        mpl_canvas_1.canvas.draw()
    elif choice == 'bar chart':
        mpl_canvas_1.figure.clear()
        N = 5
        xs = np.arange(N)
        y1s = npr.rand(len(xs))
        y2s = npr.rand(len(xs))
        width=0.35
        axes = mpl_canvas_1.figure.add_subplot(111)
        axes.bar(xs, y1s, width, color='r')
        axes.bar(xs+width, y2s, width, color='y')
        axes.set_xticks(xs+width)
        axes.set_xticklabels(('A', 'B', 'C', 'D', 'E'))
        axes.set_xlabel('Group')
        axes.set_ylabel('Scores')
        axes.set_title('Simple Bar Chart')
        mpl_canvas_1.canvas.draw()
    elif choice == 'image plot':
        mpl_canvas_1.figure.clear()
        zs = 100*np.random.rand(100, 150)
        axes = mpl_canvas_1.figure.add_subplot(111)
        image = axes.imshow(zs, interpolation='nearest', animated=True)
        axes.set_xlabel('X')
        axes.set_ylabel('Y')
        axes.set_title('Image Plot')
        mpl_canvas_1.figure.colorbar(image)
        mpl_canvas_1.canvas.draw()
    elif choice == 'pcolor':
        mpl_canvas_1.figure.clear()
        r_steps = 20
        theta_steps = 80
        axes = mpl_canvas_1.figure.add_subplot(111, projection='polar')
        theta_grid, step = np.linspace(0, 2*np.pi, theta_steps+1, endpoint=True, retstep=True)
        theta_grid -= step/2.0
        r_grid = np.linspace(0, 1.0, r_steps+1, endpoint=True)
        X, Y = np.meshgrid(theta_grid, r_grid) #rectangular plot of polar data
        zs = np.zeros((r_steps, theta_steps))
        thetas = np.linspace(0, 2*np.pi, theta_steps, endpoint=False)
        rs, step = np.linspace(0, 1.0, r_steps, endpoint=False, retstep=True)
        rs += step/2.0
        for ri in range(r_steps):
            for ti in range(theta_steps):
                zs[ri, ti] = np.sin(2*np.pi*rs[ri])*np.cos(4*thetas[ti])
        #axes.pcolormesh(X, Y, zs)
        #axes.pcolor(X, Y, zs)
        #axes.pcolorfast(X, Y, zs)
        axes.pcolor(X, Y, zs)
        axes.set_title('Polar Image Plot')
        mpl_canvas_1.canvas.draw()
    elif choice == 'surface3d':
        mpl_canvas_1.figure.clear()
        axes = mpl_canvas_1.figure.add_subplot(111, projection='3d')
        X = np.arange(-5, 5, 0.25)
        Y = np.arange(-5, 5, 0.25)
        X, Y = np.meshgrid(X, Y)
        R = np.sqrt(X**2 + Y**2)
        Z = np.sin(R)
        surf = axes.plot_surface(X, Y, Z,
                                 rstride=1,
                                 cstride=1,
                                 cmap=matplotlib.cm.coolwarm,
                                 linewidth=0,
                                 antialiased=False)
        axes.set_zlim(-1.01, 1.01)
        axes.zaxis.set_major_locator(matplotlib.ticker.LinearLocator(10))
        axes.zaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%.02f'))
        mpl_canvas_1.figure.colorbar(surf, shrink=0.5, aspect=5)
        mpl_canvas_1.canvas.draw()


#
# mpl.Plot2D
#
def test_mpl_plot_2d(mpl_plot_2d_1, mpl_plot_2d_2, mpl_plot_2d_3, mpl_plot_2d_4, mpl_plot_2d_stop, **kwargs):
    x = 0.0
    y = 0.0
    mpl_plot_2d_1.clear()
    mpl_plot_2d_2.clear()
    mpl_plot_2d_3.clear()
    mpl_plot_2d_4.clear()
    mpl_plot_2d_1.set_plot_properties(
        title='Random Walk',
        x_label='x position',
        y_label='y position',
        aspect_ratio='equal')
    mpl_plot_2d_1.new_curve('random_walk', memory='growable', length=10000, animated=True,
                  line_color='red', line_width=0.5)
    mpl_plot_2d_2.set_plot_properties(
        title='Polar Random Walk',
        x_label='theta position',
        y_label='r position',
        aspect_ratio='equal')
    mpl_plot_2d_2.new_curve('random_walk', memory='growable', length=10000, animated=True,
                  line_color='red', line_width=0.5)
    mpl_plot_2d_3.set_plot_properties(
        title='Random Image',
        x_label='r position',
        y_label='t position',
        aspect_ratio='equal')
    mpl_plot_2d_3.new_image('random', interpolation='nearest')
    mpl_plot_2d_4.set_plot_properties(
        title='Random Polar Image',
        x_label='r position',
        y_label='t position',
        aspect_ratio='equal')
    # color mesh, make the grid
    r_steps = 10
    theta_steps = 10
    theta_grid = np.linspace(0, 2*np.pi, theta_steps+1, endpoint=True)
    r_grid = np.linspace(0, 1.0, r_steps+1, endpoint=True)
    X, Y = np.meshgrid(theta_grid, r_grid)
    mpl_plot_2d_4.new_colormesh('random', X, Y)
    while True:
        x += random.uniform(-1.0, 1.0)
        y += random.uniform(-1.0, 1.0)
        mpl_plot_2d_1.append_data('random_walk', (x, y))
        mpl_plot_2d_2.append_data('random_walk', (x, y))
        image = np.random.rand(10, 10)
        mpl_plot_2d_3.set_data('random', image)
        mpl_plot_2d_4.set_data('random', image)
        if mpl_plot_2d_stop.value: break
    mpl_plot_2d_stop.value = False


def test_event_mpl_plot_2d_4(mpl_plot_2d_4, **kwargs):
    event = mpl_plot_2d_4.events.pop()
    print 'EVENT:', event.name


#
# mpl.Chart2D
#
def test_mpl_chart_2d_1_1(mpl_chart_2d_1, **kwargs):
    global last_x1
    xs = np.arange(0.0, 20.0, 0.01)
    ys_1 = 2*np.sin(2*pi*xs)
    ys_2 = npr.rand(len(xs))
    ys_3 = 2*np.cos(2*pi*xs)
    ys_4 = -npr.rand(len(xs))
    data = np.column_stack([xs, ys_1, ys_2, ys_3, ys_4])
    mpl_chart_2d_1.curves_per_plot = (2, 1, 1)
    mpl_chart_2d_1.set_data(data)
    last_x1 = xs[-1]

def test_mpl_chart_2d_1_2(mpl_chart_2d_1, **kwargs):
    mpl_chart_2d_1.set_curve_properties(0, line_color='red', line_width=2)
    mpl_chart_2d_1.set_curve_properties(1, line_color='violet', line_width=1)
    mpl_chart_2d_1.set_curve_properties(2, line_color='orange', line_width=2)
    mpl_chart_2d_1.set_curve_properties(3, line_color='green', line_width=1)
    mpl_chart_2d_1.update()

def test_mpl_chart_2d_1_3(mpl_chart_2d_1, **kwargs):
    global last_x1
    xs = np.arange(last_x1, last_x1+20.0, 0.01)
    ys_1 = 2*np.sin(2*pi*xs)
    ys_2 = npr.rand(len(xs))
    ys_3 = 2*np.cos(2*pi*xs)
    ys_4 = -npr.rand(len(xs))
    data = np.column_stack([xs, ys_1, ys_2, ys_3, ys_4])
    mpl_chart_2d_1.append_data(data)
    last_x1 = xs[-1]

def test_mpl_chart_2d_1_clear(mpl_chart_2d_1, **kwargs):
    mpl_chart_2d_1.clear()


#
# MPLPlot
#
def test_mpl_plot_1_1(mpl_plot_1, **kwargs):
    t = np.arange(0.0, 2.0, 0.01)
    s = np.sin(2*pi*t)
    mpl_plot_1.plot(t, s, linewidth=1.0)
    mpl_plot_1.set_xlabel('time (s)')
    mpl_plot_1.set_ylabel('voltage (mV)')
    mpl_plot_1.set_title('Simple Plot')
    mpl_plot_1.grid(True)
    mpl_plot_1.show()

def test_mpl_plot_1_2(mpl_plot_1, **kwargs):
    N = 150
    r = 2*npr.rand(N)
    theta = 2*pi*npr.rand(N)
    area = 200*r**2*npr.rand(N)
    colors = theta
    mpl_plot_1.setup_axes(projection='polar')
    mpl_plot_1.scatter(theta, r, c=colors, s=area)
    mpl_plot_1.show()

def test_mpl_plot_1_3(mpl_plot_1, **kwargs):
    N = 5
    xs = np.arange(N)
    y1s = npr.rand(len(xs))
    y2s = npr.rand(len(xs))
    width=0.35
    mpl_plot_1.bar(xs, y1s, width, color='r')
    mpl_plot_1.bar(xs+width, y2s, width, color='y')
    mpl_plot_1.set_xticks(xs+width)
    mpl_plot_1.set_xticklabels(('A', 'B', 'C', 'D', 'E'))
    mpl_plot_1.set_xlabel('Group')
    mpl_plot_1.set_ylabel('Scores')
    mpl_plot_1.set_title('Simple Bar Chart')
    mpl_plot_1.show()

def test_mpl_plot_1_4(mpl_plot_1, **kwargs):
    zs = 100*np.random.rand(100, 150)
    mpl_plot_1.imshow(zs, interpolation='nearest', animated=True)
    mpl_plot_1.set_xlabel('X')
    mpl_plot_1.set_ylabel('Y')
    mpl_plot_1.set_title('Image Plot')
    mpl_plot_1.colorbar()
    mpl_plot_1.show()

def test_mpl_plot_1_5(mpl_plot_1, **kwargs):
    r_steps = 20
    theta_steps = 80
    mpl_plot_1.setup_axes(projection='polar')
    theta_grid, step = np.linspace(0, 2*np.pi, theta_steps+1, endpoint=True, retstep=True)
    theta_grid -= step/2.0
    r_grid = np.linspace(0, 1.0, r_steps+1, endpoint=True)
    X, Y = np.meshgrid(theta_grid, r_grid) #rectangular plot of polar data
    zs = np.zeros((r_steps, theta_steps))
    thetas = np.linspace(0, 2*np.pi, theta_steps, endpoint=False)
    rs, step = np.linspace(0, 1.0, r_steps, endpoint=False, retstep=True)
    rs += step/2.0
    for ri in range(r_steps):
        for ti in range(theta_steps):
            zs[ri, ti] = np.sin(2*np.pi*rs[ri])*np.cos(4*thetas[ti])
    #mpl_plot_1.pcolormesh(X, Y, zs)
    #mpl_plot_1.pcolor(X, Y, zs)
    #mpl_plot_1.pcolorfast(X, Y, zs)
    mpl_plot_1.pcolor(X, Y, zs)
    mpl_plot_1.set_title('Polar Image Plot')
    mpl_plot_1.show()
    zs2 = zs.copy()
    for ri in range(r_steps):
        for ti in range(theta_steps):
            zs2[ri, ti] = np.sin(2*np.pi*rs[ri])*np.sin(4*thetas[ti])
    mpl_plot_1.update_pcolor_data(zs2)
    mpl_plot_1.show()
    mpl_plot_1.update_pcolor_data(zs)
    mpl_plot_1.show()

def test_mpl_plot_1_clear(mpl_plot_1, **kwargs):
    mpl_plot_1.reset()
    mpl_plot_1.show()


#
# PyQtGraph - loaded directly, no wrapper
#
def test_pyqtgraph(pyqtgraph, pyqtgraph_plot_widget, pyqtgraph_graphics_layout_widget, **kwargs):
    #pyqtgraph.setConfigOption('background', 'w')
    #pyqtgraph.setConfigOption('foreground', 'k')
    pyqtgraph_plot_widget.clear()
    xs = np.arange(0, 30, 0.1)
    ys = np.sin(xs)
    curve = pyqtgraph_plot_widget.plot(xs, ys, pen='b')
    for i in range(100):
        ys = np.sin(xs + (i+1)*2*np.pi/100)
        curve.setData(xs, ys)

    # this is the pyqtgraph GraphicsLayout Example
    pg = pyqtgraph
    l = pyqtgraph_graphics_layout_widget
    ## Title at top
    text = """
    This example demonstrates the use of GraphicsLayout to arrange items in a grid.<br>
    The items added to the layout must be subclasses of QGraphicsWidget (this includes <br>
    PlotItem, ViewBox, LabelItem, and GrphicsLayout itself).
    """
    l.addLabel(text, col=1, colspan=4)
    l.nextRow()

    ## Put vertical label on left side
    l.addLabel('Long Vertical Label', angle=-90, rowspan=3)

    ## Add 3 plots into the first row (automatic position)
    p1 = l.addPlot(title="Plot 1")
    p2 = l.addPlot(title="Plot 2")
    vb = l.addViewBox(lockAspect=True)
    img = pg.ImageItem(np.random.normal(size=(100,100)))
    vb.addItem(img)
    vb.autoRange()

    ## Add a sub-layout into the second row (automatic position)
    ## The added item should avoid the first column, which is already filled
    l.nextRow()
    l2 = l.addLayout(colspan=3, border=(50,0,0))
    l2.setContentsMargins(10, 10, 10, 10)
    l2.addLabel("Sub-layout: this layout demonstrates the use of shared axes and axis labels", colspan=3)
    l2.nextRow()
    l2.addLabel('Vertical Axis Label', angle=-90, rowspan=2)
    p21 = l2.addPlot()
    p22 = l2.addPlot()
    l2.nextRow()
    p23 = l2.addPlot()
    p24 = l2.addPlot()
    l2.nextRow()
    l2.addLabel("HorizontalAxisLabel", col=1, colspan=2)

    ## hide axes on some plots
    p21.hideAxis('bottom')
    p22.hideAxis('bottom')
    p22.hideAxis('left')
    p24.hideAxis('left')
    p21.hideButtons()
    p22.hideButtons()
    p23.hideButtons()
    p24.hideButtons()

    ## Add 2 more plots into the third row (manual position)
    p4 = l.addPlot(row=3, col=1)
    p5 = l.addPlot(row=3, col=2, colspan=2)

    ## show some content in the plots
    p1.plot([1,3,2,4,3,5])
    p2.plot([1,3,2,4,3,5])
    p4.plot([1,3,2,4,3,5])
    p5.plot([1,3,2,4,3,5])

#
# qwt.Chart
#
def test_qwt_chart_1_1(qwt_chart_1, **kwargs):
    global last_x1
    xs = np.arange(0.0, 20.0, 0.01)
    ys_1 = 2*np.sin(2*pi*xs)
    ys_2 = npr.rand(len(xs))
    ys_3 = 2*np.cos(2*pi*xs)
    ys_4 = -npr.rand(len(xs))
    data = np.column_stack([xs, ys_1, ys_2, ys_3, ys_4])
    qwt_chart_1.curves_per_plot = (2, 2)
    qwt_chart_1.set_plot_properties(0, title='Data 1', x_title='time (s)',
                                y_title='distance (m)')
    qwt_chart_1.set_plot_properties(1, title='Data 2', x_title='speed (m/s)',
                                y_title='height (m)')
    qwt_chart_1.span = 100
    qwt_chart_1.data = data
    last_x1 = xs[-1]

def test_qwt_chart_1_2(qwt_chart_1, **kwargs):
    qwt_chart_1.set_plot_properties(0, background='yellow', x_grid=True,
                                y_grid=True)
    qwt_chart_1.set_plot_properties(1, background='pink', x_grid=True, y_grid=True,
                                dashed_grid=True)
    qwt_chart_1.set_curve_properties(0, line_color='red', line_width=2)
    qwt_chart_1.set_curve_properties(1, line_color='green', line_width=1)
    qwt_chart_1.set_curve_properties(2, line_color='yellow', line_width=2)
    qwt_chart_1.set_curve_properties(3, line_color='blue', line_width=1)
    qwt_chart_1.update()

def test_qwt_chart_1_3(qwt_chart_1, **kwargs):
    global last_x1
    xs = np.arange(last_x1, last_x1+20.0, 0.01)
    ys_1 = 2*np.sin(2*pi*xs)
    ys_2 = npr.rand(len(xs))
    ys_3 = 2*np.cos(2*pi*xs)
    ys_4 = -npr.rand(len(xs))
    data = np.column_stack([xs, ys_1, ys_2, ys_3, ys_4])
    qwt_chart_1.append_array(data)
#    qwt_chart_1.append(data[0])
    last_x1 = xs[-1]

def test_qwt_chart_1_clear(qwt_chart_1, **kwargs):
    qwt_chart_1.clear()


#
# qwt.Plot
#
def test_qwt_plot_1_1(qwt_plot_1, **kwargs):
    global first_x2, last_x2
    xs = np.arange(0.0, 2.0, 0.01)
    data_1 = 2*np.sin(2*pi*xs)
    data_2 = npr.rand(len(xs))
    data_3 = 2*np.cos(2*pi*xs)
    data_4 = -npr.rand(len(xs))
    qwt_plot_1.set_plot_properties(title='Data 1', x_title='time (s)', y_title='distance (m)')
    qwt_plot_1.new_element('first_curve', 'curve')
    qwt_plot_1.set_element_data('first_curve', x=xs, y=data_1)
    qwt_plot_1.new_element('second_curve', 'curve')
    qwt_plot_1.set_element_data('second_curve', x=xs, y=data_2)
    qwt_plot_1.new_element('third_curve', 'curve')
    qwt_plot_1.set_element_data('third_curve', x=xs, y=data_3)
    qwt_plot_1.new_element('fourth_curve', 'curve')
    qwt_plot_1.set_element_data('fourth_curve', x=xs, y=data_4)
    qwt_plot_1.update()

def test_qwt_plot_1_2(qwt_plot_1, **kwargs):
    qwt_plot_1.set_plot_properties(background='yellow', x_grid=True, y_grid=True, dashed_grid=True)
    qwt_plot_1.set_element_properties('first_curve', line_color='red', line_width=2)
    qwt_plot_1.set_element_properties('second_curve', line_color='green', line_width=1)
    qwt_plot_1.set_element_properties('third_curve', line_color='violet', line_width=2)
    qwt_plot_1.set_element_properties('fourth_curve', line_color='blue', line_width=1)
    qwt_plot_1.update()

def test_qwt_plot_1_3(qwt_plot_1, **kwargs):
    xs = np.arange(0.0, 2.0, 0.01)
    data_2 = npr.rand(len(xs))
    data_4 = -npr.rand(len(xs))
    qwt_plot_1.set_element_data('second_curve', x=xs, y=data_2)
    qwt_plot_1.set_element_data('fourth_curve', x=xs, y=data_4)
    qwt_plot_1.update()

#def test_qwt_plot_1_4(qwt_plot_1, **kwargs):
#    zs = np.eye(10, 15)
#    qwt_plot_1.new_element('first_image', 'image')
#    qwt_plot_1.set_element_data('first_image', z=zs)
#    qwt_plot_1.update()

def test_qwt_plot_1_clear(qwt_plot_1, **kwargs):
    qwt_plot_1.clear()


#
# qwt.PointLinePlot
#
def test_point_line_plot_setup(qwt_point_plot_1, **kwargs):
    qwt_point_plot_1.set_plot_properties(x_title='X Axis Label',
                                     y_title='Y Axis Label',
                                     title='Simple XY Plot',
                                     x_grid=True, y_grid=True,
                                     dashed_grid=True)

def test_qwt_point_line_plot_1_point(qwt_point_plot_1,
                            point_plot_symbol,
                            point_plot_line_color,
                            point_plot_fill_color,
                            point_plot_line_width,
                            point_plot_size,
                            **kwargs):
    x = 10*random.random()
    y = 10*random.random()
    qwt_point_plot_1.draw_point((x, y),
                            symbol=point_plot_symbol.value,
                            line_color=point_plot_line_color.value,
                            fill_color=point_plot_fill_color.value,
                            line_width=point_plot_line_width.value,
                            size=point_plot_size.value)

def test_qwt_point_line_plot_1_line(qwt_point_plot_1,
                           point_plot_line_color,
                           point_plot_line_width,
                           **kwargs):
    x1 = 10*random.random()
    y1 = 10*random.random()
    x2 = 10*random.random()
    y2 = 10*random.random()
    qwt_point_plot_1.draw_line((x1, y1), (x2, y2),
                           line_color=point_plot_line_color.value,
                           line_width=point_plot_line_width.value)

def test_qwt_point_line_plot_1_line_to(qwt_point_plot_1,
                              point_plot_line_color,
                              point_plot_line_width,
                              **kwargs):
    x = 10*random.random()
    y = 10*random.random()
    qwt_point_plot_1.draw_line_to((x, y),
                              line_color=point_plot_line_color.value,
                              line_width=point_plot_line_width.value)

def test_qwt_point_line_plot_1_start_line(qwt_point_plot_1, **kwargs):
    x = 10*random.random()
    y = 10*random.random()
    qwt_point_plot_1.start_line((x, y))

def test_qwt_point_line_plot_1_clear(qwt_point_plot_1, **kwargs):
    qwt_point_plot_1.clear()


def test_qwt_point_line_plot_1_draw_point_and_points(qwt_point_plot_1,
                            point_plot_symbol,
                            point_plot_line_color,
                            point_plot_fill_color,
                            point_plot_line_width,
                            point_plot_size,
                            **kwargs):
    x = 10*random.random()
    y = 10*random.random()
    qwt_point_plot_1.draw_point((x, y), key='test_point',
                            symbol=point_plot_symbol.value,
                            line_color=point_plot_line_color.value,
                            fill_color=point_plot_fill_color.value,
                            line_width=point_plot_line_width.value,
                            size=point_plot_size.value)
    qwt_point_plot_1.draw_points(npr.rand(5,2), key='test_points',
                            symbol=point_plot_symbol.value,
                            line_color=point_plot_line_color.value,
                            fill_color=point_plot_fill_color.value,
                            line_width=point_plot_line_width.value,
                            size=point_plot_size.value)

def test_qwt_point_line_plot_1_change_point_data(qwt_point_plot_1, **kwargs):
    x = 10*random.random()
    y = 10*random.random()
    qwt_point_plot_1.change_point_data((x, y), key='test_point')
    qwt_point_plot_1.change_points_data(npr.rand(5,2), key='test_points')

def test_qwt_point_line_plot_1_change_point_properties(qwt_point_plot_1,
                            point_plot_symbol,
                            point_plot_line_color,
                            point_plot_fill_color,
                            point_plot_line_width,
                            point_plot_size,
                            **kwargs):
    qwt_point_plot_1.change_point_properties(key='test_point',
                            symbol=point_plot_symbol.value,
                            line_color=point_plot_line_color.value,
                            fill_color=point_plot_fill_color.value,
                            line_width=point_plot_line_width.value,
                            size=point_plot_size.value)
    qwt_point_plot_1.change_point_properties(key='test_points',
                            symbol=point_plot_symbol.value,
                            line_color=point_plot_line_color.value,
                            fill_color=point_plot_fill_color.value,
                            line_width=point_plot_line_width.value,
                            size=point_plot_size.value)

def test_qwt_point_line_plot_1_draw_line_and_lines(qwt_point_plot_1,
                           point_plot_line_color,
                           point_plot_line_width,
                           **kwargs):
    x1 = 10*random.random()
    y1 = 10*random.random()
    x2 = 10*random.random()
    y2 = 10*random.random()
    qwt_point_plot_1.draw_line((x1, y1), (x2, y2), key='test_line',
                           line_color=point_plot_line_color.value,
                           line_width=point_plot_line_width.value)
    qwt_point_plot_1.draw_lines(npr.rand(5,2), key='test_lines',
                           line_color=point_plot_line_color.value,
                           line_width=point_plot_line_width.value)

def test_qwt_point_line_plot_1_change_line_data(qwt_point_plot_1, **kwargs):
    x1 = 10*random.random()
    y1 = 10*random.random()
    x2 = 10*random.random()
    y2 = 10*random.random()
    qwt_point_plot_1.change_line_data((x1, y1), (x2, y2), key='test_line')
    qwt_point_plot_1.change_lines_data(npr.rand(5,2), key='test_lines')


def test_qwt_point_line_plot_1_change_line_properties(qwt_point_plot_1,
                           point_plot_line_color,
                           point_plot_line_width,
                           **kwargs):
    qwt_point_plot_1.change_line_properties(key='test_line',
                           line_color=point_plot_line_color.value,
                           line_width=point_plot_line_width.value)
    qwt_point_plot_1.change_line_properties(key='test_lines',
                           line_color=point_plot_line_color.value,
                           line_width=point_plot_line_width.value)
