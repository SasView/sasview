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
from copy import copy
from keyword import iskeyword


def standard_symbols(context={}):
    symbols = {}
    symbols.update(math.__dict__)
    symbols.update(dict(arcsin=math.asin, arccos=math.acos,
                        arctan=math.atan, arctan2=math.atan2))
    symbols.update(context)
    symbols['id'] = id
    return symbols

def _check_syntax(target, expr, html=False):
    try:
        compile(expr, expr, "exec")
    except SyntaxError as exc:
        if html:
            if "\n" in expr:
                # Multiline expression. Be lazy and just show line, col for
                # syntax error since this should never happen.
                return [
                    f"Syntax error on line {exc.lineno} column {exc.offset} for {target}:\n<pre>\n{expr}\n</pre>"]

            if exc.offset > len(expr):
                # Single line expression with error after the expression.
                # Probably missing a closing paren, but it could
                # also be that the expression ends with an operator such as
                # "3+4+"
                return [f"Expression `{target} = {expr}` is not complete."]

            # Single line expression. Wrap the tail of the expr after the
            # syntax error in <b>...</b>. exc.lineno=1, exc.text = expr+"\n",
            # and exc.offset = location of the syntax error in expr.
            return [
                f"Syntax error in expression '{target} = {expr[:exc.offset - 1]}<b>{expr[exc.offset - 1:]}</b>'"]
        else:
            return ["Syntax error in expression '%s = %s'" % (target, expr)]
    return []

def _check_free_variables(target, expr, symbol_table, html=False):
    undefined = [sym for sym in _symbols(expr)
                 if sym not in symbol_table and not iskeyword(sym)]
    if undefined:
        undefined_str = ", ".join(sorted(undefined))
        if html:
            for symbol in undefined:
                # Identify the symbol for replacement as everything between a
                # word boundary. Since symbols can contain '.', we need to
                # use negative lookbehind and negative lookahead on a
                # character set containing '.' to check for the boundaries.
                # Also, if there is a '.' in the symbol it could match any
                # character, so it needs to be turned into a regular
                # expression that matches '.'.
                pattern = f"(?<![a-zA-Z0-9_.]){symbol.replace('.', '[.]')}(?![a-zA-Z0-9_.])"
                expr = re.sub(pattern, f"<b>{symbol}</b>", expr)
            return ["Unknown parameters (%s) in expression '%s = %s'"
                    % (undefined_str, target, expr)]
        else:
            return ["Unknown parameters (%s) in expression '%s = %s'"
                    % (undefined_str, target, expr)]
    return []

# simple pattern which matches symbols.  Note that it will also match
# invalid substrings such as a3...9, but given syntactically correct
# input it will only match symbols.
_SYMBOL_PATTERN = re.compile('([a-zA-Z_][a-zA-Z_0-9.]*)')
def _symbols(expr):
    return set(m.group(0) for m in _SYMBOL_PATTERN.finditer(expr))

def _substitute(expr, mapping):
    """
    Replace all occurrences of symbol s with mapping[s] for s in mapping.
    """
    # Find the symbols and the mapping
    matches = [(m.start(), m.end(), mapping[m.group(1)])
               for m in _SYMBOL_PATTERN.finditer(expr)
               if m.group(1) in mapping]

    # Split the expression in to pieces, with new symbols replacing old
    pieces = []
    offset = 0
    for start, end, text in matches:
        pieces += [expr[offset:start], text]
        offset = end
    pieces.append(expr[offset:])

    # Join the pieces and return them
    return "".join(pieces)

def _find_dependencies(symtab, exprs):
    """
    Returns a list of pair-wise dependencies from the parameter expressions.

    *symtab* gives the *{'parameter': value}* table of available parameters.

    *exprs* gives the *{'parameter': 'expr'}* table of parameter expressions.

    For example, if p3 = p1+p2, then find_dependencies([p1, p2, p3]) will
    return *[('p3', 'p1'), ('p3', 'p2')]*. For base expressions without
    dependencies, such as p4 = 2*pi, this should return *[('p4', None)]*.
    """
    deps = [(target, source)
            for target, expr in exprs.items()
            for source in _dependent_symbols(expr, symtab)]
    return deps

# Hack to deal with expressions without dependencies --- return a fake
# dependency of None.
# The better solution is fix order_dependencies so that it takes a
# dictionary of {symbol: dependency_list}, for which no dependencies
# is simply []; fix in parameter_mapping as well
def _dependent_symbols(expr, symtab):
    """
    Given an expression string and a symbol table, return the set of symbols
    used in the expression. Symbols are only returned once even if they occur
    multiple times. The return value is a set with the elements in no
    particular order. Returns a set containing *None* if no dependencies (as
    needed by *order_dependencies*).

    This is the first step in computing a dependency graph.
    """
    deps = set([m for m in _symbols(expr) if m in symtab])
    return deps if deps else {None}

def _parameter_mapping(pairs):
    """
    Find the parameter substitution we need so that expressions can
    be evaluated without having to traverse a chain of
    model.layer.parameter.value
    """
    left, right = zip(*pairs)
    pars = list(sorted(p for p in set(left+right) if p is not None))
    definition = dict( ('P%d'%i, p)  for i, p in enumerate(pars) )
    # p is None when there is an expression with no dependencies
    substitution = dict((p, 'P%d.value'%i)
                        for i, p in enumerate(sorted(pars))
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

       RunTimeError if any expression contains a syntax error, if any
       symbol used is not defined, or if there are circular dependencies
       between symbols. Runtime error argument is a string describing all
       found errors.

    This function is not terribly sophisticated, and it would be easy to
    trick.  However it handles the common cases cleanly and generates
    reasonable messages for the common errors.

    This code has not been fully audited for security.  While we have
    removed the builtins and the ability to import modules, there may
    be other vectors for users to perform more than simple function
    evaluations. Unauthenticated users should not be running this code.

    Parameter names are assumed to contain only _.a-zA-Z0-9#[]

    Both names are provided for inverse functions, e.g., acos and arccos.

    Should try running the function to identify syntax errors before
    running it in a fit.

    Use help(fn) to see the code generated for the returned function fn.
    dis.dis(fn) will show the corresponding python vm instructions.
    """
    retfn, errors = _compile_constraints(symtab, exprs, context=context)
    if errors:
        raise RuntimeError("\n".join(errors))
    return retfn

# Simple parameter class for checking constraints
class _Variable:
    def __init__(self, value=0):
        self.value = value

class _Parameter:
    slot = None
    def __init__(self, value=0):
        self.slot = _Variable(value)

    @property
    def value(self):
        return self.slot.value

    @value.setter
    def value(self, value):
        self.slot.value = value

def check_constraints(symtab, exprs, context={}, html=False):
    """
    Returns a list of errors in *exprs* or the empty list if there are none.
    If the html flag is set to True, the list elements will have html <b>
    markups that allow the caller to control rendering:

    Unknown symbol: tags unknown symbols in *exprs*
    Syntax error: tags the beginning of a syntax error in *exprs*
    Cyclic dependency: tags comma separated parameters that have
    cyclic dependency

    All symbols must exist in *context* or in *symtab*. The symbols in
    *context* should be constants or functions. The symbols in *symtab*
    can be constants or parameter objects with a *value* attribute.

    It first runs :func:`compile_constraints`, returning a list of errors
    if any. If there are no errors it runs the compiled constraints function,
    returning any errors it produces. Any parameters in *symtab* are copied
    with a shallow copy so they aren't overridden when the constraints are run.
    """
    # Make sure the symbols are wrapped in parameter objects. This allows
    # us to run the function and check constraints.
    symtab = {k: (copy(v) if hasattr(v, 'value') else _Parameter(v))
              for k, v in symtab.items()}
    retfn, errors = _compile_constraints(symtab,
                                         exprs,
                                         context=context,
                                         html=html)
    if not errors:
        try:
            retfn()
        except Exception as exc:
            errors.append(str(exc))
    return errors

def _compile_constraints(symtab, exprs, context={}, html=False):
    errors = []

    # Check the syntax before compiling the complete function.
    available_symbols = standard_symbols(context)
    available_symbols.update(symtab)
    for k, v in exprs.items():
        errors.extend(_check_syntax(k, v, html=html))
        errors.extend(_check_free_variables(k, v, available_symbols, html=html))

    # Sort the parameters in the order they need to be evaluated
    # Note: order_dependencies raises an error if there are cyclic dependencies
    deps = _find_dependencies(symtab, exprs)
    if not deps:
        return no_constraints, []
    try:
        order = order_dependencies(deps)
    except Exception as exc:
        if html:
            errors.append("Cyclic dependency amongst parameters: "
                          "<b>%s</b>"
                          % str(exc))
        else:
            errors.append("Cyclic dependency amongst parameters: %s" % str(exc))

    if errors:
        return None, errors
    #print(f"{symtab=}\n  {deps=}\n  {order=}\n")

    # Rather than using the full path to the parameters in the parameter
    # expressions, instead use Pn, and substitute Pn.value for each occurrence
    # of the parameter in the expression.
    names = list(sorted(symtab.keys()))
    parameters = dict(('P%d'%i, symtab[k]) for i, k in enumerate(names))
    mapping = dict((k, 'P%d.slot'%i) for i, k in enumerate(names))

    # Add the parameters to the global context
    global_context = standard_symbols(context)
    global_context.update(parameters)
    local_context = {}

    # Define the constraints function
    assignments = ["=".join((p, exprs[p])) for p in order]
    code = [_substitute(s, mapping) for s in assignments]
    # TODO: maybe wrap body in try...except block and return NaN?
    functiondef = """
def eval_expressions():
    '''
    %s
    '''
    %s
    return 0
"""%("\n    ".join(assignments), "\n    ".join(code))

    #print(" ", "\n  ".join(code))
    #print("Function: "+functiondef)
    # CRUFT: python < 3.0;  doc builder isn't allowing the following exec
    # https://stackoverflow.com/questions/4484872/why-doesnt-exec-work-in-a-function-with-a-subfunction/41368813#comment73790496_41368813
    #exec(functiondef, global_context, local_context)
    source = functiondef
    location = "\n  ".join(assignments)
    eval(compile(source, location, 'exec'), global_context, local_context)
    retfn = local_context['eval_expressions']

    # Remove garbage added to globals by exec
    global_context.pop('__doc__', None)
    global_context.pop('__name__', None)
    global_context.pop('__file__', None)
    global_context.pop('__builtins__')
    #print globals.keys()

    return retfn, errors

def order_dependencies(pairs):
    """
    Order elements from pairs so that b comes before a in the
    ordered list for all pairs (a, b).
    """
    emptyset = set()
    order = []

    # Break pairs into left set and right set
    # Note: pairs is array or list, so use "len(pairs) > 0" to check for empty.
    left, right = [set(s) for s in zip(*pairs)] if len(pairs) > 0 else ([], [])
    while len(pairs) > 0:
        # Find which items only occur on the right
        independent = right - left
        if independent == emptyset:
            cycleset = ", ".join(str(s) for s in left)
            raise ValueError(cycleset)

        # The possibly resolvable items are those that depend on the independents
        dependent = set([a for a, b in pairs if b in independent])
        pairs = [(a, b) for a, b in pairs if b not in independent]
        if len(pairs) == 0:
            resolved = dependent
        else:
            left, right = [set(s) for s in zip(*pairs)]
            resolved = dependent - left

        order += resolved

    return order

# ========= Test code ========
def _check(msg, pairs):
    """
    Verify that the list n contains the given items, and that the list
    satisfies the partial ordering given by the pairs in partial order.
    """
    # pairs are a list of (lhs, rhs)
    # lhs may be repeated e.g., x = a+b has pairs (x, a) and (x, b)
    # lhs may be in rhs e.g., x = a+b; b = 2*c has pairs (x, a) (x, b), (b, c)
    # find lhs eval order; since (x, b) is a pair then b must come before x
    # Note: pairs is array or list, so use "len(pairs) > 0" to check for empty.
    lhs_list, rhs_list = zip(*pairs) if len(pairs) > 0 else ([], [])
    items = set(lhs_list) # items = all LHS, removing duplicates
    order = order_dependencies(pairs)
    if set(order) != set(items) or len(order) != len(items):
        raise ValueError("%s expect %s to contain %s for %s"
                         % (msg, order, sorted(items), pairs))
    for lhs, rhs in pairs:
        if lhs in order and rhs in order and order.index(rhs) >= order.index(lhs):
            raise ValueError("%s expect %s before %s in %s for %s"
                             % (msg, lhs, rhs, order, pairs))

def test_deps():
    import numpy as np

    # Null case
    _check("test empty", [])

    # Some dependencies
    _check("test1", [(2, 7), (1, 5), (1, 4), (2, 1), (3, 1), (5, 6)])
    _check("test1 renumbered",
           [(6, 1), (7, 3), (7, 4), (6, 7), (5, 7), (3, 2)])
    _check("test1 numpy",
           np.array([(2, 7), (1, 5), (1, 4), (2, 1), (3, 1), (5, 6)]))

    # No dependencies
    _check("test2", [(4, 1), (3, 2), (8, 4)])

    # Cycle test
    pairs = [(1, 4), (4, 3), (4, 5), (5, 1)]
    try:
        n = order_dependencies(pairs)
    except ValueError:
        pass
    else:
        raise ValueError("test3 expect ValueError exception for %s" % (pairs,))

    # large test for gross speed check
    A = np.random.randint(4000, size=(1000, 2))
    A[:, 1] += 4000  # Avoid cycles
    _check("test-large", A)

    # depth tests
    k = 200
    A = np.array([range(0, k), range(1, k+1)]).T
    _check("depth-1", A)

    A = np.array([range(1, k+1), range(0, k)]).T
    _check("depth-2", A)

def test_expr():
    import dis
    import inspect

    symtab = {'a.b.x': 1, 'a.c': 2, 'a.b': 3, 'b.x': 4}
    expr = 'a.b.x + sin(4*pi*a.c) + a.b.x/a.b'

    # Check symbol lookup
    assert _dependent_symbols(expr, symtab) == set(['a.b.x', 'a.c', 'a.b'])

    # Check symbol rename
    assert _substitute(expr, {'a.b.x': 'Q'}) == 'Q + sin(4*pi*a.c) + Q/a.b'
    assert _substitute(expr, {'a.b': 'Q'}) == 'a.b.x + sin(4*pi*a.c) + a.b.x/Q'

    # Check dependency builder
    # Fake parameter class
    class TestParameter:
        def __init__(self, name, value=0, expression=''):
            self.path = name
            self.value = value
            self.expression = expression
        def iscomputed(self):
            return (self.expression != '')
        def __repr__(self):
            value = self.expression if self.iscomputed() else str(self.value)
            return self.path + '=' + value
    def world(*pars):
        symtab = dict((p.path, p) for p in pars)
        exprs = dict((p.path, p.expression) for p in pars if p.iscomputed())
        return symtab, exprs
    p1 = TestParameter('G0.sigma', 5)
    p2 = TestParameter('other', expression='2*pi*sin(G0.sigma/.1875) + M1.G1')
    p3 = TestParameter('M1.G1', 6)
    p3_circular = TestParameter('M1.G1', expression='other + 6')
    p3_self = TestParameter('M1.G1', expression='M1.G1')
    p4 = TestParameter('constant', expression='2*pi*35')
    p5 = TestParameter('chain', expression='2+other')
    # Simple pairs
    assert (set(_find_dependencies(*world(p1, p2, p3)))
            == set([(p2.path, p1.path), (p2.path, p3.path)]))
    # Chain
    assert (set(_find_dependencies(*world(p1, p2, p3, p5)))
            == set([(p2.path, p1.path), (p2.path, p3.path), (p5.path, p2.path)]))
    # Constant expression
    assert set(_find_dependencies(*world(p1, p4))) == set([(p4.path, None)])
    # No dependencies
    assert not set(_find_dependencies(*world(p1, p3)))

    # Make sure 'other' is evaluated before 'chain'
    assert (order_dependencies(_find_dependencies(*world(p1, p2, p3, p5)))
            == [p2.path, p5.path])
    # Check function builder
    fn = compile_constraints(*world(p1, p2, p3))

    # Inspect the resulting function
    if 0:
        print(inspect.getdoc(fn))
        print(dis.dis(fn))

    # Evaluate the function and see if it updates the
    # target value as expected
    fn()
    expected = 2*math.pi*math.sin(5/.1875) + 6
    assert p2.value == expected, "Value was %s, not %s" % (p2.value, expected)

    # Make sure check_constraints returns an empty list for these expressions.
    assert not check_constraints(*world(p1, p2, p3))

    # Check empty dependency set doesn't crash
    fn = compile_constraints(*world(p1, p3))
    fn()

    # Check that constants are evaluated properly
    fn = compile_constraints(*world(p4))
    fn()
    assert p4.value == 2*math.pi*35

    # Check that circular definitions get flagged
    try:
        fn = compile_constraints(*world(p1, p2, p3_circular))
    except Exception as exc:
        assert str(exc).startswith('Cyclic')
    else:
        raise RuntimeError("failed to raise error for cyclic dependency")
    try:
        fn = compile_constraints(*world(p1, p2, p3_self))
    except Exception as exc:
        assert str(exc).startswith('Cyclic')
    else:
        raise RuntimeError("failed to raise error for self dependency")

    # Make sure errors are returned from check_constraints
    errors = check_constraints(*world(p1, p2, p3_circular))
    assert len(errors) == 1 and errors[0].startswith('Cyclic')
    errors = check_constraints(*world(p1, p2, p3_self))
    assert len(errors) == 1 and errors[0].startswith('Cyclic')

    # Check additional context example; this also tests multiple expressions
    tbl = {'tbl_Si': 2.09}
    p5 = TestParameter('lookup', expression="tbl_Si")
    fn = compile_constraints(*world(p1, p2, p3, p5), context=tbl)
    fn()
    assert p5.value == 2.09, "Value for %s was %s" % (p5.expression, p5.value)

    #class Table:
    #    Si = 2.09
    #    values = {'Si': 2.07}
    #tbl = Table()
    #p5 = TestParameter('lookup', expression="tbl.Si")
    #fn = compile_constraints(*world(p1, p2, p3, p5), context=dict(tbl=tbl))
    #fn()
    #assert p5.value == 2.09, "Value for %s was %s"%(p5.expression, p5.value)
    #
    #p5.expression = "tbl.values['Si']"
    #fn = compile_constraints(*world(p1, p2, p3, p5), context=dict(tbl=tbl))
    #fn()
    #assert p5.value == 2.07, "Value for %s was %s" % (p5.expression, p5.value)

    # Verify that we capture invalid expressions
    for expr in ['G4.cage', 'M0.cage', 'M1.G1 + *2',
                 'piddle',
                 #'5; import sys; print("p0wned")',
                 '__import__("sys").argv'
                 ]:
        try:
            p6 = TestParameter('broken', expression=expr)
            fn = compile_constraints(*world(p6))
            fn()
        except Exception:
            #print(msg)
            pass
        else:
            raise RuntimeError("Failed to raise error for %s" % (expr,))

    # Verify that check_constraints returns multiple errors.
    symtab = {
        'M1.sld': 1.0,
        'M1.sld_solvent': 6.0,
        'M1.radius': 50,
        'M1.scale': 1.0,
    }
    exprs = {
        'M1.background': 'M1.scal/1e5',
        'M1.sld': 'M1.sld_solvent + 1',
        'M1.sld_solvent': 'M1.sld + 2',
    }
    errors = check_constraints(symtab, exprs)
    assert len(errors) == 2
    #print("\n".join(errors))

if __name__ == "__main__":
    test_expr()
    test_deps()
