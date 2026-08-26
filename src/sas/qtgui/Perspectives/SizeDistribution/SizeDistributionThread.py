import logging
from collections.abc import Callable

from sasdata.dataloader.data_info import Data1D

from sas.qtgui.Perspectives.SizeDistribution.SizeDistributionUtils import (
    MaxEntParameters,
    MaxEntResult,
)
from sas.sascalc.data_util.calcthread import CalcThread
from sas.sascalc.size_distribution.SizeDistribution import sizeDistribution

logger = logging.getLogger(__name__)


class SizeDistributionThread(CalcThread):
    """Thread performing the fit."""

    def __init__(
        self,
        data: Data1D,
        background: Data1D,
        params: MaxEntParameters,
        completefn: Callable[[MaxEntResult], None] | None = None,
        updatefn: Callable | None = None,
        yieldtime: float = 0.01,
        worktime: float = 0.01,
        exception_handler: Callable | None = None,
    ) -> None:
        CalcThread.__init__(
            self,
            completefn,
            updatefn,
            yieldtime,
            worktime,
            exception_handler=exception_handler,
        )
        self.data: Data1D = data
        self.background: Data1D = background
        self.params: MaxEntParameters = params
        self.starttime: float = 0

    def compute(self, *args, **kwargs) -> None:
        """Perform the size distribution fit."""
        sd = sizeDistribution(self.data)
        sd.qMin = self.params.qmin
        sd.qMax = self.params.qmax
        sd.diamMin = self.params.dmin
        sd.diamMax = self.params.dmax
        sd.aspectRatio = self.params.aspect_ratio
        sd.contrast = self.params.contrast
        sd.model = self.params.model
        sd.iterMax = self.params.max_iterations
        sd.skyBackground = self.params.sky_background
        sd.weightType = self.params.weight_type
        sd.weightFactor = self.params.weight_factor
        sd.weightPercent = self.params.weight_percent
        sd.nbins = self.params.num_bins

        trim_data, intensities, init_bins_back, sigma = sd.prep_maxEnt(self.background, full_fit=self.params.full_fit)
        convergence_info = sd.run_maxEnt(trim_data, intensities, init_bins_back, sigma)

        convergences, num_iters = zip(*convergence_info)
        results = MaxEntResult(
            convergences=convergences,
            num_iters=num_iters,
            chisq=sd.chiSq_maxEnt,
            bins=sd.bins,
            bin_diff=sd._binDiff,
            bin_mag=sd.BinMagnitude_maxEnt,
            bin_err=sd.BinMagnitude_Errs,
            data_max_ent=sd.Iq_maxEnt,
            statistics=sd.MaxEnt_statistics,
        )

        self.completefn(results)
