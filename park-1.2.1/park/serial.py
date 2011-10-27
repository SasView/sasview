# This program is public domain
"""
Service to handle serialization and deserialization of fit objects.

Object serialization is useful for long term storage, interlanguage
communication and network transmission.  In all cases, the process
involves an initial encode() followed by a later decode().

We need the following properties for serialization/deserialization:

1. human readable so that disaster recovery is possible
2. readable/writable by other languages and environments
3. support for numerics: complex, nan, inf, arrays, full precision
4. version support: load object into newer versions of the
   program even if the class structure has changed
5. refactoring support: load object into newer versions of the
   program even if the classes have been moved or renamed

A complete solution would also support self referential data structures,
but that is beyond our needs.

Python's builtin serialization, pickle/cPickle, cannot meet these
needs.  It is python specific, and not friendly to human readers
or readers from other environments such as IDL which may want to
load or receive data from a python program.  Pickle inf/nan doesn't
work on windows --- some of our models may use inf data, and some of
our results may be nan.  pickle has minimal support for versioning:
users can write __setstate__ which accepts a dictionary and adjusts
it accordingly.  Beware though that version must be an instance
variable rather than a class variable, since class variables are not
seen by pickle.  If the class is renamed, then pickle can do nothing
to recover it.

Instead of pickle, we break the problem into steps: structucture and
encoding.  A pair of functions deconstruct() and reconstruct() work
directly with the structure.  Deconstruct extracts the state of the 
python object defined using a limited set of python primitives.  
Reconstruct takes an extracted state and rebuilds the complete python 
object.  See documentation on the individual functions for details.

For serial encoding we will use json.  The json format is human 
readable and easily parsed. json iteself does not define support 
of Inf/NaN, though some json tools support it using the native
javascript values of Infinity and Nan. Various xml encodings are 
also possible, though somewhat more difficult to work with.

Object persistence for long term storage places particular burdens
on the serialization protocol.  In particular, the class may have
changed since the instance was serialized.  To aid the process of
maintaining classes over the long term, the class definition can
contain the following magic names:

__version__
    Strict version number of the class.  See isnewer() for
    details, or distutils.version.StrictVersion.
__factory__
    Name of a factory function to return a new instance of
    the class.  This will be stored as the class name, and
    should include the complete path so that it can be
    imported by python.
__reconstruct__
    Method which takes a structure tree and rebuilds the object.
    This is different from __setstate__ in that __setstate__
    assumes its children have already been reconstructed.  This
    is the difference between top-down and bottom-up
    interpretation.  Bottom-up is usually easiear and sufficient,
    but top-down is required for radical restructuring of the
    object representation.


Example
=======

The following example shows how to use reconstruct and factory to get
maximum flexibility when restoring an object::

    from danse.common.serial import isnewer, reconstruct, setstate
    def data():
        from data import Data
        return Data()
    class Data(object):
        __version__ = '1.2'
        __factory__ = 'danse.builder.data'
        def __reconstruct__(self,instance):
            '''
            Reconstruct the state from 
            '''
            if isnewer('1.0',instance['version']):
                raise RuntimeError('pre-1.0 data objects no longer supported')
            if isnewer('1.1',instance['version']):
                # Version 1.1 added uncertainty; default it to zero
                instance['state']['uncertainty'] = 0
            setstate(self,reconstruct(instance['state']))
"""

import types
import sys
import demjson

def encode(obj):
    """
    Convert structure to a string.
   
    Basic python types (list, string, dictionary, numbers, boolean, None) 
    are converted directly to the corresponding string representation.
    tuples and sets are converted to lists, and str is converted to unicode.
   
    Python objects are represented by::
    
        { 
            '.class': 'module.classname', 
            '.version': 'versionstring',
            '.state': { object state }
        }
    
    where state comes from the object __getstate__, the object __dict__ or
    the object __slots__.  See the pickle documentation for details.

    Python functions are represented by::
    
        {
            '.function': 'module.functionname'
        }
        
    """
    return demjson.encode(deconstruct(obj))

def decode(string):
    """
    Convert string to structure, reconstructing classes as needed.  See
    pickle documentation for details.  This function will fail with a
    RuntimeError if the version of the class in the string is newer
    than the version of the class in the python path.
    """
    return reconstruct(demjson.decode(string))


def deconstruct(obj):
    """
    Convert an object hierarchy into python primitives.
    
    The primitives used are int, float, str, unicode, bool, None,
    list, tuple, and dict.
    
    Classes are encoded as a dict with keys '.class', '.version', and '.state'.  
    Version is copied from the attribute __version__ if it exists.
    
    Functions are encoded as a dict with key '.function'.
    
    Raises RuntimeError if object cannot be deconstructed.  For example,
    deconstruct on deconstruct will cause problems since '.class' will
    be in the dictionary of a deconstructed object.
    """
    if type(obj) in [int, float, str, unicode, bool] or obj is None:
        return obj
    elif type(obj) in [list, tuple, set]:
        return type(obj)(deconstruct(el) for el in obj)
    elif type(obj) == dict:
        # Check for errors
        for name in ['.class', '.function']:
            if name in obj:
                raise RuntimeError("Cannot deconstruct dict containing "+name)
        return dict((k,deconstruct(v)) for k,v in obj.items())
    elif type(obj) == types.FunctionType:
        return {
            '.function'  : obj.__module__+'.'+obj.__name__
        }
    else:
        cls = _getclass(obj)
        version = _getversion(obj)
        return { 
            '.class'   : _getclass(obj), 
            '.version' : _getversion(obj), 
            '.state'   : deconstruct(_getstate(obj))
        }
 
def reconstruct(tree):
    """
    Reconstruct an object hierarchy from a tree of primitives.
    
    The tree is generated by deconstruct from python primitives 
    (list, dict, string, number, boolean, None) with classes 
    encoded as a particular kind of dict.
    
    Unlike pickle, we do not make an exact copy of the original
    object.  In particular, the serialization format may not
    distinguish between list and tuples, or str and unicode.  We
    also have no support for self-referential structures.
    
    Raises RuntimeError if could not reconstruct
    """
    if type(tree) in [int, float, str, unicode, bool] or tree is None:
        return tree
    elif type(tree) in [list, tuple, set]:
        return type(tree)(reconstruct(el) for el in tree)
    elif type(tree) == dict:
        if '.class' in tree:
            # Chain if program version is newer than stored version (too cold)
            fn = _lookup_refactor(tree['.class'],tree['.version'])
            if fn is not None: return fn(tree)

            # Fail if program version is older than stored version (too hot)
            obj = _createobj(tree['.class'])
            if isnewer(tree['.version'],_getversion(obj)):
                raise RuntimeError('Version of %s is out of date'%tree['.class'])
            # Reconstruct if program version matches stored version (just right)
            if hasattr(obj, '__reconstruct__'):
                obj.__reconstruct__(tree['.state'])
            else:
                _setstate(obj,reconstruct(tree['.state']))
            return obj
        elif '.function' in tree:
            return _import_symbol(tree['.function'])
        else:
            return dict((k,reconstruct(v)) for k,v in tree.items())
    else:
        raise RuntimeError('Could not reconstruct '+type(obj).__name__)

def _getversion(obj):
    version = getattr(obj,'__version__','0.0')
    try:
        # Force parsing of version number to check format
        isnewer(version,'0.0')
    except ValueError,msg:
        raise ValueError("%s for class %s"%(msg,obj.__class__.__name__))
    return version

def _getclass(obj):
    if hasattr(obj,'__factory__'): return obj.__factory__
    return obj.__class__.__module__+'.'+obj.__class__.__name__

def _getstate(obj):
    if hasattr(obj,'__getinitargs__') or hasattr(obj,'__getnewargs__'):
        # Laziness: we could fetch the initargs and store them, but until
        # we need to do so, I'm not going to add the complexity.
        raise RuntimeError('Cannot serialize a class with initialization arguments')
    elif hasattr(obj,'__getstate__'):
        state = obj.__getstate__()
    elif hasattr(obj,'__slots__'):
        state = dict((s,getattr(obj,s)) for s in obj.__slots__ if hasattr(obj,s))
    elif hasattr(obj,'__dict__'):
        state = obj.__dict__
    else:
        state = {}
    return state

def _setstate(obj,kw):
    if hasattr(obj,'__setstate__'):
        obj.__setstate__(kw)
    elif hasattr(obj,'__slots__'):
        for k,v in kw.items(): setattr(obj,k,v)
    elif hasattr(obj,'__dict__'):
        obj.__dict__ = kw
    else:
        pass
    return obj

def _lookup_refactor(cls,ver):
    return None

class _EmptyClass: pass
def _import_symbol(path):
    """
    Recover symbol from path.
    """
    parts = path.split('.')
    module_name = ".".join(parts[:-1])
    symbol_name = parts[-1]
    __import__(module_name)
    module = sys.modules[module_name]
    symbol = getattr(module,symbol_name)
    return symbol

def _createobj(path):
    """
    Create an empty object which we can update with __setstate__
    """
    factory = _import_symbol(path)
    if type(factory) is types.FunctionType:
        # Factory method to return an empty class instance
        obj = factory()
    elif type(factory) is types.ClassType:
        # Old-style class: create an empty class and override its __class__
        obj = _EmptyClass()
        obj.__class__ = factory
    elif type(factory) is types.TypeType:
        obj = factory.__new__(factory)
    else:
        raise RuntimeError('%s should be a function, class or type'%path)
    return obj

def isnewer(version,target):
    """
    Version comparison function.  Returns true if version is at least
    as new as the target version.

    A version number consists of two or three dot-separated numeric 
    components, with an optional "pre-release" tag on the end.  The 
    pre-release tag consists of the letter 'a' or 'b' followed by 
    a number.  If the numeric components of two version numbers 
    are equal, then one with a pre-release tag will always
    be deemed earlier (lesser) than one without.

    The following will be true for version numbers::

      8.2 < 8.19a1 < 8.19 == 8.19.0

    
    You should follow the rule of incrementing the minor version number
    if you add attributes to your models, and the major version number
    if you remove attributes.  Then assuming you are working with
    e.g., version 2.2, your model loading code will look like::
    
        if isnewer(version, Model.__version__):
            raise IOError('software is older than model')
        elif isnewer(xml.version, '2.0'):
            instantiate current model from xml
        elif isnewer(xml.version, '1.0'):
            instantiate old model from xml
            copy old model format to new model format
        else:
            raise IOError('pre-1.0 models not supported')

    Based on distutils.version.StrictVersion
    """
    from distutils.version import StrictVersion as Version
    return Version(version) > Version(target)

class _RefactoringRegistry(object):
    """
    Directory of renamed classes.
    
    """
    registry = {}
    
    @classmethod
    def register(cls,oldname,newname,asof_version):
        """
        As of the target version, references to the old name are no
        longer valid (e.g., when reconstructing stored objects), and
        should be resolved by the new name (or None if they should
        just raise an error.)  The old name can then be reused for
        new objects or abandoned.
        """
        # Insert (asof_version,newname) in the right place in the
        # list of rename targets for the object.  This list will
        # be empty unless the name is reused.
        if name not in cls.registry: cls.registry[name] = []
        for idx,(version,name) in cls.registry[name]:
            if isnewer(asof_version, version):
                cls.registry[name].insert(idx,(asof_version, newname))
                break
        else:
            cls.registry[name].append((asof_version, newname))
    
    @classmethod
    def redirect(cls, oldname, newname, version):
        if oldname not in cls.registry[oldname]: return None
        for idx,(target_version,newname) in cls.registry[name]:
            if isnewer(target_version, version):
                return target_version
        # error conditions at this point

def refactor(oldname,newname,asof_version):
    """
    Register the renaming of a class.  
   
    As code is developed and maintained over time, it is sometimes 
    beneficial to restructure the source to support new features.  
    However, the structure and location of particular objects is 
    encoded in the saved file format.

    When you move a class that may be stored in a model,
    be sure to put an entry into the registry saying where
    the model was moved, or None if the model is no longer
    supported.
    
    reconstructor as a function to build a python object from
    a particular class/version, presumably older than the current
    version.  This is necessary, e.g., to set default values for new
    fields or to modify components of the model which are now
    represented differently.
    
    The reconstructor function takes the structure above as 
    its argument and returns a python instance.  You are free
    to restructure the state and version fields as needed to
    bring the object in line with the next version, then call
    setstate(tree) to build the return object.  Indeed this
    technique will chain, and you can morph an ancient version
    of your models into the latest version.
    """

    return _RefactoringRegistry.redirect(oldname, newname, asof_version)

# Test classes need to be at the top level for reconstruct to find them
class _Simple: x = 5
class _SimpleNew(object): x = 5
class _Slotted(object): __slots__ = ['a','b']
class _Controlled:
    def __getstate__(self): return ["mystate",self.__dict__]
    def __setstate__(self, state):
        if state[0] != "mystate": raise RuntimeError("didn't get back my state")
        self.__dict__ = state[1]
class _Factory: __factory__ = __name__ + "._factory"
def _factory():
    obj =  _Factory()
    # Note: can't modify obj because state will be overridden
    _Factory.fromfactory = True
    return obj
class _VersionError:
    __version__ = "3.5."
def _hello():
    return 'hello'
def test():
    primitives = ['list',1,{'of':'dict',2:'really'},True,None]
    assert deconstruct(primitives) == primitives
    # Hmmm... dicts with non-string keys are not permitted by strict json
    # I'm not sure we care for our purposes, but it would be best to avoid
    # them and instead have a list of tuples which can be converted to and
    # from a dict if the need arises
    assert encode(primitives) == '["list",1,{"of":"dict",2:"really"},true,null]'

    h = _Simple()
    h.a = 2
    #print encode(deconstruct(h))
    assert decode(encode(h)).a == h.a
    
    assert decode(encode(_hello))() == 'hello'

    h = _SimpleNew()
    h.a = 2
    #print encode(deconstruct(h))
    assert decode(encode(h)).a == h.a

    h = _Slotted()
    h.a = 2
    #print encode(deconstruct(h))
    assert decode(encode(h)).a == h.a

    h = _Controlled()
    h.a = 2
    #print encode(deconstruct(h))
    assert decode(encode(h)).a == h.a

    h = _Factory()
    h.a = 2
    #print encode(deconstruct(h))
    assert decode(encode(h)).a == h.a
    assert hasattr(h,'fromfactory')
    
    try:
        deconstruct(_VersionError())
        raise RuntimeError("should have raised a version error")
    except ValueError,msg:
        assert "_VersionError" in str(msg)

if __name__ == "__main__": test()
