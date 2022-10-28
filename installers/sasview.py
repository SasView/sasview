# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
Run sasview from an installed bundle
"""

import sys
sys.dont_write_bytecode = True

if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    from sas.cli import main
    sys.exit(main())
