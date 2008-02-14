#!/usr/bin/env python
## \mainpage DANSE wrapper code for IGOR
#
# \section intro_sec Introduction
# This module provides automatically generated code to help
# use DANSE code in third party software like IGOR.
#
# Look under the Files tab of the Doxygen information
# for details about the models. 
#
"""
    @copyright 2007: University of Tennessee, for the DANSE project
"""

import os

def write_header(path = 'src'):
    """
        Write a header file that imports all the header files in a directory
        @param path: include path to analyze
    """
    
    # Write a line for each file
    # "double oriented_[C_FILENAME]_2D(double pars[], double q, double phi)"
        #double disperse_cylinder_analytical_2D(double dp[], double q, double phi) {


    
    headerfile = open('include/danse.h', 'w')
    template = open("templates/function_header_template.h", 'r')
    
    tmp_buf = template.read()
    tmp_lines = tmp_buf.split('\n')
    
    # Get header file list
    file_list = os.listdir(path)
    func_list = ''
    for file in file_list:
        # Look for 'disp'
        if file[:5]=='disp_':    
            toks = file[5:].split('.')
            func_list += "double oriented_%s_2D(double pars[], double q, double phi);\n" % toks[0]
            func_list += "double disperse_%s_analytical_2D(double dp[], double q, double phi);\n" % toks[0]
            
            func_list += "double %s_Weights(double dp[], double *phi_values, double *phi_weights, int n_phi,\n" % toks[0]
            func_list += "    double *theta_values, double *theta_weights, int n_theta, "
            func_list += "double q, double phi_q);\n\n"
            
            print "Found %s" % file
    
    for tmp_line in tmp_lines:
        
        # Include file
        newline = replaceToken(tmp_line, 
                                    "[FUNCTION_LIST]", func_list)
        
        # Write new line to the wrapper .c file
        headerfile.write(newline+'\n')            
    
    headerfile.close()
    
def replaceToken(line, key, value): #pylint: disable-msg=R0201
    """ Replace a token in the template file 
        @param line: line of text to inspect
        @param key: token to look for
        @param value: string value to replace the token with
        @return: new string value
    """
    lenkey = len(key)
    newline = line
    while newline.count(key)>0:
        index = newline.index(key)
        newline = newline[:index]+value+newline[index+lenkey:]
    return newline

    
if __name__ == '__main__':
    write_header()
