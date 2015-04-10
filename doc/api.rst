.. _api:


***********
Pythics API
***********

This section describes the html *parameters* as well as the Python attributes 
and methods of all the standard controls which are included with the Pythics 
distribution.

HTML paramter names and values must always be passed as strings (surrounded 
with single or double quotes). Many of the HTML parameter descriptions include 
a listing of the allowed values for the parameter, with the default value 
emphasized. For example, in ('True' or *'False'*), the value 'False' is the 
default value if no value is specified.


Controls
--------

These controls are built in and always loaded. You should omit ``controls.`` 
from the start of the ``classid`` when using these controls.

.. automodule:: controls
   :members:
   :undoc-members:
   :inherited-members:
   :exclude-members: Dial, ImageWithShared


Matplotlib Controls
-------------------

These controls are from the matplotlib library. This library optional for 
Pythics (although strongly recommended for plotting) and is not loaded if none 
of these controls are used. When these controls are used, the ``classid`` must 
begin with ``mpl.``.

.. automodule:: mpl
   :members:
   :undoc-members:
   :inherited-members:


PyQwt Controls
--------------

These controls are from the PyQwt library. This library optional for Pythics
and is not loaded if none of these controls are used. When these controls are 
used, the ``classid`` must begin with ``qwt.``.

.. automodule:: qwt
   :members:
   :undoc-members:
   :inherited-members:


Deprecated Controls
-------------------

These controls have been replaced by newer controls and will likely be removed
from Pythics in the near future. When these controls are used, the ``classid`` 
must begin with ``deprecated.``.

.. automodule:: deprecated
   :members:
   :undoc-members:
   :inherited-members:
