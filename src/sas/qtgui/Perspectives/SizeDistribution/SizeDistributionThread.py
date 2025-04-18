import logging
import time

import numpy as np

from sas.sascalc.data_util.calcthread import CalcThread

logger = logging.getLogger(__name__)


class SizeDistributionThread(CalcThread):
    """Thread performing the fit"""

    def compute(self, *args, **kwargs):
        try:
            # TODO: replace this with call to sascalc function
            time.sleep(5)
            x = np.logspace(start=1, stop=3, num=10, endpoint=True, base=10.0)
            y = [4, 6, 8, 10, 11, 9, 8, 5, 4, 2]
            results = dict(
                x=x,
                y=y,
            )

            self.completefn(results)
        except KeyboardInterrupt:
            pass
        except Exception:
            logger.exception("Size distribution fitting failed")
