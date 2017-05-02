"""
MachOlib fix
============

Monkey-patch macholib to get around error in v1.7 and earlier, which
gives:: 

    TypeError: dyld_find() got an unexpected keyword argument 'loader'

Add the following to the top of your setup_py2app to work around this::

    import macholib_patch
"""

import macholib
#print("~"*60 + "macholib verion: "+macholib.__version__)
if macholib.__version__ <= "1.7":
    print("Applying macholib patch...")
    import macholib.dyld
    import macholib.MachOGraph
    dyld_find_1_7 = macholib.dyld.dyld_find
    def dyld_find(name, loader=None, **kwargs):
        #print("~"*60 + "calling alternate dyld_find")
        if loader is not None:
            kwargs['loader_path'] = loader
        return dyld_find_1_7(name, **kwargs)
    macholib.MachOGraph.dyld_find = dyld_find
