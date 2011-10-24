################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation. 
#
#See the license text in license.txt
#
#copyright 2008, University of Tennessee
################################################################################

The inversionview is responsible for creating and maintaining the graphical
component of the P(r) inversion perspective. It uses the sans.guiframe
package to create the necessary panels and widgets. The sans.dataloader is
used to transmit data to the GUI and the pr_inversion package is used
to perform the actual P(r) inversion calculations.