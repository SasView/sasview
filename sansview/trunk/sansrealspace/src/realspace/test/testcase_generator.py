"""
    Random test-case generator for Real-space simulation
    
    @copyright: University of Tennessee, 2007
    @license: This software is provided as part of the DANSE project.
"""
import time

class Stimulus:
    """Base class for simuli objects"""
    
    frequency = 1.0
    
    def __init__(self):
        """Initialization"""
        name = self.__class__.__name__
        pos = name.index('Stimulus')        
        self.name = name[0:pos]
        
    def __call__(self, obj):
        """
            Stimulus application
            @param obj: object to apply the stimulus to
            @return: the modified object and the StimulusReport object
        """
        return obj, None
    

class StimulusReport:
    """Report on the application of a stimulus"""
    def __init__(self, tag=''):
        """   
            Initialization
            @param tag: name of the applied stimulus
        """
        self.tag = tag
        self.applied = 1
        self.passed  = 0
        self.trace = ''
        self.log = ''
        
    def __str__(self):
        """Returns a string with the success rate"""
        return str(self.passed/self.applied)
    
    def __add__(self, other):
        """Adds two reports"""
        self.applied += other.applied
        self.passed  += other.passed
        if len(other.trace)>0:
            self.trace = self.trace+'\n'+other.trace
        if len(other.log)>0:
            self.log = self.log+'\n'+other.log
        return self

    def isPassed(self):
        """Returns true if report is a success"""
        if self.applied == self.passed:
            return True
        return False


class ReportCard: # pylint: disable-msg=R0902
    """ Class to hold test-case results """
    
    def __init__(self):
        """ Initialization """
        ## Number of test cases
        self.n_cases = 0
        ## Number of passed test cases
        self.n_cases_pass = 0
        
        ## Dictionary of stimuli
        self.stimuli = {}
        
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
        if other.__class__.__name__=='ReportCard':
            # Adding two test-case report cards
            self.n_cases += other.n_cases
            self.n_cases_pass += other.n_cases_pass
            
            for tag in other.stimuli:
                if tag in self.stimuli:
                    self.stimuli[tag] += other.stimuli[tag]
                else:
                    self.stimuli[tag] = other.stimuli[tag]
                    
            if len(other.log)>0:
                self.log += other.log
            if len(other.trace)>0:
                self.trace += other.trace
                
            if not other.model in self.modelList:
                self.modelList.append(other.model)
            
        elif other.__class__.__name__ == 'StimulusReport':
            # Adding a stimulus report to the report card
            if other.tag in self.stimuli:
                self.stimuli[other.tag] += other
            else:
                self.stimuli[other.tag] = other
                    
        else:
            raise ValueError, \
            "ReportCard: Unrecognized class %s" % other.__class__.__name__
        return self
        
    def isPassed(self):
        """ Returns true if no error was found """
        if self.n_cases_pass < self.n_cases:
            return False
        return True
        
    def __str__(self):
        """ String representation of the report card """
        from sans.models.ModelFactory import ModelFactory
        
        log = ''
        
        rep = "Detailed output:\n"
        rep += self.log
        rep += "\n"
        rep += "Total number of cases: %g\n" % self.n_cases
        rep += "   Passed:             %g\n" % self.n_cases_pass
        rep += "\n"
        self.modelList.sort()
        rep += "Models tested: %s\n" % self.modelList
        rep += "\n"
        rep += "\n"
        rep += "Breakdown:\n"
        
        for tag in self.stimuli:
            
            rep += "   %-10s:          %g / %g\n" % (tag, self.stimuli[tag].passed, self.stimuli[tag].applied)
            log += self.stimuli[tag].log
        
        rep += '\n'+log
        return rep
    
        

class TestCaseGenerator:
    """ Generator for suite of test-cases
    """
    
    def __init__(self, stimuli):
        """ Initialization
        """
        self.stimuli = stimuli
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
            t = TestCase(self.stimuli, text = textcase)
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
        
        # Reset stimuli object
        self.stimuli.reset()
        #t = TestCase()
        text = "<?xml version=\"1.0\"?>\n"
        text  += "<TestCase>\n"
        loop = True
        while loop:
            
            stimulus = self.stimuli.getRandomStimulus()
            if stimulus == None:
                loop = False
            else:   
                text += "  <Stimulus id=\"%s\"/>\n" % stimulus
        text += "</TestCase>"
        
        return text
    
        
class TestCase:
    """ Test-case class """
    
    def __init__(self, stimuliObject, filename = None, text = None):
        """ Initialization
            @param filename: name of file containing the test case
        """
        self.filename = filename
        self.text = text
        self.stimuli = stimuliObject
        self.model = stimuliObject.setup()
        self.passed = True
        self.reportCard = ReportCard()
        
    
    def run(self):
        """ Read the test case and execute it """
        from xml.dom.minidom import parse
        from xml.dom.minidom import parseString
        
        # Initialize report
        self.reportCard = ReportCard()
        self.reportCard.model = "Canvas"
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
                    if hasattr(self.stimuli,"%sStimulus" % s_type):
                        stimulus = getattr(self.stimuli,"%sStimulus" % s_type)()
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
            print report.trace
        return self.passed
        
 