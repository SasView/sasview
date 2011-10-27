# This program is public domain
# Author: Paul Kienzle
"""
Functions for manipulating dependencies.

Parameter values must be updated in the correct order.  If parameter A
depends on parameter B, then parameter B must be evaluated first.  
"""

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
            raise ValueError,"Cyclic dependencies amongst %s"%cycleset

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
        raise Exception,"%s expect %s to contain %s for %s"%(msg,n,items,pairs)
    for lo,hi in pairs:
        if lo in n and hi in n and n.index(lo) >= n.index(hi):
            raise Exception,"%s expect %s before %s in %s for %s"%(msg,lo,hi,n,pairs)

def test():
    import numpy

    # Null case
    _check("test empty",[])

    # Some dependencies
    _check("test1",[(2,7),(1,5),(1,4),(2,1),(3,1),(5,6)])
    _check("test1 renumbered",[(6,1),(7,3),(7,4),(6,7),(5,7),(3,2)])
    _check("test1 numpy",numpy.array([(2,7),(1,5),(1,4),(2,1),(3,1),(5,6)]))

    # No dependencies
    _check("test2",[(4,1),(3,2),(8,4)])

    # Cycle test
    pairs = [(1,4),(4,3),(4,5),(5,1)] 
    try: n = order_dependencies(pairs)
    except ValueError: pass
    else: raise Exception,"test3 expect ValueError exception for %s"%(pairs,)

    # large test for gross speed check
    A = numpy.random.randint(4000,size=(1000,2))
    A[:,1] += 4000  # Avoid cycles
    _check("test-large",A)

    # depth tests
    k = 200
    A = numpy.array([range(0,k),range(1,k+1)]).T
    _check("depth-1",A)

    A = numpy.array([range(1,k+1),range(0,k)]).T
    _check("depth-2",A)

if __name__ == "__main__":
    test()
