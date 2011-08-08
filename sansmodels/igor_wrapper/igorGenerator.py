#!/usr/bin/env python
""" WrapperGenerator class to generate model code automatically.
  
  This code was written as part of the DANSE project
  http://danse.us/trac/sans/wiki/WikiStart
 
"""

import os, sys

class WrapperGenerator:
    """ Python wrapper generator for C models
    
        The developer must provide a header file describing 
        the new model.
                
        @author: Mathieu Doucet / UTK
        @contact: mathieu.doucet@nist.gov
    """
    
    def __init__(self, filename, args):
        """ Initialization 
            @param filename: path of header file to wrap
            @param args: list of parameters to disperse
        """
        
        ## Name of .h file to generate wrapper from
        self.file = filename
        
        # Info read from file
        
        ## Name of python class to write
        self.pythonClass = None
        ## Parser in struct section
        self.inStruct = False
        ## Name of struct for the c object
        self.structName = None
        ## Dictionary of parameters
        self.params = {}
        ## ModelCalculation module flag
        self.modelCalcFlag = False
        ## List of default parameters (text)
        self.default_list = ""
        ## Base struct name
        self.base_struct = ""
        ## Base header file name
        self.base_header = ""
        ## Bindings to parameter array
        self.translation_list = ""
        self.counter = 0
        self.disperse_count = 0
        self.disperse_code = ""
        self.added_list = ""
        self.phi_index = -1
        self.theta_index = -1
        
        self.disp_list = args
            
        
    def read(self):
        """ Reads in the .h file to catch parameters of the wrapper """
        
        # Check if the file is there
        if not os.path.isfile(self.file):
            raise ValueError, "File %s is not a regular file" % self.file
        
        # Read file
        f = open(self.file,'r')
        buf = f.read()
        
        self.default_list = "    // List of default parameters:\n"
        #lines = string.split(buf,'\n')
        lines = buf.split('\n')
        for line in lines:
            
            # Catch class name
            key = "[PYTHONCLASS]"
            if line.count(key)>0:
                try:
                    index = line.index(key)
                    #toks = string.split( line[index:], "=" )
                    toks = line[index:].split("=" )
                    self.pythonClass = toks[1].lstrip().rstrip()
                except:
                    raise ValueError, "Could not parse file %s" % self.file
                
            # Catch struct name
            if line.count("typedef struct")>0:
                # We are entering a struct block
                self.inStruct = True
            
            if self.inStruct and line.count("}")>0:
                # We are exiting a struct block
                self.inStruct = False
    
                # Catch the name of the struct
                index = line.index("}")
                #toks = string.split(line[index+1:],";")
                toks = line[index+1:].split(";")
                # Catch pointer definition
                #toks2 = string.split(toks[0],',')
                toks2 = toks[0].split(',')
                self.structName = toks2[0].lstrip().rstrip()
                
            # Catch struct content
            key = "[DEFAULT]"
            if self.inStruct and line.count(key)>0:
                # Found a new parameter
                try:
                    index = line.index(key)
                    toks = line[index:].split("=")
                    toks2 = toks[2].split()
                    val = float(toks2[0])
                    
                    # Find in dispersed list
                    if toks[1] in self.disp_list:
                        print "Found ", toks[1]
                        self.disperse_code += "    // %s\n" % toks[1]
                        self.disperse_code += "    paramList[%i] = %i;\n" % (self.disperse_count, self.counter)
                        self.disperse_count += 1
                        
                    #self.pythonClass = toks[1].lstrip().rstrip()
                    units = ""
                    if len(toks2) >= 2:
                        units = toks2[1]
                    self.default_list += "    //         pars[%i]:   %-15s = %s %s\n" % \
                        (self.counter, toks[1], val, units)
                       
                    # Identify theta and phi indices, if present 
                    if toks[1].count('phi'):
                        self.phi_index = self.counter
                    if toks[1].count('theta'):
                        self.theta_index = self.counter
                        
                    # Bindings
                    self.translation_list += "    danse_pars.%s = pars[%i];\n" % ( toks[1], self.counter)
                    self.counter += 1
                  
                except:
                    raise ValueError, "Could not parse input file %s \n  %s" % \
                        (self.file, sys.exc_value)
                
                
    def write_c_wrapper(self):
        """ 
        Writes the C file to create the dispersed model function
        """
        
        toks = os.path.basename(self.file).split('.')
        file = open("src/disp_"+toks[0]+'.c', 'w')
        template = open("templates/disperse_template.c", 'r')
        
        tmp_buf = template.read()
        #tmp_lines = string.split(tmp_buf,'\n')
        tmp_lines = tmp_buf.split('\n')
        
        
        self.translation_list = self.default_list+self.translation_list
        
        sigma_txt = "\n"
        for i in range(len(self.disp_list)):
            ipar = self.counter+i
            sigma_txt += "    sigmaList[%i] = dp[%i];\n" % (i, ipar)
            
        ipar = self.counter+len(self.disp_list)
        sigma_txt += "\n    npts = (int)(floor(dp[%i]));\n" % ipar
                      
        self.disperse_code += sigma_txt
        
        # Document the added (dispersed) parameters
        added_pars_txt = "\n"
        for i in range(len(self.disp_list)):
            ipar = self.counter+i
            added_pars_txt += "    //         pars[%i]:   dispersion of %s\n" % (ipar, self.disp_list[i])
            
        ipar = self.counter+len(self.disp_list)
        added_pars_txt += "    //         pars[%s]:   number of points in dispersion curve\n" % \
                    str(self.counter+len(self.disp_list))                              
        
        
        for tmp_line in tmp_lines:
            
            # Catch class name
            newline = self.replaceToken(tmp_line, 
                                        "[PYTHONCLASS]", 'C'+self.pythonClass)
            
            # Catch class name
            newline = self.replaceToken(newline, 
                                        "[MODELSTRUCT]", self.structName)
            
            # Dictionary initialization
            param_str = "// bindings to parameter array\n"
            newline = self.replaceToken(newline, 
                                        "[BINDINGS]", self.translation_list)
                            
            newline = self.replaceToken(newline, 
                                        "[DISPERSE]", self.disperse_code)
            
            # Name of .c file
            #toks = string.split(self.file,'.')
            toks = os.path.basename(self.file).split('.')
            newline = self.replaceToken(newline, "[C_FILENAME]", toks[0])
            
            # Include file
            newline = self.replaceToken(newline, 
                                        "[INCLUDE_FILE]", os.path.basename(self.file))
            
            # Include file
            newline = self.replaceToken(newline, 
                                        "[NDISPERSE]", str(len(self.disp_list)))
            
            # Number of parameters
            newline = self.replaceToken(newline, 
                                        "[NPARS]", str(self.counter+len(self.disp_list)+1))
            
            # Documentation
            newline = self.replaceToken(newline, 
                                        "[PARS_LIST]", self.default_list+added_pars_txt)
            
            # Write new line to the wrapper .c file
            file.write(newline+'\n')
            
            
        file.close()
        
        
    def write_weight_function(self):
        """ 
            Writes the C file to create the dispersed model function
            with angular distributions
        """
        # If we dont' have any angle, just return
        if self.phi_index<0 and self.theta_index<0:
            return
        
        
        toks = os.path.basename(self.file).split('.')
        file = open("src/weighted_"+toks[0]+'.c', 'w')
        template = open("templates/weighted_template.c", 'r')
        
        tmp_buf = template.read()
        tmp_lines = tmp_buf.split('\n')
           
        #self.translation_list = self.default_list+self.translation_list
        added_pars_txt = "\n"
        for i in range(len(self.disp_list)):
            ipar = self.counter+i
            added_pars_txt += "    //         pars[%i]:   dispersion of %s\n" % (ipar, self.disp_list[i])
            
        ipar = self.counter+len(self.disp_list)
        added_pars_txt += "    //         pars[%s]:   number of points in dispersion curve\n" % \
                    str(self.counter+len(self.disp_list))
        added_pars_txt += " * \n"
        added_pars_txt += " * NOTE: DO NOT USE THETA AND PHI PARAMETERS WHEN\n"
        added_pars_txt += " *       USING THIS FUNCTION TO APPLY ANGULAR DISTRIBUTIONS."  
                              
        
        
        for tmp_line in tmp_lines:
            
            # Catch class name
            newline = self.replaceToken(tmp_line, 
                                        "[PYTHONCLASS]", self.pythonClass)
            
            # Dictionary initialization
            param_str = "// bindings to parameter array\n"
            newline = self.replaceToken(newline, 
                                        "[PARS_LIST]", self.default_list+added_pars_txt)
                            
            # Name of .c file
            #toks = string.split(self.file,'.')
            toks = os.path.basename(self.file).split('.')
            newline = self.replaceToken(newline, "[MODEL_NAME]", toks[0])
            
            toks = os.path.basename(self.file).split('.')
            newline = self.replaceToken(newline, "[C_FILE_NAME]", "disp_%s.c" % toks[0])
            
            # Include file
            newline = self.replaceToken(newline, 
                                        "[INCLUDE_FILE]", os.path.basename(self.file))
            
            # Include file
            #newline = self.replaceToken(newline, 
            #                            "[NDISPERSE]", str(len(self.disp_list)))
            
            # Number of parameters
            newline = self.replaceToken(newline, 
                                        "[NPARS]",  str(self.counter+len(self.disp_list)+1))
            
            # Theta index
            newline = self.replaceToken(newline, 
                                        "[THETA_INDEX]",  str(self.theta_index))
            
            # Phi index
            newline = self.replaceToken(newline, 
                                        "[PHI_INDEX]",  str(self.phi_index))
            
            # Write new line to the wrapper .c file
            file.write(newline+'\n')
            
            
        file.close()
        
    def replaceToken(self, line, key, value): #pylint: disable-msg=R0201
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
        
        
# main
if __name__ == '__main__':
    if len(sys.argv)>1:
        print "Will look for file %s" % sys.argv[1]
        app = WrapperGenerator(sys.argv[1], sys.argv[2:])
        app.read()
        app.write_c_wrapper()
        app.write_weight_function()
    else:
        print "Usage: python igorGenerator.py [header file] [list of parameters to disperse]"
        print ""
        print "Example: "
        print "    python igorGenerator.py cylinder.h cyl_phi cyl_theta"
   
# End of file        