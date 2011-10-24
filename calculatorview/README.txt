################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation. 
#
#See the license text in license.txt
#
#copyright 2008, University of Tennessee
################################################################################



Calculatorview is responsible for creating and maintaining the
graphical perspective for the calculator module. It uses the sans.dataloader
and sans.guiframe packages, as well as the sans.calculator and Matplotlib
packages for the mathematical components. 
It provides the following tools:
- SLD Calculator
- Kiessing Calculator
- Resolution Calculator
- Slit Length Calculator


Others packages dependencies are the following:
- wxPython
- periodictable