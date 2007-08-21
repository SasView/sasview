"""Automated testing for simulation

    To be compatible with testcase_generator, a simulus
    class must have:
        setup(self):  to initialize the test-case
        getRandomStimulus(self): to get a random stimulus name
        stimuli that inherit from the Stimulus class
        
    @copyright: University of Tennessee, 2007
    @license: This software is provided as part of the DANSE project.

"""

import testcase_generator as generator
from testcase_generator import Stimulus
try:
    import VolumeCanvas
    print "Testing local VolumeCanvas\n"
except:
    import sans.realspace.VolumeCanvas as VolumeCanvas

def randomModel():
    """ Return a random model name """
    from random import random
    from math import floor
    
    model_list = ['sphere', 'cylinder', 'ellipsoid', 'singlehelix']
    rnd_id = int(floor(random()*len(model_list)))
    
    return model_list[rnd_id]


class Simulation:
    """Simulation testing class"""
    
    # Probability of stopping a test case without
    # adding additional stimuli
    end_frequency = 0.1
    
    def __init__(self):
        self.end_flag = False
        
    def reset(self):
        self.end_flag = False
    
    def setup(self):
        """Setup the canvas for stimuli application"""
        return VolumeCanvas.VolumeCanvas()
    
    def getRandomStimulus(self):
        """Return the name of a random stimulus"""
        
        from random import random
        
        # If the end flag is up, compute I(q) one last time
        if self.end_flag == True:
            return None
        
        # Get the list of stimuli
        attrs = dir(self)
        stim_list = []
        
        # Get the list of simuli and 
        # compute the total normalization
        sum = 0
        for item in attrs:
            if item.endswith('Stimulus'):
                obj = getattr(self, item)
                if hasattr(obj, 'frequency'):
                    stim_list.append(item)
                    sum += getattr(self, item).frequency
        
        # Choose a stimulus
        rnd = random()
        
        # Check if we need to stop
        if rnd < self.end_frequency:
            self.end_flag = True
            return "GetIq"
        
        run_sum = 0
        for item in stim_list:
            run_sum += getattr(self, item).frequency/sum 
            if run_sum >= rnd:
                pos = item.index('Stimulus')
                
                return item[0:pos]
        
    class AddStimulus(Stimulus):
        """Add an object to the canvas"""

        frequency = 1.0
        
        def __call__(self, canvas):
            """Apply stimulus"""
            report = generator.StimulusReport(tag=self.name)
        
            # Select random model
            add_model = randomModel()

            # Add the model
            handle = canvas.add(add_model)
            
            # Check that it is in the list of objects
            if handle in canvas.getShapeList():
                report.passed = 1
            else:
                report.log = "Add: tried to add %s" % add_model
            
            report.trace = "Added %s" % add_model
            
            return canvas, report
    
    class GetParamStimulus(Stimulus):
        """Get the value of a canvas or shape parameter"""

        frequency = 1.0
        
        def __call__(self, canvas):
            """Apply stimulus"""
            from random import random
            import math
            
            report = generator.StimulusReport(tag=self.name)
        
            # Read a parameter
            #TODO: access shape parameters
            rnd = random()
            i_rnd = int(math.floor(rnd*len(canvas.params)))
            par_name = canvas.params.keys()[i_rnd]
            value = canvas.getParam(par_name)
            
            # Check that it is in the list of objects
            try:
                float(value)
                report.passed = 1
            except:
                report.log = "get: bad value for [%s]" % par_name
            
            report.trace = "Read %s" % par_name
            
            return canvas, report
    
    class GetIqStimulus(Stimulus):
        """Calculate I(q)"""

        frequency = 1.0
        
        def __call__(self, canvas):
            report = generator.StimulusReport(tag=self.name)
            
            # Check that a float is returned
            # Validation testing will be done elsewhere
            value = canvas.getIq(0.1)
            
            # Check that it is in the list of objects
            try:
                float(value)
                report.passed = 1
            except:
                report.log = "GetIq: bad value for Iq "+str(value)
            
            report.trace = "I(q) = %g" % value
            return canvas, report
    
    class SetCanvasParamStimulus(Stimulus):
        """Set the value of a canvas parameter"""

        frequency = 1.0
        
        def __call__(self, canvas):
            """Apply stimulus"""
            from random import random
            import math
            
            report = generator.StimulusReport(tag=self.name)
        
            # Read a parameter
            rnd = random()
            i_rnd = int(math.floor(rnd*len(canvas.params)))
            par_name = canvas.params.keys()[i_rnd]
            
            # Get current value
            current = canvas.getParam(par_name)
            
            # Set new value
            rnd2 = random()
            new_value = current*(1.0+rnd2)
            canvas.setParam(par_name, new_value)
            
            # Read it back
            current = canvas.getParam(par_name)
            
            # Check that the new value is correct
            if current == new_value:
                report.passed = 1
            else:
                report.log = "get: bad value for [%s]" % par_name
            
            report.trace = "Read %s" % par_name
            
            return canvas, report
    
    class SetShapeParamStimulus(Stimulus):
        """Set the value of a canvas parameter"""

        frequency = 1.0
        
        def __call__(self, canvas):
            """Apply stimulus"""
            from random import random
            import math
            
            report = generator.StimulusReport(tag=self.name)
        
            # Read a parameter
            rnd = random()
            shape_list = canvas.getShapeList()

            if len(shape_list)==0:
                # No object available, let's test an error condition
                try:
                    canvas.setParam("shape0.test-radius", 1.0)
                    report.log = "SetShapeParam: set didn't throw exception"
                except:
                    report.passed = 1
                report.trace = "SetShapeParam: testing failure behavior"
                
            else:  
                i_rnd = int(math.floor(rnd*len(shape_list)))
                shape_name = shape_list[i_rnd]
                
                found = False
                while found==False:
                    rnd2 = random()
                    par_keys = canvas.shapes[shape_name].params.keys()
                    i_rnd2 = int(math.floor(rnd2*(len(par_keys))))
                    
                    short_name = par_keys[i_rnd2]
                    par_name = "%s.%s" % (shape_name, short_name)
                    if not short_name.lower() == "type":
                        found= True
                
                # Get current value
                current = canvas.getParam(par_name)
                
                # Set new value
                if short_name in ['orientation', 'center']:
                    new_value = [random(), random(), random()]
                else:
                    new_value = current*(1.0+random())

                canvas.setParam(par_name, new_value)
                
                # Read it back
                current = canvas.getParam(par_name)
                
                # Check that the new value is correct
                if current == new_value:
                    report.passed = 1
                else:
                    report.log = "get: bad value for [%s]" % par_name
                
                report.trace = "Read %s" % par_name
            
            return canvas, report
    

    class RemoveStimulus(Stimulus):
        """Calculate I(q)"""

        frequency = 1.0
        
        def __call__(self, canvas):
            from random import random
            import math
            
            report = generator.StimulusReport(tag=self.name)
            
            # Get list of shapes
            if len(canvas.shapes)>0:
                rnd = random()
                i_rnd = int(math.floor(rnd*len(canvas.shapes)))
                shape_name = canvas.shapes.keys()[i_rnd]
                
                canvas.delete(shape_name)
                if shape_name in canvas.shapes.keys() \
                    or shape_name in canvas.getShapeList():
                    report.log = "Remove: object was not removed"
                else:
                    report.passed = 1
                
            else:
                # No shape to remove: test bad remove call
                try:
                    canvas.delete("test-shape")
                    report.log = "Remove: delete didn't throw exception"
                except:
                    report.passed = 1
                report.trace = "Remove: testing failure behavior"
            
            return canvas, report
    


if __name__ == '__main__':
    import sys
    
    stimuli = Simulation()
    
    if len(sys.argv)>1:
        #t = generator.TestCase(stimuli, filename = "test-case.xml")
        t = generator.TestCase(stimuli, filename = sys.argv[1])
        print "Test passed =", t.run() 
    else:   
        g = generator.TestCaseGenerator(stimuli)
        g.generateAndRun(200)
    

    
    
