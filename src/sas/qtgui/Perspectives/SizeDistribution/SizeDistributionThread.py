import logging
import time

from sas.sascalc.data_util.calcthread import CalcThread

logger = logging.getLogger(__name__)


class SizeDistributionThread(CalcThread):
    """Thread performing the fit"""

    def compute(self, *args, **kwargs):
        try:
            # TODO: replace this with call to sascalc function
            time.sleep(5)
            x = [1, 2, 3, 4, 5]
            y = [10, 8, 6, 4, 2]
            results = dict(
                x=x,
                y=y,
            )

            self.completefn(results)
        except KeyboardInterrupt:
            pass
        except Exception:
            logger.exception("Size distribution fitting failed")
