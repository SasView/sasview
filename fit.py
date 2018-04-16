#!/usr/bin/env python
"""
Bumps model file for running saved sasview fits.

Fit configuration (including fitted variables and ranges) is set up in the
Sasview GUI and saved as a .svs or .fitv file.  These can then be run
directly from bumps using::

    path/to/sasview/fit.py path/to/save.svs [--bumps_option ...]

Alternatively, if sasview is installed on your python path, use::

    python -m sas.sascalc.fit.fitstate path/to/save.svs [--bumps_option ...]

In unix/mac you can create a file on your shell path (e.g., ~/bin/sasbumps)
containing::

    #!/usr/bin/env python
    from sas.sascalc.fit.fitstate import bumps_cli
    bumps_cli()

set it as executable with::

    chmod a+x ~/bin/sasbumps

and use::

    sasbumps path/to/save.svs [--bumps_option ...]
"""

# ============ Set up python environment ==============
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run import prepare
del sys.path[0]
prepare(rebuild=False)

# =========== Run BUMPS ===============
from sas.sascalc.fit.fitstate import bumps_cli
bumps_cli()
