#!/usr/bin/env python
""" Model IO
    Class that saves and loads composite models from files
    The parameters of the models are not set. The loaded
    model object will have the default parameters for all
    sub-models.

    @author: Mathieu Doucet / UTK
    @contact: mathieu.doucet@nist.gov
"""

import sys

class ModelIO:
    """ Class to create composite models from file or save a model """
    
    def __init__(self, factory):
        """ Initizalization 
            @param factory: ModelFactory object
        """
        
        ## Factory used to create the right type of component
        self.factory = factory
    
    def modelToXML(self, model):
        """ Saves XML representation of the component
            @param model: model to save
            @param file: name of file to write to (if None, a string is returned)
        """

        try:
            # Type
            
            repr = "<Component class='%s' name='%s'>\n" \
                % (model.__class__.__name__, model.name)
            
            # Parameters 
            
            #for p in model.params:
            #    repr += "  <Param name='%s'>\n" % p
            #    par_type = ''
            #    try:
            #        type_tok = str(type(model.params[p])).split("\'")
            #        if len(type_tok)>2:
            #            par_type = type_tok[1]
            #    except:
            #        print sys.exc_value
            #    repr += "    <Type>%s</Type>\n" % par_type
            #    repr += "    <Value>%s</Value>\n" % model.params[p]
            #    repr += "  </Param>"
        
            # Operation parameters
            if model.__class__.__name__ in ['AddComponent', 'SubComponent', 
                                            'MulComponent', 'DivComponent']:
                repr += "  <operateOn>\n"
                repr += "    %s" % self.modelToXML(model.operateOn)
                repr += "  </operateOn>\n"
                
            if model.__class__.__name__ == "AddComponent":
                repr += "  <toAdd>\n"
                repr += "    %s" % self.modelToXML(model.other)
                repr += "  </toAdd>\n"
                
            if model.__class__.__name__ == "SubComponent":
                repr += "  <toSub>\n"
                repr += "    %s" % self.modelToXML(model.other)
                repr += "  </toSub>\n"
                    
            if model.__class__.__name__ == "MulComponent":
                repr += "  <toMul>\n"
                repr += "    %s" % self.modelToXML(model.other)
                repr += "  </toMul>\n"
                
            if model.__class__.__name__ == "DivComponent":
                repr += "  <toDiv>\n"
                repr += "    %s" % self.modelToXML(model.other)
                repr += "  </toDiv>\n"
                
            repr += "</Component>\n"
        except:
            text_out = "ModelIO.save: Error occured while reading info\n  %s" \
                % sys.exc_value
            raise ValueError, text_out
        
        # Return the XML representation of the model
        return repr
        
    def save(self, model, filename):
        """ Save the XML representation of a model to a file
            @param model: XML representation of the model
            @param filename: the path of the file to write to
            @return: True if everything went well
        """
        file_obj = open(filename,'w')
        file_obj.write(self.modelToXML(model))
        file_obj.close()
        return True
    
    def load(self, filename):
        """ Load a model from a file
            @param file: file to load
            @return: a new BaseComponent
        """
        # Recurse through XML tree
        from xml.dom.minidom import parse
        dom = parse(filename)
        
        # Look for Component nodes
        return self.lookupComponentNodes(dom)
        
             
    def lookupComponentNodes(self, node):  
        """ Look up a component node among the children of a node 
            @param node: the minidom node to investigate
            @return: the model object described by the component node, None otherwise
        """
        # Look for Component nodes
        if node.hasChildNodes():
            for n in node.childNodes:
                if n.nodeName == "Component":
                    name = None
                    type = None
                    if n.hasAttributes():
                        # Get the class name & name attribute of the object
                        for i in range(len(n.attributes)):
                            attr_name = n.attributes.item(i).name
                            if attr_name == "class":
                                type = n.attributes.item(i).nodeValue
                            elif attr_name == "name":
                                name = n.attributes.item(i).nodeValue
                            
                    # Check that all the information is there
                    if name == None or type == None:
                        raise ValueError, \
                        "Incomplete model description: missing name or class"
                    else:
                        # Create an object of the type found
                        model_object = self.factory.getModel(type)
                    
                        # Process other nodes that might be attached 
                        # to this model
                        self.processComponentNode(n, model_object)
                        
                        # Return the object instantiated from the 
                        # first node found
                        return model_object
                    
        return None
                    
        
    def processComponentNode(self, node, model):
        """ Process an XML 'Component' node in a model file 
            @param node: XML minidom node to process
            @param model: model object to build from
        """
        if node.hasChildNodes():
            for n in node.childNodes:
                if n.nodeName == "operateOn":
                    model.operateOn = self.lookupComponentNodes(n)
                elif n.nodeName == "toAdd":
                    model.other = self.lookupComponentNodes(n)
                elif n.nodeName == "toSub":
                    model.other = self.lookupComponentNodes(n)
                elif n.nodeName == "toMul":
                    model.other = self.lookupComponentNodes(n)
                elif n.nodeName == "toDiv":
                    model.other = self.lookupComponentNodes(n)       

# main
if __name__ == '__main__':
    from ModelFactory import ModelFactory
    fac = ModelFactory()
    cyl = fac.getModel('CylinderModel')
    sph = fac.getModel('SphereModel')
    c = cyl+sph
    io = ModelIO(fac)
    io.save(c,"myModel.xml")
    value = c.run(1)
    print "%s: f(1) = %g" % (c.name, value)
    loaded = io.load("myModel.xml")
    #print io.modelToXML(loaded)    
    value2 = loaded.run(1)
    print "%s: f(1) = %g" % (c.name, value2)
    if not value == value2:
        print "AN ERROR OCCURED"
      
# End of file