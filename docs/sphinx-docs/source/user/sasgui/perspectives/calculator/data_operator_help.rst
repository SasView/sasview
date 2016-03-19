.. data_operator_help.rst

.. This is a port of the original SasView html help file to ReSTructured text
.. by S King, ISIS, during SasView CodeCamp-III in Feb 2015.

Data Operations Tool
====================

Description
-----------

This tool permits arithmetic operations between two data sets. Alternatively, 
the last data set can be a number.

*NOTE! When* Data1 *and* Data2 *are both data, their Q (or Qx and Qy for 2D) 
value(s) must match with each other UNLESS using the 'append' operator.*

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Using the tool
--------------

1) Ensure you have loaded data into the *Data Explorer* (see :ref:`Loading_data`).

2) Select *Data Operation* from the *Tool* menu on the SasView toolbar.

3) Select a dataset/theory in the drop-down menu *Data1*. A mini-plot of the
   data will appear underneath.

4) Select a dataset/theory in the drop-down menu *Data2* or select *Number* 
   and enter a number in the box that appears alongside.

5) Select an arithmetic operator symbol from the *Operator* drop-down. The 
   available operators are:
   
*   \+ (for addition)
*   \- (for subtraction) 
*   \* (for multiplication)
*   \/ (for division)
*   \| (for combination of two data sets)

   If two data sets do not match, the operation will fail and the background 
   color of the combo box items will turn to red (WIN only).

6) If the operation is successful, hit the Apply button to make the new dataset.
   The new dataset will appear in the *Data Explorer*.

*NOTE! Any errors and warnings will be displayed at the bottom of the SasView
window.*

.. image:: data_oper_pic.png

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. note::  This help document was last changed by Steve King, 01May2015
