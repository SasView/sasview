#!/usr/bin/env python
# This program is public domain

import os.path
from numpy.distutils.misc_util import Configuration
from numpy.distutils.core      import setup


def configuration(parent_package='',
                  top_path=None
                  ):
    config = Configuration('park', parent_package, top_path)

    # Extension reflmodule
    sources = [os.path.join(config.package_path,'lib',s)
               for s in ('modeling.cc','resolution.c')]

    config.add_extension('_modeling',
                         include_dirs=[config.package_path],
                         sources=sources,
                         )


    return config

if __name__ == '__main__':
    setup(**configuration(top_path='').todict())
