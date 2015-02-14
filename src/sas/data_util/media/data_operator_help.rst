..data_operator_help.rst

.. This is a port of the original SasView html help file to ReSTructured text
.. by S King, ISIS, during SasView CodeCamp-III in Feb 2015.

Data Operations Tool
====================

Description
-----------
This dialog panel provides arithmetic operations between two data sets (the 
last data set could be a number).

When the data1 and data2 are selected, their x (or qx and qy for 2D) value(s) 
must match with each other.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

How To
------
1. Type the data name resulted from an operation.

2) Select a data/theory in the drop down menus. When data2 is set to number, 
type a number in the text control box.

3) Select an arithmetic operator symbol; + (for addition), - (for subtraction), 
* (for multiplication), / (for division), and | (for combination of two data 
sets).

If two data sets do not match, the operation will fail and the background color 
of the combo box items will turn to red (WIN only).

4) If the operation is successful, hit the Apply button to make the new data.
Then the data name will be shown up in the data box in the data explorer.

Note: The errors and warnings will be displayed at the bottom of the SasView 
window.

.. image:: data_oper_pic.png

