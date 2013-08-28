#

def uniquelist(inputlist, hash=None): 
    '''remove redunduant elements from the give list
    and return a list of unique elements.

    inputlist: input list
    hash: use this function to make the items in the list hashable.

    Implementation details:
        This function is order-preserving.
    '''
    if hash is None:
        hash = __builtins__.hash
    seen = {}
    result = []
    for item in inputlist:
        marker = hash(item)
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result


def test():
    assert uniquelist([1,2,2,3])==[1,2,3]
    return


def main():
    test()
    return

if __name__ == '__main__': main()


# version
__id__ = "$Id$"

# End of file 
