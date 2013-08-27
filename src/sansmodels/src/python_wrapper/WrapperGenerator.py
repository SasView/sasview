#!/usr/bin/env python
""" WrapperGenerator class to generate model code automatically.
"""

import os, sys,re
import lineparser

class WrapperGenerator:
    """ Python wrapper generator for C models
    
        The developer must provide a header file describing 
        the new model.
        
        To provide the name of the Python class to be
        generated, the .h file must contain the following 
        string in the comments:
        
        // [PYTHONCLASS] = my_model
        
        where my_model must be replaced by the name of the
        class that you want to import from sans.models.
        (example: [PYTHONCLASS] = MyModel
          will create a class MyModel in sans.models.MyModel.
          It will also create a class CMyModel in 
          sans_extension.c_models.)
          
        Also in comments, each parameter of the params 
        dictionary must be declared with a default value
        in the following way:
        
        // [DEFAULT]=param_name=default_value
        
        (example:
            //  [DEFAULT]=radius=20.0
        )
          
        See cylinder.h for an example.
        
        
        A .c file corresponding to the .h file should also
        be provided (example: my_model.h, my_model.c).
    
        The .h file should define two function definitions. For example,
        cylinder.h defines the following:
        
        /// 1D scattering function
        double cylinder_analytical_1D(CylinderParameters *pars, double q);
            
        /// 2D scattering function
        double cylinder_analytical_2D(CylinderParameters *pars, double q, double phi);
            
        The .c file implements those functions.
        
        @author: Mathieu Doucet / UTK
        @contact: mathieu.doucet@nist.gov
    """
    
    def __init__(self, filename, output_dir='.', c_wrapper_dir='.'):
        """ Initialization """
        
        ## Name of .h file to generate wrapper from
        self.file = filename
        
        # Info read from file
        
        ## Name of python class to write
        self.pythonClass = None
        ## Parser in struct section
        self.inStruct = False
        self.foundCPP = False
        self.inParDefs = False
        ## Name of struct for the c object
        self.structName = None
        ## Dictionary of parameters
        self.params = {}
        ## ModelCalculation module flag
        self.modelCalcFlag = False
        ## List of default parameters (text)
        self.default_list = ""
        ## Dictionary of units
        self.details = ""
        ## List of dispersed parameters
        self.disp_params = []
        #model description
        self.description=''
        # paramaters for fittable
        self.fixed= []
        # paramaters for non-fittable
        self.non_fittable= []
        ## parameters with orientation
        self.orientation_params =[]
        ## parameter with magnetism
        self.magentic_params = []
        # Model category
        self.category = None
        # Whether model belongs to multifunc
        self.is_multifunc = False
        ## output directory for wrappers
        self.output_dir = output_dir
        self.c_wrapper_dir = c_wrapper_dir

        
        
    def __repr__(self):
        """ Simple output for printing """
        
        rep  = "\n Python class: %s\n\n" % self.pythonClass
        rep += "  struc name: %s\n\n" % self.structName
        rep += "  params:     %s\n\n" % self.params
        rep += "  description:    %s\n\n" % self.description
        rep += "  Fittable parameters:     %s\n\n"% self.fixed
        rep += "  Non-Fittable parameters:     %s\n\n"% self.non_fittable
        rep += "  Orientation parameters:  %s\n\n"% self.orientation_params
        rep += "  Magnetic parameters:  %s\n\n"% self.magnetic_params
        return rep
        
    def read(self):
        """ Reads in the .h file to catch parameters of the wrapper """
        
        # Check if the file is there
        if not os.path.isfile(self.file):
            raise ValueError, "File %s is not a regular file" % self.file
        
        # Read file
        f = open(self.file,'r')
        buf = f.read()
        
        self.default_list = "List of default parameters:\n"
        #lines = string.split(buf,'\n')
        lines = buf.split('\n')
        self.details  = "## Parameter details [units, min, max]\n"
        self.details += "        self.details = {}\n"
        
        #open item in this case Fixed
        text='text'
        key2="<%s>"%text.lower()
        # close an item in this case fixed
        text='TexT'
        key3="</%s>"%text.lower()
        
        ## Catch fixed parameters
        key = "[FIXED]"
        try:
            self.fixed= lineparser.readhelper(lines, key, 
                                              key2, key3, file=self.file)
        except:
           raise   
        ## Catch non-fittable parameters parameters
        key = "[NON_FITTABLE_PARAMS]"
        try:
            self.non_fittable= lineparser.readhelper(lines, key, key2,
                                                     key3, file=self.file)
        except:
           raise   

        ## Catch parameters with orientation
        key = "[ORIENTATION_PARAMS]"    
        try:
            self.orientation_params = lineparser.readhelper(lines, key, 
                                                    key2, key3, file=self.file)
        except:
           raise 
       
        ## Catch parameters with orientation
        key = "[MAGNETIC_PARAMS]"    
        try:
            self.magnetic_params = lineparser.readhelper( lines,key, 
                                                    key2,key3, file= self.file)
        except:
           raise 
       
        ## Catch Description
        key = "[DESCRIPTION]"
        
        find_description = False
        temp=""
        for line in lines:
            if line.count(key)>0 :
                
                try:
                    find_description= True
                    index = line.index(key)
                    toks = line[index:].split("=",1 )
                    temp=toks[1].lstrip().rstrip()
                    text='text'
                    key2="<%s>"%text.lower()
                    if re.match(key2,temp)!=None:
    
                        toks2=temp.split(key2,1)
                        self.description=toks2[1]
                        text='text'
                        key2="</%s>"%text.lower()
                        if re.search(key2,toks2[1])!=None:
                            temp=toks2[1].split(key2,1)
                            self.description=temp[0]
                            break
                      
                    else:
                        self.description=temp
                        break
                except:
                     raise ValueError, "Could not parse file %s" % self.file
            elif find_description:
                text='text'
                key2="</%s>"%text.lower()
                if re.search(key2,line)!=None:
                    tok=line.split(key2,1)
                    temp=tok[0].split("//",1)
                    self.description+=tok[1].lstrip().rstrip()
                    break
                else:
                    if re.search("//",line)!=None:
                        temp=line.split("//",1)
                        self.description+='\n\t\t'+temp[1].lstrip().rstrip()
                        
                    else:
                        self.description+='\n\t\t'+line.lstrip().rstrip()
                    
                
     
        for line in lines:
            
            # Catch class name
            key = "[PYTHONCLASS]"
            if line.count(key)>0:
                try:
                    index = line.index(key)
                    toks = line[index:].split("=" )
                    self.pythonClass = toks[1].lstrip().rstrip()

                except:
                    raise ValueError, "Could not parse file %s" % self.file
                
            key = "[CATEGORY]"
            if line.count(key)>0:
                try:
                    index = line.index(key)
                    toks = line[index:].split("=")
                    self.category = toks[1].lstrip().rstrip()

                except:
                    raise ValueError, "Could not parse file %s" % self.file

            # is_multifunc
            key = "[MULTIPLICITY_INFO]"
            if line.count(key) > 0:
                self.is_multifunc = True
                try:
                    index = line.index(key)
                    toks = line[index:].split("=")
                    self.multiplicity_info = toks[1].lstrip().rstrip()
                except:
                    raise ValueError, "Could not parse file %s" % self.file

            # Catch struct name
            # C++ class definition
            if line.count("class")>0:
                # We are entering a class definition
                self.inParDefs = True
                self.foundCPP = True
                
            # Old-Style C struct definition
            if line.count("typedef struct")>0:
                # We are entering a struct block
                self.inParDefs = True
                self.inStruct = True
            
            if self.inParDefs and line.count("}")>0:
                # We are exiting a struct block
                self.inParDefs = False
                
                if self.inStruct:
                    self.inStruct = False
                    # Catch the name of the struct
                    index = line.index("}")
                    toks = line[index+1:].split(";")
                    # Catch pointer definition
                    toks2 = toks[0].split(',')
                    self.structName = toks2[0].lstrip().rstrip()
           
            # Catch struct content
            key = "[DEFAULT]"
            if self.inParDefs and line.count(key)>0:
                # Found a new parameter
                try:
                    index = line.index(key)
                    toks = line[index:].split("=")
                    toks2 = toks[2].split()
                    val = float(toks2[0])
                    self.params[toks[1]] = val
                    #self.pythonClass = toks[1].lstrip().rstrip()
                    units = ""
                    if len(toks2) >= 2:
                        units = toks2[1]
                    self.default_list += "         %-15s = %s %s\n" % \
                        (toks[1], val, units)
                    
                    # Check for min and max
                    min = "None"
                    max = "None"
                    if len(toks2) == 4:
                        min = toks2[2]
                        max = toks2[3]
                    
                    self.details += "        self.details['%s'] = ['%s', %s, %s]\n" % \
                        (toks[1].lstrip().rstrip(), units.lstrip().rstrip(), min, max)
                except:
                    raise ValueError, "Could not parse input file %s \n  %s" % \
                        (self.file, sys.exc_value)
                
                
            # Catch need for numerical calculations
            key = "CalcParameters calcPars"
            if line.count(key)>0:
                self.modelCalcFlag = True
                
            # Catch list of dispersed parameters 
            key = "[DISP_PARAMS]"
            if line.count(key)>0:
                try:
                    index = line.index(key)
                    toks = line[index:].split("=")
                    list_str = toks[1].lstrip().rstrip()
                    self.disp_params = list_str.split(',')
                except:
                    raise ValueError, "Could not parse file %s" % self.file

    def write_c_wrapper(self):
        """ Writes the C file to create the python extension class 
            The file is written in C[PYTHONCLASS].c
        """
        file_path = os.path.join(self.c_wrapper_dir, 
                                 "C"+self.pythonClass+'.cpp')
        file = open(file_path, 'w')
        
        template = open(os.path.join(os.path.dirname(__file__), 
                                     "classTemplate.txt"), 'r')
        
        tmp_buf = template.read()
        #tmp_lines = string.split(tmp_buf,'\n')
        tmp_lines = tmp_buf.split('\n')
        
        for tmp_line in tmp_lines:
            
            # Catch class name
            newline = self.replaceToken(tmp_line, 
                                        "[PYTHONCLASS]", 'C'+self.pythonClass)
            #Catch model description
            #newline = self.replaceToken(tmp_line, 
            #                            "[DESCRIPTION]", self.description)
            # Catch C model name
            newline = self.replaceToken(newline, 
                                        "[CMODEL]", self.pythonClass)
            
            # Catch class name
            newline = self.replaceToken(newline, 
                                        "[MODELSTRUCT]", self.structName)

            # Sort model initialization based on multifunc
            if(self.is_multifunc):
                line = "int level = 1;\nPyArg_ParseTuple(args,\"i\",&level);\n"
                line += "self->model = new " + self.pythonClass + "(level);"
            else:
                line = "self->model = new " + self.pythonClass + "();"
    
            newline = self.replaceToken(newline,"[INITIALIZE_MODEL]",
                                            line)
            
            # Dictionary initialization
            param_str = "// Initialize parameter dictionary\n"            
            for par in self.params:
                param_str += "        PyDict_SetItemString(self->params,\"%s\",Py_BuildValue(\"d\",%10.12f));\n" % \
                    (par, self.params[par])

            if len(self.disp_params)>0:
                param_str += "        // Initialize dispersion / averaging parameter dict\n"
                param_str += "        DispersionVisitor* visitor = new DispersionVisitor();\n"
                param_str += "        PyObject * disp_dict;\n"
                for par in self.disp_params:
                    par = par.strip()
                    if par == '':
                        continue
                    param_str += "        disp_dict = PyDict_New();\n"
                    param_str += "        self->model->%s.dispersion->accept_as_source(visitor, self->model->%s.dispersion, disp_dict);\n" % (par, par)
                    param_str += "        PyDict_SetItemString(self->dispersion, \"%s\", disp_dict);\n" % par
                
            # Initialize dispersion object dictionnary
            param_str += "\n"
            
                
            newline = self.replaceToken(newline,
                                        "[INITDICTIONARY]", param_str)
            
            # Read dictionary
            param_str = "    // Reader parameter dictionary\n"
            for par in self.params:
                param_str += "    self->model->%s = PyFloat_AsDouble( PyDict_GetItemString(self->params, \"%s\") );\n" % \
                    (par, par)
                    
            if len(self.disp_params)>0:
                param_str += "    // Read in dispersion parameters\n"
                param_str += "    PyObject* disp_dict;\n"
                param_str += "    DispersionVisitor* visitor = new DispersionVisitor();\n"
                for par in self.disp_params:
                    par = par.strip()
                    if par == '':
                        continue
                    param_str += "    disp_dict = PyDict_GetItemString(self->dispersion, \"%s\");\n" % par
                    param_str += "    self->model->%s.dispersion->accept_as_destination(visitor, self->model->%s.dispersion, disp_dict);\n" % (par, par)
                
            newline = self.replaceToken(newline, "[READDICTIONARY]", param_str)
                
            # Name of .c file
            #toks = string.split(self.file,'.')
            basename = os.path.basename(self.file)
            toks = basename.split('.')
            newline = self.replaceToken(newline, "[C_FILENAME]", toks[0])
            
            # Include file
            basename = os.path.basename(self.file)
            newline = self.replaceToken(newline, 
                                        "[INCLUDE_FILE]", self.file)  
            if self.foundCPP:
                newline = self.replaceToken(newline, 
                            "[C_INCLUDE_FILE]", "")  
                newline = self.replaceToken(newline, 
                            "[CPP_INCLUDE_FILE]", "#include \"%s\"" % basename)  
            else:  
                newline = self.replaceToken(newline, 
                            "[C_INCLUDE_FILE]", "#include \"%s\"" % basename)   
                newline = self.replaceToken(newline, 
                            "[CPP_INCLUDE_FILE]", "#include \"models.hh\"")  
                
            # Numerical calcs dealloc
            dealloc_str = "\n"
            if self.modelCalcFlag:
                dealloc_str = "    modelcalculations_dealloc(&(self->model_pars.calcPars));\n"
            newline = self.replaceToken(newline, 
                                        "[NUMERICAL_DEALLOC]", dealloc_str)     
                
            # Numerical calcs init
            init_str = "\n"
            if self.modelCalcFlag:
                init_str = "        modelcalculations_init(&(self->model_pars.calcPars));\n"
            newline = self.replaceToken(newline, 
                                        "[NUMERICAL_INIT]", init_str)     
                
            # Numerical calcs reset
            reset_str = "\n"
            if self.modelCalcFlag:
                reset_str = "modelcalculations_reset(&(self->model_pars.calcPars));\n"
            newline = self.replaceToken(newline, 
                                        "[NUMERICAL_RESET]", reset_str)     
                
            # Setting dispsertion weights
            set_weights = "    // Ugliness necessary to go from python to C\n"
            set_weights = "    // TODO: refactor this\n"
            for par in self.disp_params:
                par = par.strip()
                if par == '':
                        continue
                set_weights += "    if (!strcmp(par_name, \"%s\")) {\n" % par
                set_weights += "        self->model->%s.dispersion = dispersion;\n" % par
                set_weights += "    } else"
            newline = self.replaceToken(newline, 
                                        "[SET_DISPERSION]", set_weights)     
            
            # Write new line to the wrapper .c file
            file.write(newline+'\n')
            
            
        file.close()
        
    def write_python_wrapper(self):
        """ Writes the python file to create the python extension class 
            The file is written in ../[PYTHONCLASS].py
        """
        file_path = os.path.join(self.output_dir, self.pythonClass+'.py')
        file = open(file_path, 'w')
        template = open(os.path.join(os.path.dirname(__file__), 
                                     "modelTemplate.txt"), 'r')
        
        tmp_buf = template.read()
        tmp_lines = tmp_buf.split('\n')
        
        for tmp_line in tmp_lines:
            
            # Catch class name
            newline = self.replaceToken(tmp_line, 
                                        "[CPYTHONCLASS]", 
                                        'C' + self.pythonClass)
            
            # Catch class name
            newline = self.replaceToken(newline, 
                                        "[PYTHONCLASS]", self.pythonClass)
            
            # Include file
            newline = self.replaceToken(newline, 
                                        "[INCLUDE_FILE]", self.file)    
                   
            # Include file
            newline = self.replaceToken(newline, 
                                        "[DEFAULT_LIST]", self.default_list)
            # model description
            newline = self.replaceToken(newline, 
                                        "[DESCRIPTION]", self.description)
            # Parameter details
            newline = self.replaceToken(newline, 
                                        "[PAR_DETAILS]", self.details)
            
            # Call base constructor
            if self.is_multifunc:
                newline = self.replaceToken(newline,"[CALL_CPYTHON_INIT]",
                    'C' + self.pythonClass + \
                    ".__init__(self,multfactor)\n\tself.is_multifunc = True")
                newline = self.replaceToken(newline,"[MULTIPLICITY_INFO]", 
                                            self.multiplicity_info)
            else:
                newline = self.replaceToken(newline,"[CALL_CPYTHON_INIT]",
                    'C' + self.pythonClass + \
                    ".__init__(self)\n        self.is_multifunc = False")
                newline = self.replaceToken(newline, 
                                            "[MULTIPLICITY_INFO]", "None")

           
            # fixed list  details
            fixed_str = str(self.fixed)
            fixed_str = fixed_str.replace(', ', ',\n                      ')
            newline = self.replaceToken(newline, "[FIXED]", fixed_str)
            
            # non-fittable list details
            pars_str = str(self.non_fittable)
            pars_str = pars_str.replace(', ', 
                                        ',\n                             ')
            newline = self.replaceToken(newline, 
                                        "[NON_FITTABLE_PARAMS]", pars_str)
            
            ## parameters with orientation
            oriented_str = str(self.orientation_params)
            formatted_endl = ',\n                                   '
            oriented_str = oriented_str.replace(', ', formatted_endl)
            newline = self.replaceToken(newline, 
                               "[ORIENTATION_PARAMS]", oriented_str)
           ## parameters with magnetism
            newline = self.replaceToken(newline, 
                               "[MAGNETIC_PARAMS]", str(self.magnetic_params))

            if self.category:
                newline = self.replaceToken(newline, "[CATEGORY]", 
                                            '"' + self.category + '"')
            else:
                newline = self.replaceToken(newline, "[CATEGORY]",
                                            "None")
            


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
        
    def getModelName(self):
        return self.pythonClass
        


# main
if __name__ == '__main__':
    if len(sys.argv)>1:
        print "Will look for file %s" % sys.argv[1]
        app = WrapperGenerator(sys.argv[1])
    else:
        app = WrapperGenerator("test.h")
    app.read()
    app.write_c_wrapper()
    app.write_python_wrapper()
    print app
   
# End of file        
