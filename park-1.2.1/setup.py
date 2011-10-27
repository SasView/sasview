#!/usr/bin/env python
# This program is public domain

import os
import sys
import numpy

if len(sys.argv) == 1:
    sys.argv.append('install')

# BEFORE importing distutils, remove MANIFEST. distutils doesn't properly
# update it when the contents of directories change.
if os.path.exists('MANIFEST'): os.remove('MANIFEST')


def configuration(parent_package='',
                  top_path=None
                  ):
    from numpy.distutils.misc_util import Configuration
    if  numpy.__version__ < '1.0.0':
        raise RuntimeError, 'numpy version %s or higher required, but got %s'\
              % ('1.0.0', numpy.__version__)

    config = Configuration(None, parent_package, top_path)

    config.set_options(ignore_setup_xxx_py=True,
                        assume_default_configuration=True,
                        delegate_options_to_subpackages=True,
                        quiet=True
                       )

    config.add_subpackage('park')

    config.add_data_files( ('park','*.txt') )
    config.add_data_files( ('park','park.epydoc') )
    config.get_version(os.path.join('park','version.py'))   # sets config.version

    return config



def setup_package():

    from numpy.distutils.core import setup
    from numpy.distutils.misc_util import Configuration

    setup( name = 'park',
           maintainer = "DANSE reflectometry group",
           maintainer_email = "unknown",
           description = "Distributed fitting service",
           url = "http://www.reflectometry.org/danse/park",
           license = 'BSD',
           configuration=configuration
           )


if __name__ == '__main__':
    setup_package()
