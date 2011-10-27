from random import randint, random
import numpy

class DE:
    """
    Differential evolution test implementation
    Implements the Scheme_DE_rand_1 variant

       F: float
           weighting factor which determines the magnitude of perturbation
           occurring in each generation.

       crossover_rate:  float
           In general, 0 < crossover_rate < 1.  Usually
           considerably lower than 1.  Convergence slows as the value
           increases, but higher crossover rates may be necessary when

       func: w = f(p)
           The function to be minimized, of the form w = f(p), where p
           is a vector of length func_dim and w is a scalar

       func_dim: int
           The dimension of the objective function

       pop: array
           The initial population.  This should be an iterable composed of
           Rank-1 numpy arrays.  The population size must be at least 4,
           preferably much greater.

       l_bound, u_bound: vector
           arrays of size func_dim representing the upper and lower bounds
           for the parameters in the solution vectors

       tol: float
           if (max(pop_values) - min(pop_values) <= conv), the population
           has converged and the evolution will stop
       """

    def __init__(self, F, crossover_rate, func, func_dim, pop, l_bound,
                 u_bound, tol=1e-7):
        self.pop_size          = len(pop)
        self.dimension         = func_dim
        self.F_orig            = F
        self.F                 = F
        self.crossover_rate    = crossover_rate
        self.func              = func
        self.tol               = tol
        self.l_bound           = l_bound
        self.u_bound           = u_bound
        self.population        = pop
        self.generations       = 0
        self.pop_values        = [self.func(p) for p in self.population]
        self.best_gene,self.best_value = self.get_best_gene()
        self.best_gene_history = [self.best_gene]
        self.best_val_history  = [self.best_value]
        self.ncalls            = 0

    #//////////////////////////////////////////////////
    def evolve(self, numgens=1000, monitor=None):
        '''Evolve the population for numgens generations, or until it converges.
            Returns the best vector from the run'''
        try:
            import psyco
            psyco.full()
        except ImportError:
            pass

        start_gen = self.generations
        for gen in xrange(self.generations + 1, self.generations + numgens + 1):
            candidate_pop = []

            for i in xrange(self.pop_size):
                (r1, r2, r3) = self.select_participants(i)

                #perturbation/mutation
                candidate = self.population[r1] + self.F*(self.population[r2]
                                                          - self.population[r3])

                #crossover
                candidate = self.crossover(candidate, i)

                #check bound constraints
                if not self.is_within_bounds(candidate):
                    candidate = self.get_random_gene()

                #test fitness to determine membership in next gen
                candidate_val = self.func(candidate)
                if candidate_val < self.pop_values[i]:
                    candidate_pop.append(candidate)
                    self.pop_values[i] = float(candidate_val)
                else:
                    candidate_pop.append(self.population[i])
            self.ncalls += self.pop_size

            self.population  = candidate_pop
            x,fx = self.get_best_gene()
            if fx < self.best_value:
                self.best_gene, self.best_value = x,fx
                if monitor is not None:
                    monitor.improvement(x,fx,self.ncalls)
            self.best_val_history.append(self.best_value)
            self.best_gene_history.append(self.best_gene)
            self.generations = gen

            if monitor is not None:
                monitor.progress(gen-start_gen,numgens)

            if self.is_converged():
                break

        return self.best_gene


    #////////////////////////////////////////////////
    def get_random_gene(self):
        '''Generate a random gene within the bounds constraints.
           Used to replace out-of-bounds genes'''
        result = [numpy.random.uniform(low, high)
                  for low, high in zip(self.l_bound, self.u_bound)]
        return numpy.array(result)

    #////////////////////////////////////////////////
    def is_within_bounds(self, gene):
        '''Determine whether the gene meets the bounds constraints'''
        return numpy.all( (self.l_bound < gene) & (self.u_bound > gene) )

    #////////////////////////////////////////////////
    #This appears to be a total failure.  I'll leave the code in,
    #but it's not called from the main evolution loop anymore.
    def adjust_F(self):
        '''Adjust F to account for stagnation of the population '''
        #has the best vector improved this generation?
        idx = len(self.best_val_history)
        if self.best_val_history[idx - 1] == self.best_val_history[idx - 2]:
            self.stagnant_gens += 1
        else:
            self.stagnant_gens  = 0

        #adapt F to account for stagnation
        self.F = min( (self.F_orig + (self.stagnant_gens * 0.01)), 2.0)

    #////////////////////////////////////////////////
    def get_best_gene(self):
        '''find the most fit gene in the current population'''
        #print "pop", self.pop_values

        best_index = numpy.argmin(self.pop_values)
        return self.population[best_index],self.pop_values[best_index],

    #////////////////////////////////////////////////
    def select_participants(self, i):
        '''generate r1, r2, and r3 randomly from the range [0, NP-1]
            such that they are distinct values not equal to i'''
        choices = [i]
        for choice in xrange(3):
            while True:
                j = numpy.random.randint(0, self.pop_size-1)
                if j not in choices:
                    break
            choices.append(j)
        return choices[1:]
    #////////////////////////////////////////////////
    def crossover(self, candidate, i):
        '''Perform a crossover between the candidate and the ith member of
            the previous generation.'''
        result = []

        #generate lower bound of crossover (this bound is inclusive)
        low = randint(0, self.dimension-1)

        #determine the size of the crossover
        L = 0
        while random() < self.crossover_rate and L < (self.dimension - low):
            L += 1

        #calculate the upper bound of crossover (this bound is exclusive)
        high = low + L

        high  = numpy.repeat(high, self.dimension)
        low   = numpy.repeat(low,  self.dimension)
        seq   = numpy.arange(0, self.dimension)

        result = numpy.choose( ((seq >= low)&(seq < high)),
                             [candidate, self.population[i]] )
        return result

    def is_converged(self):
        '''check for convergence'''
        return max(self.pop_values) - min(self.pop_values) <= self.tol

def diffev(fn, bounds, x0=None, pop_scale=4, crossover_rate=0.8,
           Fscale=1, tolerance=1e-5, maxiter=1000, monitor=None):
    """
    Run differential evolution, returning x,fx,ncalls
    """
    lo, hi = numpy.asarray(bounds[0]), numpy.asarray(bounds[1])
    dim = len(lo)
    pop = gen_pop(dim*pop_scale, lo, hi, dim)
    if x0 is not None:
        pop[0] = numpy.asarray(x0)
    evolver = DE(Fscale, crossover_rate, fn, dim, pop, lo, hi, tolerance)
    evolver.evolve(maxiter, monitor=monitor)
    return evolver.best_gene, evolver.best_value, evolver.ncalls




########################################################################
#end DE def
########################################################################
def gen_pop(size, l_bound, u_bound, dimension):
    '''generate a random population of vectors within the given bounds.  dimension
       indicates the length of the vectors.  l_bound and u_bound should be vectors
       of length dimension (any iterable container should work)'''
    result = []
    for i in xrange(size):
        entry = []
        for j in xrange(dimension):
            entry.append( ((u_bound[j] - l_bound[j]) * random()) + l_bound[j] )
        result.append(numpy.array(entry))
    return result
