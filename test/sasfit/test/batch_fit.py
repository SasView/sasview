import copy
import time
import unittest
from sas.dataloader.loader import Loader
from sas.fit.Fitting import Fit
from sas.models.CylinderModel import CylinderModel
import sas.models.dispersion_models 
from sas.models.qsmearing import smear_selection

NPTS = 1


def classMapper(classInstance, classFunc, *args):
    """
    Take an instance of a class and a function name as a string.
    Execute class.function and return result
    """
    return  getattr(classInstance,classFunc)(*args)

def mapapply(arguments):
    return apply(arguments[0], arguments[1:])


class BatchFit:
    """
    test fit module
    """
    def __init__(self, qmin=None, qmax=None):
        """ """
        self.list_of_fitter = []
        self.list_of_function = []
        self.param_to_fit = ['scale', 'length', 'radius']
        self.list_of_constraints = []
        self.list_of_mapper = []
        self.polydisp = sas.models.dispersion_models.models
        self.qmin = qmin
        self.qmax = qmin
        self.reset_value()
        
    def set_range(self, qmin=None, qmax=None):  
        self.qmin = qmin
        self.qmax = qmax
        
    def _reset_helper(self, path=None, engine="bumps", npts=NPTS):
        """
        Set value to fitter engine and prepare inputs for map function
        """
        for i in range(npts):
            data = Loader().load(path)
            fitter = Fit(engine)
            #create model
            model = CylinderModel()
            model.setParam('scale', 1.0)
            model.setParam('radius', 20.0)
            model.setParam('length', 400.0)
            model.setParam('sldCyl', 4e-006)
            model.setParam('sldSolv', 1e-006)
            model.setParam('background', 0.0)
            for param in model.dispersion.keys():
                model.set_dispersion(param, self.polydisp['gaussian']())
            model.setParam('cyl_phi.width', 10)
            model.setParam('cyl_phi.npts', 3)
            model.setParam('cyl_theta.nsigmas', 10)
            # for 2 data cyl_theta = 60.0 [deg] cyl_phi= 60.0 [deg]
            fitter.set_model(model, i, self.param_to_fit, 
                             self.list_of_constraints)
            #smear data
            current_smearer = smear_selection(data, model)
            import cPickle
            p = cPickle.dumps(current_smearer)
            sm = cPickle.loads(p)
            fitter.set_data(data=data, id=i,
                             smearer=current_smearer, qmin=self.qmin, qmax=self.qmax)
            fitter.select_problem_for_fit(id=i, value=1)
            self.list_of_fitter.append(copy.deepcopy(fitter))
            self.list_of_function.append('fit')
            self.list_of_mapper.append(classMapper)
                   
    def reset_value(self, engine='bumps'):
        """
        Initialize inputs for the map function
        """
        self.list_of_fitter = []
        self.list_of_function = []
        self.param_to_fit = ['scale', 'length', 'radius']
        self.list_of_constraints = []
        self.list_of_mapper = []

        path = "testdata_line3.txt"
        self._reset_helper(path=path, engine=engine, npts=NPTS)
        path = "testdata_line.txt"
        self._reset_helper(path=path, engine=engine, npts=NPTS)
        path = "SILIC010_noheader.DAT"
        self._reset_helper(path=path, engine=engine, npts=NPTS)
        path = "cyl_400_20.txt"
        self._reset_helper(path=path, engine=engine, npts=NPTS)
        path = "sphere_80.txt"
        self._reset_helper(path=path, engine=engine, npts=NPTS)
        path = "PolySpheres.txt"
        self._reset_helper(path=path, engine=engine, npts=NPTS)
        path = "latex_qdev.txt"
        self._reset_helper(path=path, engine=engine, npts=NPTS)
        path = "latex_qdev2.txt"
        self._reset_helper(path=path, engine=engine, npts=NPTS)
        
      
    def test_map_fit(self, n=0):
        """
        """
        if n > 0:
            self._test_process_map_fit(n=n)
        else:
            results =  map(classMapper,self.list_of_fitter, self.list_of_function)
            print len(results)
            for result in results:
                print result.fitness, result.stderr, result.pvec
        
    def test_process_map_fit(self, n=1):
        """
        run fit usong map , n is the number of processes used
        """ 
        t0 = time.time()
        print "start fit with %s process(es) at %s" % (str(n), time.strftime(" %H:%M:%S", time.localtime(t0)))
        from multiprocessing import Pool
        temp = zip(self.list_of_mapper, self.list_of_fitter, self.list_of_function)
        results =  Pool(n).map(func=mapapply, 
                               iterable=temp)
        t1 = time.time()
        print "got fit results ", time.strftime(" %H:%M:%S", time.localtime(t1)), t1 - t0
        print len(results)
        for result in results:
            print result.fitness, result.stderr, result.pvec
        t2 = time.time()
        print "print fit1 results ", time.strftime(" %H:%M:%S", time.localtime(t2)), t2 - t1   
                
class testBatch(unittest.TestCase):
    """
    fitting
    """  
    def setUp(self):
        self.test = BatchFit(qmin=None, qmax=None)
       
    
    def test_fit1(self):
        """test fit with python built in map function---- full range of each data"""
        self.test.test_map_fit()
        
    def test_fit2(self):
        """test fit with python built in map function---- common range for all data"""
        self.test.set_range(qmin=0.013, qmax=0.05)
        self.test.reset_value()
        self.test.test_map_fit()
        raise Exception("fail")
        
    def test_fit3(self):
        """test fit with data full range using 1 processor and map"""
        self.test.set_range(qmin=None, qmax=None)
        self.test.reset_value()
        self.test.test_map_fit(n=1)
        
    def test_fit4(self):
        """test fit with a common fixed range for data using 1 processor and map"""
        self.test.set_range(qmin=-1, qmax=10)
        self.test.reset_value()
        self.test.test_map_fit(n=3)
        
            
if __name__ == '__main__':
   unittest.main()
    
    
    
