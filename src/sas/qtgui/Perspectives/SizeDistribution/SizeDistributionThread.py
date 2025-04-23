import logging


from sas.qtgui.Perspectives.SizeDistribution.SizeDistributionUtils import (
    MaxEntParameters,
    MaxEntResult,
)
from sas.sascalc.data_util.calcthread import CalcThread
from sas.sascalc.poresize.SizeDistribution import sizeDistribution
from sasdata.dataloader.data_info import Data1D

logger = logging.getLogger(__name__)


class SizeDistributionThread(CalcThread):
    """Thread performing the fit"""

    def __init__(
        self,
        data: Data1D,
        background: Data1D,
        params: MaxEntParameters,
        error_func=None,
        completefn=None,
        updatefn=None,
        yieldtime=0.01,
        worktime=0.01,
    ):
        """
        Initialize parameters
        """
        CalcThread.__init__(self, completefn, updatefn, yieldtime, worktime)
        self.data = data
        self.background = background
        self.params = params
        self.error_func = error_func
        self.starttime = 0

    def compute(self, *args, **kwargs):
        try:
            sd = sizeDistribution(self.data)
            sd.diamMin = self.params.dmin
            sd.diamMax = self.params.dmax
            sd.aspectRatio = self.params.aspect_ratio
            sd.contrast = self.params.contrast
            sd.model = self.params.model
            sd.iterMax = self.params.max_iterations
            sd.skyBackground = self.params.sky_background
            sd.weightType = self.params.weight_type
            sd.weightFactor = self.params.weight_factor

            trim_data, intensities, init_bins_back, sigma = sd.prep_maxEnt(
                self.background, full_fit=self.params.full_fit
            )
            chisq, bins, bin_diff, bin_mag, bin_err, data_max_ent = sd.run_maxEnt(
                trim_data, intensities, init_bins_back, sigma
            )

            results = MaxEntResult(
                chisq=chisq,
                bins=bins,
                bin_diff=bin_diff,
                bin_mag=bin_mag,
                bin_err=bin_err,
                data_max_ent=data_max_ent,
            )

            self.completefn(results)
        except KeyboardInterrupt:
            pass
        except Exception:
            logger.exception("Size distribution fitting failed")
