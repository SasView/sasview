#!/usr/bin/env python
""" Model factory
    Class that creates models by looking up the name of a model
    in the models directory

    @author: Mathieu Doucet / UTK
    @contact: mathieu.doucet@nist.gov
"""

import os
import imp

# info
__author__ = "Mathieu Doucet"   

class ModelFactory: #pylint: disable-msg=W0232
    """ Class to create available models """

    def getModel(self, name="BaseComponent"): #pylint: disable-msg=R0201
        """ Returns the model if found 
            @param name: name of the model to look for
            @return: the model object
        """
         
        # Look up the files in the model directory
         
        # Find correct directory first...
        path = os.path.dirname(__file__)
        if(os.path.isfile("%s/%s.py" % (path, name))):
            fObj, path, descr = imp.find_module(name, [path])
            modObj = imp.load_module(name, fObj, path, descr)
            if hasattr(modObj, name):
                return getattr(modObj, name)()
        else:
            raise ValueError, "Could not find module file"
            
        raise ValueError, "Could not find module %s" % name
      
    def getAllModels(self): #pylint: disable-msg=R0201
        """ Returns a list of all available models 
            @return: python list object
        """
        
        # from AbstractModel import AbstractModel
        # Find correct directory first...
        path = os.path.dirname(__file__)
        filelist = os.listdir(path)
        internal_components = ["BaseComponent", "AddComponent",
                "SubComponent", "DivComponent", "MulComponent",
                "DisperseModel", "ModelFactory", "ModelIO"]
    
        funclist = []
        for filename in filelist:
            toks = filename.split('.')
            # Look for exceptions... 
            # TODO: These should be in another directory
            if len(toks)==2 and toks[0].count('__')==0 and toks[1]=='py' \
                and not toks[0] in internal_components:
                funclist.append(toks[0])
     
        return funclist
             
# main
if __name__ == '__main__':
    print ModelFactory().getAllModels()
    app = ModelFactory().getModel('CylinderModel')
    print "%s: f(45) = %g" % (app.name, app.run(1))
         
# End of file