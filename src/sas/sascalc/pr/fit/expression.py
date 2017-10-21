from __future__ import print_function

# This program is public domain
"""
Parameter expression evaluator.

For systems in which constraints are expressed as string expressions rather
than python code, :func:`compile_constraints` can construct an expression
evaluator that substitutes the computed values of the expressions into the
parameters.

The compiler requires a symbol table, an expression set and a context.
The symbol table maps strings containing fully qualified names such as
'M1.c[3].full_width' to parameter objects with a 'value' property that
can be queried and set.  The expression set maps symbol names from the
symbol table to string expressions.  The context provides additional symbols
for the expressions in addition to the usual mathematical functions and
constants.

The expressions are compiled and interpreted by python, with only minimal
effort to make sure that they don't contain bad code.  The resulting
constraints function returns 0 so it can be used directly in a fit problem
definition.

Extracting the symbol table from the model depends on the structure of the
model.  If fitness.parameters() is set correctly, then this should simply
be a matter of walking the parameter data, remembering the path to each
parameter in the symbol table.  For compactness, dictionary elements should
be referenced by .name rather than ["name"].  Model name can be used as the
top level.

Getting the parameter expressions applied correctly is challenging.
The following monkey patch works by overriding model_update in FitProblem
so that after setp(p) is called and, the constraints expression can be
applied before telling the underlying fitness function that the model
is out of date::

        # Override model update so that parameter constraints are applied
        problem._model_update = problem.model_update
        def model_update():
            constraints()
            problem._model_update()
        problem.model_update = model_update

Ideally, this interface will change
"""
import math
import re

# simple pattern which matches symbols.  Note that it will also match
# invalid substrings such as a3...9, but given syntactically correct
# input it will only match symbols.
_symbol_pattern = re.compile('([a-zA-Z_][a-zA-Z_0-9.]*)')

def _symbols(expr,symtab):
    """
    Given an expression string and a symbol table, return the set of symbols
    used in the expression.  Symbols are only returned once even if they
    occur multiple times.  The return value is a set with the elements in
    no particular order.

    This is the first step in computing a dependency graph.
    """
    matches = [m.group(0) for m in _symbol_pattern.finditer(expr)]
    return set([symtab[m] for m in matches if m in symtab])

def _substitute(expr,mapping):
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

def _find_dependencies(symtab, exprs):
    """
    Returns a list of pair-wise dependencies from the parameter expressions.

    For example, if p3 = p1+p2, then find_dependencies([p1,p2,p3]) will
    return [(p3,p1),(p3,p2)].  For base expressions without dependencies,
    such as p4 = 2*pi, this should return [(p4, None)]
    """
    deps = [(target,source)
            for target,expr in exprs.items()
            for source in _symbols_or_none(expr,symtab)]
    return deps

# Hack to deal with expressions without dependencies --- return a fake
# dependency of None.
# The better solution is fix order_dependencies so that it takes a
# dictionary of {symbol: dependency_list}, for which no dependencies
# is simply []; fix in parameter_mapping as well
def _symbols_or_none(expr,symtab):
    syms = _symbols(expr,symtab)
    return syms if len(syms) else [None]

def _parameter_mapping(pairs):
    """
    Find the parameter substitution we need so that expressions can
    be evaluated without having to traverse a chain of
    model.layer.parameter.value
    """
    left,right = zip(*pairs)
    pars = list(sorted(p for p in set(left+right) if p is not None))
    definition = dict( ('P%d'%i,p)  for i,p in enumerate(pars) )
    # p is None when there is an expression with no dependencies
    substitution = dict( (p,'P%d.value'%i)
                    for i,p in enumerate(sorted(pars))
                    if p is not None)
    return definition, substitution

def no_constraints():
    """
    This parameter set has no constraints between the parameters.
    """
    pass

def compile_constraints(symtab, exprs, context={}):
    """
    Build and return a function to evaluate all parameter expressions in
    the proper order.

    Input:

        *symtab* is the symbol table for the model: { 'name': parameter }

        *exprs* is the set of computed symbols: { 'name': 'expression' }

        *context* is any additional context needed to evaluate the expression

    Return:

        updater function which sets parameter.value for each expression

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

    Both names are provided for inverse functions, e.g., acos and arccos.

    Should try running the function to identify syntax errors before
    running it in a fit.

    Use help(fn) to see the code generated for the returned function fn.
    dis.dis(fn) will show the corresponding python vm instructions.
    """

    # Sort the parameters in the order they need to be evaluated
    deps = _find_dependencies(symtab, exprs)
    if deps == []: return no_constraints
    order = order_dependencies(deps)


    # Rather than using the full path to the parameters in the parameter
    # expressions, instead use Pn, and substitute Pn.value for each occurrence
    # of the parameter in the expression.
    names = list(sorted(symtab.keys()))
    parameters = dict(('P%d'%i, symtab[k]) for i,k in enumerate(names))
    mapping = dict((k, 'P%d.value'%i) for i,k in enumerate(names))


    # Initialize dictionary with available functions
    globals = {}
    globals.update(math.__dict__)
    globals.update(dict(arcsin=math.asin,arccos=math.acos,
                        arctan=math.atan,arctan2=math.atan2))
    globals.update(context)
    globals.update(parameters)
    globals['id'] = id
    locals = {}

    # Define the constraints function
    assignments = ["=".join((p,exprs[p])) for p in order]
    code = [_substitute(s, mapping) for s in assignments]
    functiondef = """
def eval_expressions():
    '''
    %s
    '''
    %s
    return 0
"""%("\n    ".join(assignments),"\n    ".join(code))

    #print("Function: "+functiondef)
    exec functiondef in globals,locals
    retfn = locals['eval_expressions']

    # Remove garbage added to globals by exec
    globals.pop('__doc__',None)
    globals.pop('__name__',None)
    globals.pop('__file__',None)
    globals.pop('__builtins__')
    #print globals.keys()

    return retfn

def order_dependencies(pairs):
    """
    Order elements from pairs so that b comes before a in the
    ordered list for all pairs (a,b).
    """
    #print "order_dependencies",pairs
    emptyset = set()
    order = []

    # Break pairs into left set and right set
    left,right = [set(s) for s in zip(*pairs)] if pairs != [] else ([],[])
    while pairs != []:
        #print "within",pairs
        # Find which items only occur on the right
        independent = right - left
        if independent == emptyset:
            cycleset = ", ".join(str(s) for s in left)
            raise ValueError("Cyclic dependencies amongst %s"%cycleset)

        # The possibly resolvable items are those that depend on the independents
        dependent = set([a for a,b in pairs if b in independent])
        pairs = [(a,b) for a,b in pairs if b not in independent]
        if pairs == []:
            resolved = dependent
        else:
            left,right = [set(s) for s in zip(*pairs)]
            resolved = dependent - left
        #print "independent",independent,"dependent",dependent,"resolvable",resolved
        order += resolved
        #print "new order",order
    order.reverse()
    return order

# ========= Test code ========
def _check(msg,pairs):
    """
    Verify that the list n contains the given items, and that the list
    satisfies the partial ordering given by the pairs in partial order.
    """
    left,right = zip(*pairs) if pairs != [] else ([],[])
    items = set(left)
    n = order_dependencies(pairs)
    if set(n) != items or len(n) != len(items):
        n.sort()
        items = list(items); items.sort()
        raise ValueError("%s expect %s to contain %s for %s"%(msg,n,items,pairs))
    for lo,hi in pairs:
        if lo in n and hi in n and n.index(lo) >= n.index(hi):
            raise ValueError("%s expect %s before %s in %s for %s"%(msg,lo,hi,n,pairs))

def test_deps():
    import numpy as np

    # Null case
    _check("test empty",[])

    # Some dependencies
    _check("test1",[(2,7),(1,5),(1,4),(2,1),(3,1),(5,6)])
    _check("test1 renumbered",[(6,1),(7,3),(7,4),(6,7),(5,7),(3,2)])
    _check("test1 numpy",np.array([(2,7),(1,5),(1,4),(2,1),(3,1),(5,6)]))

    # No dependencies
    _check("test2",[(4,1),(3,2),(8,4)])

    # Cycle test
    pairs = [(1,4),(4,3),(4,5),(5,1)]
    try:
        n = order_dependencies(pairs)
    except ValueError:
        pass
    else:
        raise Exception("test3 expect ValueError exception for %s"%(pairs,))

    # large test for gross speed check
    A = np.random.randint(4000,size=(1000,2))
    A[:,1] += 4000  # Avoid cycles
    _check("test-large",A)

    # depth tests
    k = 200
    A = np.array([range(0,k),range(1,k+1)]).T
    _check("depth-1",A)

    A = np.array([range(1,k+1),range(0,k)]).T
    _check("depth-2",A)

def test_expr():
    import inspect, dis
    import math

    symtab = {'a.b.x':1, 'a.c':2, 'a.b':3, 'b.x':4}
    expr = 'a.b.x + sin(4*pi*a.c) + a.b.x/a.b'

    # Check symbol lookup
    assert _symbols(expr, symtab) == set([1,2,3])

    # Check symbol rename
    assert _substitute(expr,{'a.b.x':'Q'}) == 'Q + sin(4*pi*a.c) + Q/a.b'
    assert _substitute(expr,{'a.b':'Q'}) == 'a.b.x + sin(4*pi*a.c) + a.b.x/Q'


    # Check dependency builder
    # Fake parameter class
    class Parameter:
        def __init__(self, name, value=0, expression=''):
            self.path = name
            self.value = value
            self.expression = expression
        def iscomputed(self): return (self.expression != '')
        def __repr__(self): return self.path
    def world(*pars):
        symtab = dict((p.path,p) for p in pars)
        exprs = dict((p.path,p.expression) for p in pars if p.iscomputed())
        return symtab, exprs
    p1 = Parameter('G0.sigma',5)
    p2 = Parameter('other',expression='2*pi*sin(G0.sigma/.1875) + M1.G1')
    p3 = Parameter('M1.G1',6)
    p4 = Parameter('constant',expression='2*pi*35')
    # Simple chain
    assert set(_find_dependencies(*world(p1,p2,p3))) == set([(p2.path,p1),(p2.path,p3)])
    # Constant expression
    assert set(_find_dependencies(*world(p1,p4))) == set([(p4.path,None)])
    # No dependencies
    assert set(_find_dependencies(*world(p1,p3))) == set([])

    # Check function builder
    fn = compile_constraints(*world(p1,p2,p3))

    # Inspect the resulting function
    if 0:
        print(inspect.getdoc(fn))
        print(dis.dis(fn))

    # Evaluate the function and see if it updates the
    # target value as expected
    fn()
    expected = 2*math.pi*math.sin(5/.1875) + 6
    assert p2.value == expected,"Value was %s, not %s"%(p2.value,expected)

    # Check empty dependency set doesn't crash
    fn = compile_constraints(*world(p1,p3))
    fn()

    # Check that constants are evaluated properly
    fn = compile_constraints(*world(p4))
    fn()
    assert p4.value == 2*math.pi*35

    # Check additional context example; this also tests multiple
    # expressions
    class Table:
        Si = 2.09
        values = {'Si': 2.07}
    tbl = Table()
    p5 = Parameter('lookup',expression="tbl.Si")
    fn = compile_constraints(*world(p1,p2,p3,p5),context=dict(tbl=tbl))
    fn()
    assert p5.value == 2.09,"Value for %s was %s"%(p5.expression,p5.value)
    p5.expression = "tbl.values['Si']"
    fn = compile_constraints(*world(p1,p2,p3,p5),context=dict(tbl=tbl))
    fn()
    assert p5.value == 2.07,"Value for %s was %s"%(p5.expression,p5.value)


    # Verify that we capture invalid expressions
    for expr in ['G4.cage', 'M0.cage', 'M1.G1 + *2',
                 'piddle',
                 '5; import sys; print "p0wned"',
                 '__import__("sys").argv']:
        try:
            p6 = Parameter('broken',expression=expr)
            fn = compile_constraints(*world(p6))
            fn()
        except Exception as msg:
            #print(msg)
            pass
        else:
            raise "Failed to raise error for %s"%expr

if __name__ == "__main__":
    test_expr()
    test_deps()
