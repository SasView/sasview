import os

MODULE_TEMPLATE="""

******************************************************************************
%(name)s
******************************************************************************

:mod:`%(package)s.%(module)s`
==============================================================================

.. automodule:: %(package)s.%(module)s
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:

"""

INDEX_TEMPLATE="""

.. _api-index:

##############################################################################
   %(package_name)s
##############################################################################

.. only:: html

   :Release: |version|
   :Date: |today|

.. toctree::

   %(rsts)s
"""

SRC_DIR = 'source/api'

for root, dirs, files in os.walk('../../src'):
    if '__init__.py' not in files:
        continue
    
    if not os.path.isdir(SRC_DIR):
        os.mkdir(SRC_DIR)
        
    module_path = root.replace('../../src/','')
    package = module_path.replace('/','.')
    
    if package.startswith('sans.simulation'):
        continue
    
    print package
    
    if not os.path.isdir('%s/%s' % (SRC_DIR, module_path)):
        os.mkdir('%s/%s' % (SRC_DIR, module_path))    
    rsts = "\n  ".join(dirs)
    with open('%s/%s/index.rst' % (SRC_DIR, module_path), 'w') as f:
        f.write(INDEX_TEMPLATE % {'package_name': package,
                                  'rsts': rsts})
        f.close()
        
    for item in files:
        if not item.endswith('.py'):
            continue
        
        module, ext = os.path.splitext(item)
        with open('%s/%s/%s.rst' % (SRC_DIR, module_path, module), 'w') as f:
            f.write(MODULE_TEMPLATE % {'name': module,
                                       'package': package,
                                       'module': module})
            f.close()
    
    #TODO: Need index for each module
