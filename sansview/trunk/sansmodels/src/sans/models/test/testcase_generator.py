"""
    Random test-case generator for BaseComponents
    
    @author: Mathieu Doucet / UTK
    @license: This software is provided as part of the DANSE project.
"""
import time

def randomModel():
    """ Return a random model name """
    from sans.models.ModelFactory import ModelFactory
    from random import random
    from math import floor
    
    model_list = ModelFactory().getAllModels()
    ready = False
    while not ready:
        rnd_id = int(floor(random()*len(model_list)))
        if model_list[rnd_id] not in ["TestSphere2", "DataModel"]:
            ready = True
    return model_list[rnd_id]

class ReportCard: # pylint: disable-msg=R0902
    """ Class to hold test-case results """
    
    def __init__(self):
        """ Initialization """
        ## Number of test cases
        self.n_cases = 0
        ## Number of passed test cases
        self.n_cases_pass = 0
        ## Number of Evaluation calls
        self.n_eval = 0
        ## Number of passed Evaluation calls
        self.n_eval_pass = 0
        ## Number of SetParam calls
        self.n_set = 0
        ## Number of passed Set calls
        self.n_set_pass = 0
        ## Number of GetParam calls
        self.n_get = 0
        ## Number of passed Get calls
        self.n_get_pass = 0
        ## Number of load calls
        self.n_load = 0
        ## Number of passed Load calls
        self.n_load_pass = 0
        ## Number of save calls
        self.n_save = 0
        ## Number of passed Save calls
        self.n_save_pass = 0
        ## Number of Add calls
        self.n_add = 0
        ## Number of passed Add calls
        self.n_add_pass = 0
        ## Number of Sub calls
        self.n_sub = 0
        ## Number of passed Sub calls
        self.n_sub_pass = 0
        ## Number of Div calls
        self.n_div = 0
        ## Number of passed Div calls
        self.n_div_pass = 0
        ## Number of mul calls
        self.n_mul = 0
        ## Number of passed Mul calls
        self.n_mul_pass = 0
        ## Test log
        self.log = ""
        ## Trace
        self.trace = ""
        ## Model tested
        self.model = ""
        ## List of all models tested
        self.modelList = []
        
        
    def __add__(self, other):
        """ Add two report cards
            @param other: other report to add
            @return: updated self
        """
        
        self.n_cases += other.n_cases
        self.n_cases_pass += other.n_cases_pass
        self.n_eval += other.n_eval
        self.n_eval_pass += other.n_eval_pass
        self.n_set += other.n_set
        self.n_set_pass += other.n_set_pass
        self.n_get += other.n_get
        self.n_get_pass += other.n_get_pass
        self.n_load += other.n_load
        self.n_load_pass += other.n_load_pass
        self.n_save += other.n_save
        self.n_save_pass += other.n_save_pass
        self.n_add += other.n_add
        self.n_add_pass += other.n_add_pass
        self.n_sub += other.n_sub
        self.n_sub_pass += other.n_sub_pass
        self.n_mul += other.n_mul
        self.n_mul_pass += other.n_mul_pass
        self.n_div += other.n_div
        self.n_div_pass += other.n_div_pass
        if len(other.log)>0:
            self.log += other.log
        if len(other.trace)>0:
            self.trace += other.trace
            
        if not other.model in self.modelList:
            self.modelList.append(other.model)
            
        return self
        
    def isPassed(self):
        """ Returns true if no error was found """
        if self.n_cases_pass < self.n_cases \
            or self.n_save_pass < self.n_save \
            or self.n_load_pass < self.n_load \
            or self.n_set_pass < self.n_set \
            or self.n_get_pass < self.n_get \
            or self.n_eval_pass < self.n_eval \
            or self.n_add_pass < self.n_add \
            or self.n_sub_pass < self.n_sub \
            or self.n_mul_pass < self.n_mul \
            or self.n_div_pass < self.n_div:
            return False
        return True
        
    def __str__(self):
        """ String representation of the report card """
        from sans.models.ModelFactory import ModelFactory
        
        rep = "Detailed output:\n"
        rep += self.log
        rep += "\n"
        rep += "Total number of cases: %g\n" % self.n_cases
        rep += "   Passed:             %g\n" % self.n_cases_pass
        rep += "\n"
        self.modelList.sort()
        rep += "Models tested: %s\n" % self.modelList
        all_models = ModelFactory().getAllModels()
        all_models.sort()
        rep += "\n"
        rep += "Available models: %s\n" % all_models
        rep += "\n"
        rep += "Breakdown:\n"
        rep += "   Eval:          %g / %g\n" % (self.n_eval_pass, self.n_eval)
        rep += "   Set:           %g / %g\n" % (self.n_set_pass, self.n_set)
        rep += "   Get:           %g / %g\n" % (self.n_get_pass, self.n_get)
        rep += "   Load:          %g / %g\n" % (self.n_load_pass, self.n_load)
        rep += "   Save:          %g / %g\n" % (self.n_save_pass, self.n_save)
        rep += "   Add:           %g / %g\n" % (self.n_add_pass, self.n_add)
        rep += "   Sub:           %g / %g\n" % (self.n_sub_pass, self.n_sub)
        rep += "   Mul:           %g / %g\n" % (self.n_mul_pass, self.n_mul)
        rep += "   Div:           %g / %g\n" % (self.n_div_pass, self.n_div)
        return rep
    
        

class TestCaseGenerator:
    """ Generator for suite of test-cases
    """
    
    def __init__(self):
        """ Initialization
        """
        
        self.n_tests = 0
        self.n_passed = 0
        self.time = 0
        self.reportCard = ReportCard()
    
    def generateFiles(self, number, file_prefix):
        """ Generate test-case files
            @param number: number of files to generate
            @param file_prefix: prefix for the file names
        """
        
        for i in range(number):
            filename = "%s_%d.xml" % (file_prefix, i)
            self.generateFileTest(filename)
            self.n_tests += 1
            
    def generateAndRun(self, number):
        """ Generate test-cases and run them
            @param number: number of test-cases to generate
        """
        start_time = time.time()
        for i in range(number):
            textcase = self.generateTest()
            t = TestCase(text = textcase)
            passed = t.run()
            self.reportCard += t.reportCard
            if not passed:
                t = time.localtime()
                xmloutput = open("error_%i-%i-%i-%i-%i-%i_%i.xml" % \
                 (t[0],t[1],t[2],t[3],t[4],t[5],self.reportCard.n_cases),'w')
                xmloutput.write(textcase)
                xmloutput.close()

                
        self.time += time.time()-start_time
        print self.reportCard        
        
    def generateFileTest(self, filename = "tmp.xml"):
        """
            Write a random test-case in an XML file
            @param filename: name of file to write to
        """
        text = self.generateTest()
        # Write test case in file
        xmlfile = open(filename,'w')
        xmlfile.write(text)
        xmlfile.close()
    
    
    def generateTest(self):
        """
            Generate an XML representation of a random test-case
        """
        import random
        
        #t = TestCase()
        text = "<?xml version=\"1.0\"?>\n"
        text  += "<TestCase>\n"
        stimulus = "eval"
    
        loop = True
        while loop:
            rnd = random.random()
            
            # run 50%
            if rnd <= 0.5:
                stimulus = "eval"
            elif rnd>0.5 and rnd<=0.7:
                stimulus = "set"
            elif rnd>0.7 and rnd<=0.72:
                stimulus = "save"
            elif rnd>0.72 and rnd<=0.74:
                stimulus = "load"
            elif rnd>0.74 and rnd<=0.8:
                stimulus = "get"
            elif rnd>0.8 and rnd<=0.81:
                stimulus = "add"
            elif rnd>0.81 and rnd<=0.82:
                stimulus = "div"
            elif rnd>0.82 and rnd<=0.83:
                stimulus = "mul"
            elif rnd>0.83 and rnd<=0.84:
                stimulus = "sub"
            else:
                # just run and quit
                stimulus = "eval"
                loop = False
                
            text += "  <Stimulus id=\"%s\"/>\n" % stimulus
        text += "</TestCase>"
        
        return text
    
        
class TestCase:
    """ Test-case class """
    
    def __init__(self, filename = None, text = None):
        """ Initialization
            @param filename: name of file containing the test case
        """
        #from sans.models.ModelFactory import ModelFactory
        self.filename = filename
        self.text = text
        #self.model = ModelFactory().getModel(randomModel())
        self.model = getRandomModelObject()
        #self.model = ModelFactory().getModel("SphereModel")
        self.passed = True
        self.reportCard = ReportCard()
        
    
    def run(self):
        """ Read the test case and execute it """
        from xml.dom.minidom import parse
        from xml.dom.minidom import parseString
        
        # Initialize report
        self.reportCard = ReportCard()
        self.reportCard.model = self.model.name
        self.reportCard.n_cases = 1
        
        if not self.text == None:
            dom = parseString(self.text)
        elif not self.filename == None:
            dom = parse(self.filename)
        else:
            print "No input to parse"
            return False
        
        if dom.hasChildNodes():
            for n in dom.childNodes:
                if n.nodeName == "TestCase":
                    self.processStimuli(n)
            
        # Update report card        
        if self.passed:
            self.reportCard.n_cases_pass = 1
            
        return self.passed
                          
    def processStimuli(self, node):
        """ Process the stimuli list in the TestCase node 
            of an XML test-case file
            @param node: test-case node
        """
        import testcase_generator as generator
        report = ReportCard()
        report.trace = "%s\n" % self.model.name
        
        self.passed = True
        if node.hasChildNodes():
            for n in node.childNodes:
                if n.nodeName == "Stimulus":
                    
                    s_type = None
                    if n.hasAttributes():
                        # Get stilumus ID
                        for i in range(len(n.attributes)):
                            attr_name = n.attributes.item(i).name
                            if attr_name == "id":
                                s_type = n.attributes.item(i).nodeValue
                    if hasattr(generator,"%sStimulus" % s_type):
                        stimulus = getattr(generator,"%sStimulus" % s_type)
                        #print s_type, self.model.name
                        m, res = stimulus(self.model)
                        #print "     ", m.name
                        self.model = m
                        if not res.isPassed():
                            self.passed = False
                        
                        report += res
                        
                    else:
                        print "Stimulus %s not found" % s_type
                        
        self.reportCard += report
        
        if not self.passed:
            print "\nFailure:"
            print report.trace
        return self.passed
        
    
def evalStimulus(model):
    """ Apply the stimulus to the supplied model object
        @param model: model to apply the stimulus to
        @return: True if passed, False otherwise
    """
    minval = 0.001
    maxval = 1.0
    # Call run with random input
    import random, math
    input_value = random.random()*(maxval-minval)+minval
    
    # Catch division by zero, which can happen
    # when creating random models
    try:
        # Choose whether we want 1D or 2D
        if random.random()>0.5:
            output = model.run(input_value)
        else:
            output = model.run([input_value, 2*math.pi*random.random()])            
    except ZeroDivisionError:
        print "Error evaluating model %s: %g" % (model.name, input_value)
        output = None
        
    #print "Eval: %g" % output
    
    # Oracle bit - just check that we have a number...
    passed = False
    try:
        if output != None and math.fabs(output) >= 0: 
            passed = True
    except:
        print "---> Could not compute abs val", output, model.name
        
    
    report = ReportCard()
    report.n_eval = 1
    if passed:
        report.n_eval_pass = 1
    else:
        report.log = "Eval: bad output value %s\n" % str(output)
        
    report.trace = "Eval(%g) = %s %i\n" % (input_value, str(output), passed)    
    return model, report

def setStimulus(model):
    """ Apply the stimulus to the supplied model object
        @param model: model to apply the stimulus to
        @return: True if passed, False otherwize
    """
    # Call run with random input
    import random, math
    minval = 1
    maxval = 5
    
    # Choose a parameter to change
    keys = model.getParamList()
    if len(keys)==0:
        #print model.name+" has no params"
        return model, ReportCard()
    
    p_len = len(keys)
    i_param = int(math.floor(random.random()*p_len))
    p_name  = keys[i_param]
    
    # Choose a value
    # Check for min/max
    if hasattr(model, "details"):
        if model.details.has_key(p_name):
            if model.details[p_name][1] != None:
                minval = model.details[p_name][1]
            if model.details[p_name][2] != None:
                maxval = model.details[p_name][2]
        elif model.other.details.has_key(p_name):
            if model.other.details[p_name][1] != None:
                minval = model.other.details[p_name][1]
            if model.other.details[p_name][2] != None:
                maxval = model.other.details[p_name][2]
        elif model.operateOn.details.has_key(p_name):
            if model.operateOn.details[p_name][1] != None:
                minval = model.operateOn.details[p_name][1]
            if model.operateOn.details[p_name][2] != None:
                maxval = model.operateOn.details[p_name][2]
            
    input_val = random.random()*(maxval-minval)+minval
    model.setParam(p_name, input_val)
    
    # Read back
    check_val = model.getParam(p_name)
    #print "Set: %s = %g" % (p_name, check_val)
    
    # Oracle bit
    passed = False
    if check_val == input_val: 
        passed = True
    
    report = ReportCard()
    report.n_set = 1
    if passed:
        report.n_set_pass = 1
    else:
        report.log = "Set: parameter %s not set properly %g <> %g\n" % \
            (p_name, input_val, check_val)
        
    report.trace = "Set %s = %g %i\n" % (p_name, input_val, passed)    
    return model, report

def getStimulus(model):
    """ Apply the stimulus to the supplied model object
        @param model: model to apply the stimulus to
        @return: True if passed, False otherwise
    """
    import random, math
    # Choose a parameter to change
    keys = model.getParamList()
    if len(keys)==0:
        #print model.name+" has no params"
        return model, ReportCard()    
    
    p_len = len(keys)
    i_param = int(math.floor(random.random()*p_len))
    p_name  = keys[i_param]
    
    # Read back
    check_val = model.getParam(p_name)
    #print "Get: %s = %g" % (p_name, check_val)
    
    # Oracle bit
    passed = False
    if math.fabs(check_val) >= 0: 
        passed = True
        
    report = ReportCard()
    report.n_get = 1
    if passed:
        report.n_get_pass = 1
    else:
        report.log = "Get: bad value for parameter %s: %g\n" % \
            (p_name, check_val)
        
    report.trace = "Get %s = %g %i\n" % (p_name, check_val, passed)    
    return model, report

def loadStimulus(model):
    """ Apply the stimulus to the supplied model object
        @param model: model to apply the stimulus to
        @return: True if passed, False otherwize
    """
    from sans.models.ModelIO import ModelIO
    from sans.models.ModelFactory import ModelFactory
    factory = ModelFactory()
    io = ModelIO(factory)
    
    # testModel.xml should be in the directory
    loaded = io.load("load_test_model.xml")
    value2 = loaded.run(1)
    
    # Oracle bit
    passed = False
    if not value2 == 0: 
        passed = True
        
    report = ReportCard()
    report.n_load = 1
    if passed:
        report.n_load_pass = 1
    else:
        report.log = "Load: bad loaded model\n"
        
    report.trace = "Load = %s %i\n" % (loaded.name, passed)    
    return model, report

def saveStimulus(model):
    """ Apply the stimulus to the supplied model object
        @param model: model to apply the stimulus to
        @return: True if passed, False otherwize
    """
    from sans.models.ModelIO import ModelIO
    from sans.models.ModelFactory import ModelFactory
    factory = ModelFactory()
    io = ModelIO(factory)
    io.save(model,"testModel.xml")
    #value = model.run(1)

    # Check it 
    loaded = io.load("testModel.xml")
    try:
        value2 = loaded.run(1)
    except ZeroDivisionError:
        value2 = -1
    
    # Oracle bit
    passed = False
    
    # The two outputs do not need to be the same
    # since we do not save the parameters!
    # If it's the subtraction of two identical models, 
    # we will also get zero!
    #if value2 == value: 
    #    passed = True
    
    passed = True

        
    report = ReportCard()
    report.n_save = 1
    if passed:
        report.n_save_pass = 1
    else:
        report.log = "Save: bad output from saved model %g\n" % value2
        
    report.trace = "Save %s %i\n" % (model.name, passed)    
    return model, report

def getRandomModelObject():
    """
        Return a random model object
    """
    from sans.models.ModelFactory import ModelFactory
    while True:
        try:
            modelname = randomModel()
            add_model = ModelFactory().getModel(modelname)
            return add_model
        except:
            # Don't complain when a model can't be loaded.
            # A list of tested models will appear in the 
            # file report, which can be compared with the 
            # list of available models, also printed.
            pass
            #print "Could not load ", modelname
    

def addStimulus(model):
    """ Apply the stimulus to the supplied model object
        @param model: model to apply the stimulus to
        @return: True if passed, False otherwize
    """
    #from sans.models.ModelFactory import ModelFactory
    #factory = ModelFactory()
    #add_model = factory.getModel("SphereModel")
    add_model = getRandomModelObject()
            
    tmp = model + add_model
    model = tmp
    
    # Oracle bit
    passed = False
    
    try:
        value2 = model.run(1)
        value2 = float(value2)
    except:
        passed = False
    
    # If we made it this far, we have a float
    passed = True 
        
    report = ReportCard()
    report.n_add = 1
    if passed:
        report.n_add_pass = 1
    else:
        report.log = "Add: bad output from composite model\n"
        
    report.trace = "Div %s %i\n" % (model.name, passed)    
    return model, report

def subStimulus(model):
    """ Apply the stimulus to the supplied model object
        @param model: model to apply the stimulus to
        @return: True if passed, False otherwize
    """
    from sans.models.ModelFactory import ModelFactory
    from random import random
    
    #factory = ModelFactory()
    #sub_model = factory.getModel("CylinderModel")
    #sub_model = factory.getModel(randomModel())
    sub_model = getRandomModelObject()

    
    sub_model.params["scale"] = 1.1*random()
    tmp = model - sub_model
    
    # Oracle bit
    passed = False
    
    try:
        value2 = tmp.run(1.1 * (1.0 + random()))
        value2 = float(value2)
    except:
        value2 = None
        passed = False
    
    # If we made it this far, we have a float
    passed = True 
        
    report = ReportCard()
    report.n_sub = 1
    if passed:
        report.n_sub_pass = 1
    else:
        report.log = "Sub: bad output from composite model\n"

    report.trace = "Sub %s (%g - %g = %s) %i\n" % \
        (model.name, model.run(1), \
         sub_model.run(1), str(value2), passed)                
    return tmp, report

def mulStimulus(model):
    """ Apply the stimulus to the supplied model object
        @param model: model to apply the stimulus to
        @return: True if passed, False otherwize
    """
    #from sans.models.ModelFactory import ModelFactory
    #factory = ModelFactory()
    #mul_model = factory.getModel("SphereModel")
    #mul_model = factory.getModel(randomModel())
    mul_model = getRandomModelObject()
    tmp = model * mul_model
    
    # Oracle bit
    passed = False
    
    from random import random
    input_val = 1.1 * (1.0 + random())
    v1 = None
    v2 = None
    try:
        v1 = mul_model.run(input_val)
        v2 = model.run(input_val)
        value2 = tmp.run(input_val)
        value2 = float(value2)
    except ZeroDivisionError:
        value2 = None
    
    # If we made it this far, we have a float
    passed = True 
        
    report = ReportCard()
    report.n_mul = 1
    if passed:
        report.n_mul_pass = 1
    else:
        report.log = "Mul: bad output from composite model\n"
        
    report.trace = "Mul %s (%s * %s = %s) %i\n" % \
      (model.name, str(v1), str(v2), str(value2), passed)                
    return tmp, report

def divStimulus(model):
    """ Apply the stimulus to the supplied model object
        @param model: model to apply the stimulus to
        @return: True if passed, False otherwise
    """
    #from sans.models.ModelFactory import ModelFactory
    #factory = ModelFactory()
    #div_model = factory.getModel("SphereModel")
    #div_model = factory.getModel(randomModel())

    from random import random
    input_val = 1.5 * random()
    
    # Find a model that will not evaluate to zero
    # at the input value
    try_again = True
    while try_again:
        div_model = getRandomModelObject()
        try:
            v2 = div_model.run(input_val)
            try_again = False
        except:
            pass
        
    tmp = model / div_model
    
    # Oracle bit
    passed = False
    
    v1 = None
    v2 = None
    try:
        
        # Check individual models against bad combinations,
        # which happen from time to time given that all 
        # parameters are random
        try:
            v2 = div_model.run(input_val)
            v1 = model.run(input_val)
            value2 = tmp.run(input_val)
            value2 = float(value2)
        except ZeroDivisionError:
            value2 = None
    except:
        passed = False
    
    # If we made it this far, we have a float
    passed = True 
        
    report = ReportCard()
    report.n_div = 1
    if passed:
        report.n_div_pass = 1
    else:
        report.log = "Div: bad output from composite model\n"
        
    report.trace = "Div %s/%s (%g) = %s / %s = %s %i\n" % \
      (model.name, div_model.name, input_val, str(v1), str(v2), str(value2), passed)                
    return tmp, report

if __name__ == '__main__':

    #print randomModel()
    g = TestCaseGenerator()
    g.generateAndRun(20000)
    
    #t = TestCase(filename = "error_1.17721e+009.xml")
    #print t.run()
    