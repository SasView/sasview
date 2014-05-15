# This program is public domain
"""
Functions for manipulating expressions.   
"""
import math
import re
from deps import order_dependencies

# simple pattern which matches symbols.  Note that it will also match
# invalid substrings such as a3...9, but given syntactically correct
# input it will only match symbols.
_symbol_pattern = re.compile('([a-zA-Z][a-zA-Z_0-9.]*)')

def symbols(expr,symtab):
    """
    Given an expression string and a symbol table, return the set of symbols
    used in the expression.  Symbols are only returned once even if they
    occur multiple times.  The return value is a set with the elements in
    no particular order.
    
    This is the first step in computing a dependency graph.
    """
    matches = [m.group(0) for m in _symbol_pattern.finditer(expr)]
    return set([symtab[m] for m in matches if m in symtab])

def substitute(expr,mapping):
    """
    Replace all occurrences of symbol s with mapping[s] for s in mapping.
    """
    # Find the symbols and the mapping
    matches = [(m.start(),m.end(),mapping[m.group(1)])
               for m in _symbol_pattern.finditer(expr)
               if m.group(1) in mapping]
    
    # Split the expression in to pieces, with new symbols replacing old
    pieces = []
    offset = 0
    for start,end,text in matches:
        pieces += [expr[offset:start],text]
        offset = end
    pieces.append(expr[offset:])
    
    # Join the pieces and return them
    return "".join(pieces)

def find_dependencies(pars):
    """
    Returns a list of pair-wise dependencies from the parameter expressions.
    
    For example, if p3 = p1+p2, then find_dependencies([p1,p2,p3]) will
    return [(p3,p1),(p3,p2)].  For base expressions without dependencies,
    such as p4 = 2*pi, this should return [(p4, None)]
    """
    symtab = dict([(p.path, p) for p in pars])
    # Hack to deal with expressions without dependencies --- return a fake
    # dependency of None.  
    # The better solution is fix order_dependencies so that it takes a 
    # dictionary of {symbol: dependency_list}, for which no dependencies 
    # is simply []; fix in parameter_mapping as well
    def symbols_or_none(expr,symtab):
        syms = symbols(expr,symtab)
        return syms if len(syms) else [None]
    deps = [(p,dep) 
            for p in pars if p.iscomputed()
            for dep in symbols_or_none(p.expression,symtab)]
    return deps

def parameter_mapping(pairs):
    """
    Find the parameter substitution we need so that expressions can
    be evaluated without having to traverse a chain of 
    model.layer.parameter.value
    """
    left,right = zip(*pairs)
    pars = set(left+right)
    symtab = dict( ('P%d'%i,p) for i,p in enumerate(pars) )
    # p is None when there is an expression with no dependencies
    mapping = dict( (p.path,'P%d.value'%i) 
                    for i,p in enumerate(pars) 
                    if p is not None)
    return symtab,mapping

def no_constraints(): 
    """
    This parameter set has no constraints between the parameters.
    """
    pass

def build_eval(pars, context={}):
    """
    Build and return a function to evaluate all parameter expressions in
    the proper order.
    
    Inputs:
        pars is a list of parameters
        context is a dictionary of additional symbols for the expressions

    Output:
        updater function

    Raises:
       AssertionError - model, parameter or function is missing
       SyntaxError - improper expression syntax
       ValueError - expressions have circular dependencies

    This function is not terribly sophisticated, and it would be easy to
    trick.  However it handles the common cases cleanly and generates
    reasonable messages for the common errors.

    This code has not been fully audited for security.  While we have
    removed the builtins and the ability to import modules, there may
    be other vectors for users to perform more than simple function
    evaluations.  Unauthenticated users should not be running this code.

    Parameter names are assumed to contain only _.a-zA-Z0-9#[]
    
    The list of parameters is probably something like::
    
        parset.setprefix()
        pars = parset.flatten()
    
    Note that math uses acos while numpy uses arccos.  To avoid confusion
    we allow both.
    
    Should try running the function to identify syntax errors before
    running it in a fit.
    
    Use help(fn) to see the code generated for the returned function fn.
    dis.dis(fn) will show the corresponding python vm instructions.
    """

    # Initialize dictionary with available functions
    globals = {}
    globals.update(math.__dict__)
    globals.update(dict(arcsin=math.asin,arccos=math.acos,
                        arctan=math.atan,arctan2=math.atan2))
    globals.update(context)

    # Sort the parameters in the order they need to be evaluated
    deps = find_dependencies(pars)
    if deps == []: return no_constraints
    par_table,par_mapping = parameter_mapping(deps)
    order = order_dependencies(deps)
    
    # Finish setting up the global and local namespace
    globals.update(par_table)
    locals = {}

    # Define the function body
    exprs = [p.path+"="+p.expression for p in order]
    code = [substitute(s,par_mapping) for s in exprs]
        
    # Define the constraints function
    functiondef = """
def eval_expressions():
    '''
    %s
    '''
    %s
"""%("\n    ".join(exprs),"\n    ".join(code))

    #print "Function:",functiondef
    exec functiondef in globals,locals
    retfn = locals['eval_expressions']

    # Remove garbage added to globals by exec
    globals.pop('__doc__',None)
    globals.pop('__name__',None)
    globals.pop('__file__',None)
    globals.pop('__builtins__')
    #print globals.keys()

    return retfn

def test():
    import inspect, dis
    import math
    
    symtab = {'a.b.x':1, 'a.c':2, 'a.b':3, 'b.x':4}
    expr = 'a.b.x + sin(4*pi*a.c) + a.b.x/a.b'
    
    # Check symbol lookup
    assert symbols(expr, symtab) == set([1,2,3])

    # Check symbol rename
    assert substitute(expr,{'a.b.x':'Q'}) == 'Q + sin(4*pi*a.c) + Q/a.b'
    assert substitute(expr,{'a.b':'Q'}) == 'a.b.x + sin(4*pi*a.c) + a.b.x/Q'


    # Check dependency builder
    # Fake parameter class
    class Parameter:
        def __init__(self, name, value=0, expression=''):
            self.path = name
            self.value = value
            self.expression = expression
        def iscomputed(self): return (self.expression != '')
        def __repr__(self): return self.path
    p1 = Parameter('G0.sigma',5)
    p2 = Parameter('other',expression='2*pi*sin(G0.sigma/.1875) + M1.G1')
    p3 = Parameter('M1.G1',6)
    p4 = Parameter('constant',expression='2*pi*35')
    # Simple chain
    assert set(find_dependencies([p1,p2,p3])) == set([(p2,p1),(p2,p3)])
    # Constant expression
    assert set(find_dependencies([p1,p4])) == set([(p4,None)])
    # No dependencies
    assert set(find_dependencies([p1,p3])) == set([])

    # Check function builder
    fn = build_eval([p1,p2,p3])

    # Inspect the resulting function
    if False:
        print inspect.getdoc(fn)
        print dis.dis(fn)

    # Evaluate the function and see if it updates the
    # target value as expected
    fn()
    expected = 2*math.pi*math.sin(5/.1875) + 6
    assert p2.value == expected,"Value was %s, not %s"%(p2.value,expected)
    
    # Check empty dependency set doesn't crash
    fn = build_eval([p1,p3])
    fn()

    # Check that constants are evaluated properly
    fn = build_eval([p4])
    fn()
    assert p4.value == 2*math.pi*35

    # Check additional context example; this also tests multiple
    # expressions
    class Table:
        Si = 2.09
        values = {'Si': 2.07}
    tbl = Table()
    p5 = Parameter('lookup',expression="tbl.Si")
    fn = build_eval([p1,p2,p3,p5],context=dict(tbl=tbl))
    fn()
    assert p5.value == 2.09,"Value for %s was %s"%(p5.expression,p5.value)
    p5.expression = "tbl.values['Si']"
    fn = build_eval([p1,p2,p3,p5],context=dict(tbl=tbl))
    fn()
    assert p5.value == 2.07,"Value for %s was %s"%(p5.expression,p5.value)
    

    # Verify that we capture invalid expressions
    for expr in ['G4.cage', 'M0.cage', 'M1.G1 + *2', 
                 'piddle',
                 '5; import sys; print "p0wned"',
                 '__import__("sys").argv']:
        try:
            p6 = Parameter('broken',expression=expr)
            fn = build_eval([p6])
            fn()
        except Exception,msg: pass
        else:  raise "Failed to raise error for %s"%expr

if __name__ == "__main__": test()
