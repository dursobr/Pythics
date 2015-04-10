.. _programming:


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

.. figure:: _static/process_diagram.png
   :width: 80%
   :align: center

   Data flow betweeen processes and threads in Pythics.

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

.. literalinclude:: _static/minimal_document.html

The `head` is actually completely optional, although the defaults that are used 
without a `head` are typically not desirable.


HTML Elements
-------------

- `<html>`: begin and end `html` tags should surround the whole document

- `<head>`: used to surround the header of the document, which contains `title` 
  `style` elements

- `<style type='text/css'>`:

- `<title>`: The text between `title` start and end tags will be used as the 
  VI tab title and the window title when the VI tab is selected

- `<body>`: surrounds the main body of the html document (everything but the 
  document header)

- `<h1>`, `<h2>`, ... `<h6>`: text placed on its own line, typically used for 
  VI or section names

- `<p>`: text which is not on its own line

- `<hr/>`: insert a horizontal line, typeically as a separator between sections 
  (no closing tag needed)

- `<br/>`: insert a line break to start the next elements on a new line (no 
  closing tag needed)

- `<table>`: use a table to arrange elements

- `<object>`: used to insert a control object into a VI interface, see details
  below


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

.. literalinclude:: _static/typical_css.html


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


Parameters and Python API
-------------------------

See automatically generated API documetation, which lists parameters for 
specifying the behavior of each control from the html file as well as the 
methods and properties of the control accessible from a VI's Python code.
