"""
BumpsFitting module runs the bumps optimizer.
"""
import os
from datetime import timedelta, datetime

import numpy

from bumps import fitters
try:
    from bumps.options import FIT_CONFIG
    # Default bumps to use the Levenberg-Marquardt optimizer
    FIT_CONFIG.selected_id = fitters.LevenbergMarquardtFit.id
    def get_fitter():
        return FIT_CONFIG.selected_fitter, FIT_CONFIG.selected_values
except:
    # CRUFT: Bumps changed its handling of fit options around 0.7.5.6
    # Default bumps to use the Levenberg-Marquardt optimizer
    fitters.FIT_DEFAULT = 'lm'
    def get_fitter():
        fitopts = fitters.FIT_OPTIONS[fitters.FIT_DEFAULT]
        return fitopts.fitclass, fitopts.options.copy()


from bumps.mapper import SerialMapper, MPMapper
from bumps import parameter
from bumps.fitproblem import FitProblem


from sas.fit.AbstractFitEngine import FitEngine
from sas.fit.AbstractFitEngine import FResult
from sas.fit.expression import compile_constraints

class Progress(object):
    def __init__(self, history, max_step, pars, dof):
        remaining_time = int(history.time[0]*(float(max_step)/history.step[0]-1))
        # Depending on the time remaining, either display the expected
        # time of completion, or the amount of time remaining.  Use precision
        # appropriate for the duration.
        if remaining_time >= 1800:
            completion_time = datetime.now() + timedelta(seconds=remaining_time)
            if remaining_time >= 36000:
                time = completion_time.strftime('%Y-%m-%d %H:%M')
            else:
                time = completion_time.strftime('%H:%M')
        else:
            if remaining_time >= 3600:
                time = '%dh %dm'%(remaining_time//3600, (remaining_time%3600)//60)
            elif remaining_time >= 60:
                time = '%dm %ds'%(remaining_time//60, remaining_time%60)
            else:
                time = '%ds'%remaining_time
        chisq = "%.3g"%(2*history.value[0]/dof)
        step = "%d of %d"%(history.step[0], max_step)
        header = "=== Steps: %s  chisq: %s  ETA: %s\n"%(step, chisq, time)
        parameters = ["%15s: %-10.3g%s"%(k,v,("\n" if i%3==2 else " | "))
                      for i,(k,v) in enumerate(zip(pars,history.point[0]))]
        self.msg = "".join([header]+parameters)

    def __str__(self):
        return self.msg


class BumpsMonitor(object):
    def __init__(self, handler, max_step, pars, dof):
        self.handler = handler
        self.max_step = max_step
        self.pars = pars
        self.dof = dof

    def config_history(self, history):
        history.requires(time=1, value=2, point=1, step=1)

    def __call__(self, history):
        if self.handler is None: return
        self.handler.set_result(Progress(history, self.max_step, self.pars, self.dof))
        self.handler.progress(history.step[0], self.max_step)
        if len(history.step)>1 and history.step[1] > history.step[0]:
            self.handler.improvement()
        self.handler.update_fit()

class ConvergenceMonitor(object):
    """
    ConvergenceMonitor contains population summary statistics to show progress
    of the fit.  This is a list [ (best, 0%, 25%, 50%, 75%, 100%) ] or
    just a list [ (best, ) ] if population size is 1.
    """
    def __init__(self):
        self.convergence = []

    def config_history(self, history):
        history.requires(value=1, population_values=1)

    def __call__(self, history):
        best = history.value[0]
        try:
            p = history.population_values[0]
            n,p = len(p), numpy.sort(p)
            QI,Qmid, = int(0.2*n),int(0.5*n)
            self.convergence.append((best, p[0],p[QI],p[Qmid],p[-1-QI],p[-1]))
        except:
            self.convergence.append((best, best,best,best,best,best))


# Note: currently using bumps parameters for each parameter object so that
# a SasFitness can be used directly in bumps with the usual semantics.
# The disadvantage of this technique is that we need to copy every parameter
# back into the model each time the function is evaluated.  We could instead
# define reference parameters for each sas parameter, but then we would not
# be able to express constraints using python expressions in the usual way
# from bumps, and would instead need to use string expressions.
class SasFitness(object):
    """
    Wrap SAS model as a bumps fitness object
    """
    def __init__(self, model, data, fitted=[], constraints={},
                 initial_values=None, **kw):
        self.name = model.name
        self.model = model.model
        self.data = data
        if self.data.smearer is not None:
            self.data.smearer.model = self.model
        self._define_pars()
        self._init_pars(kw)
        if initial_values is not None:
            self._reset_pars(fitted, initial_values)
        self.constraints = dict(constraints)
        self.set_fitted(fitted)
        self.update()

    def _reset_pars(self, names, values):
        for k,v in zip(names, values):
            self._pars[k].value = v

    def _define_pars(self):
        self._pars = {}
        for k in self.model.getParamList():
            name = ".".join((self.name,k))
            value = self.model.getParam(k)
            bounds = self.model.details.get(k,["",None,None])[1:3]
            self._pars[k] = parameter.Parameter(value=value, bounds=bounds,
                                                fixed=True, name=name)
        #print parameter.summarize(self._pars.values())

    def _init_pars(self, kw):
        for k,v in kw.items():
            # dispersion parameters initialized with _field instead of .field
            if k.endswith('_width'): k = k[:-6]+'.width'
            elif k.endswith('_npts'): k = k[:-5]+'.npts'
            elif k.endswith('_nsigmas'): k = k[:-7]+'.nsigmas'
            elif k.endswith('_type'): k = k[:-5]+'.type'
            if k not in self._pars:
                formatted_pars = ", ".join(sorted(self._pars.keys()))
                raise KeyError("invalid parameter %r for %s--use one of: %s"
                               %(k, self.model, formatted_pars))
            if '.' in k and not k.endswith('.width'):
                self.model.setParam(k, v)
            elif isinstance(v, parameter.BaseParameter):
                self._pars[k] = v
            elif isinstance(v, (tuple,list)):
                low, high = v
                self._pars[k].value = (low+high)/2
                self._pars[k].range(low,high)
            else:
                self._pars[k].value = v

    def set_fitted(self, param_list):
        """
        Flag a set of parameters as fitted parameters.
        """
        for k,p in self._pars.items():
            p.fixed = (k not in param_list or k in self.constraints)
        self.fitted_par_names = [k for k in param_list if k not in self.constraints]
        self.computed_par_names = [k for k in param_list if k in self.constraints]
        self.fitted_pars = [self._pars[k] for k in self.fitted_par_names]
        self.computed_pars = [self._pars[k] for k in self.computed_par_names]

    # ===== Fitness interface ====
    def parameters(self):
        return self._pars

    def update(self):
        for k,v in self._pars.items():
            #print "updating",k,v,v.value
            self.model.setParam(k,v.value)
        self._dirty = True

    def _recalculate(self):
        if self._dirty:
            self._residuals, self._theory \
                = self.data.residuals(self.model.evalDistribution)
            self._dirty = False

    def numpoints(self):
        return numpy.sum(self.data.idx) # number of fitted points

    def nllf(self):
        return 0.5*numpy.sum(self.residuals()**2)

    def theory(self):
        self._recalculate()
        return self._theory

    def residuals(self):
        self._recalculate()
        return self._residuals

    # Not implementing the data methods for now:
    #
    #     resynth_data/restore_data/save/plot

class ParameterExpressions(object):
    def __init__(self, models):
        self.models = models
        self._setup()

    def _setup(self):
        exprs = {}
        for M in self.models:
            exprs.update((".".join((M.name, k)), v) for k, v in M.constraints.items())
        if exprs:
            symtab = dict((".".join((M.name, k)), p)
                          for M in self.models
                          for k,p in M.parameters().items())
            self.update = compile_constraints(symtab, exprs)
        else:
            self.update = lambda: 0

    def __call__(self):
        self.update()

    def __getstate__(self):
        return self.models

    def __setstate__(self, state):
        self.models = state
        self._setup()

class BumpsFit(FitEngine):
    """
    Fit a model using bumps.
    """
    def __init__(self):
        """
        Creates a dictionary (self.fit_arrange_dict={})of FitArrange elements
        with Uid as keys
        """
        FitEngine.__init__(self)
        self.curr_thread = None

    def fit(self, msg_q=None,
            q=None, handler=None, curr_thread=None,
            ftol=1.49012e-8, reset_flag=False):
        # Build collection of bumps fitness calculators
        models = [SasFitness(model=M.get_model(),
                             data=M.get_data(),
                             constraints=M.constraints,
                             fitted=M.pars,
                             initial_values=M.vals if reset_flag else None)
                  for M in self.fit_arrange_dict.values()
                  if M.get_to_fit()]
        if len(models) == 0:
            raise RuntimeError("Nothing to fit")
        problem = FitProblem(models)

        # TODO: need better handling of parameter expressions and bounds constraints
        # so that they are applied during polydispersity calculations.  This
        # will remove the immediate need for the setp_hook in bumps, though
        # bumps may still need something similar, such as a sane class structure
        # which allows a subclass to override setp.
        problem.setp_hook = ParameterExpressions(models)

        # Run the fit
        result = run_bumps(problem, handler, curr_thread)
        if handler is not None:
            handler.update_fit(last=True)

        # TODO: shouldn't reference internal parameters of fit problem
        varying = problem._parameters
        # collect the results
        all_results = []
        for M in problem.models:
            fitness = M.fitness
            fitted_index = [varying.index(p) for p in fitness.fitted_pars]
            param_list = fitness.fitted_par_names + fitness.computed_par_names
            R = FResult(model=fitness.model, data=fitness.data,
                        param_list=param_list)
            R.theory = fitness.theory()
            R.residuals = fitness.residuals()
            R.index = fitness.data.idx
            R.fitter_id = self.fitter_id
            # TODO: should scale stderr by sqrt(chisq/DOF) if dy is unknown
            R.success = result['success']
            if R.success:
                R.stderr = numpy.hstack((result['stderr'][fitted_index],
                                         numpy.NaN*numpy.ones(len(fitness.computed_pars))))
                R.pvec = numpy.hstack((result['value'][fitted_index],
                                      [p.value for p in fitness.computed_pars]))
                R.fitness = numpy.sum(R.residuals**2)/(fitness.numpoints() - len(fitted_index))
            else:
                R.stderr = numpy.NaN*numpy.ones(len(param_list))
                R.pvec = numpy.asarray( [p.value for p in fitness.fitted_pars+fitness.computed_pars])
                R.fitness = numpy.NaN
            R.convergence = result['convergence']
            if result['uncertainty'] is not None:
                R.uncertainty_state = result['uncertainty']
            all_results.append(R)

        if q is not None:
            q.put(all_results)
            return q
        else:
            return all_results

def run_bumps(problem, handler, curr_thread):
    def abort_test():
        if curr_thread is None: return False
        try: curr_thread.isquit()
        except KeyboardInterrupt:
            if handler is not None:
                handler.stop("Fitting: Terminated!!!")
            return True
        return False

    fitclass, options = get_fitter()
    steps = options.get('steps', 0)
    if steps == 0:
        pop = options.get('pop',0)*len(problem._parameters)
        samples = options.get('samples', 0)
        steps = (samples+pop-1)/pop if pop != 0 else samples
    max_step = steps + options.get('burn', 0)
    pars = [p.name for p in problem._parameters]
    #x0 = numpy.asarray([p.value for p in problem._parameters])
    options['monitors'] = [
        BumpsMonitor(handler, max_step, pars, problem.dof),
        ConvergenceMonitor(),
        ]
    fitdriver = fitters.FitDriver(fitclass, problem=problem,
                                  abort_test=abort_test, **options)
    omp_threads = int(os.environ.get('OMP_NUM_THREADS','0'))
    mapper = MPMapper if omp_threads == 1 else SerialMapper
    fitdriver.mapper = mapper.start_mapper(problem, None)
    #import time; T0 = time.time()
    try:
        best, fbest = fitdriver.fit()
    except:
        import traceback; traceback.print_exc()
        raise
    finally:
        mapper.stop_mapper(fitdriver.mapper)


    convergence_list = options['monitors'][-1].convergence
    convergence = (2*numpy.asarray(convergence_list)/problem.dof
                   if convergence_list else numpy.empty((0,1),'d'))

    success = best is not None
    return {
        'value': best if success else None,
        'stderr': fitdriver.stderr() if success else None,
        'success': success,
        'convergence': convergence,
        'uncertainty': getattr(fitdriver.fitter, 'state', None),
        }

