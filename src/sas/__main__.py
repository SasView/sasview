# All the work is done in sas.cli. This is just a stub to allow:
#    python -m sas

# TODO: how do we make this "python -m sasview" ?

import sys

from . import cli

__doc__ = cli.__doc__

sys.exit(cli.main())
