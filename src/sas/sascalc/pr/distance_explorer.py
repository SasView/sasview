
################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation.
#
#See the license text in license.txt
#
#copyright 2009, University of Tennessee
################################################################################

"""
Module to explore the P(r) inversion results for a range
of D_max value. User picks a number of points and a range of
distances, then get a series of outputs as a function of D_max
over that range.
"""


class Results:
    """
    Class to hold the inversion output parameters
    as a function of D_max
    """
    def __init__(self):
        """
        Initialization. Create empty arrays
        and dictionary of labels.
        """
        # Array of output for each inversion
        self.chi2 = []
        self.osc = []
        self.pos = []
        self.pos_err = []
        self.rg = []
        self.iq0 = []
        self.bck = []
        self.d_max = []
        ## List of errors found during the last exploration
        self.errors = []


class DistExplorer:
    """
    The explorer class
    """

    def __init__(self, pr_state):
        """
        Initialization.

        :param pr_state: sas.sascalc.pr.invertor.Invertor object

        """
        self.pr_state = pr_state
        self._default_min = 0.8 * self.pr_state.d_max
        self._default_max = 1.2 * self.pr_state.d_max

    def __call__(self, dmin=None, dmax=None, npts=10):
        """
        Compute the outputs as a function of D_max.

        :param dmin: minimum value for D_max
        :param dmax: maximum value for D_max
        :param npts: number of points for D_max

        """
        # Take care of the defaults if needed
        if dmin is None:
            dmin = self._default_min

        if dmax is None:
            dmax = self._default_max

        # Results object to store the computation outputs.
        results = Results()

        # Loop over d_max values
        for i in range(npts):
            d = dmin + i * (dmax - dmin) / (npts - 1.0)
            self.pr_state.d_max = d
            try:
                out, cov = self.pr_state.invert(self.pr_state.nfunc)

                # Store results
                iq0 = self.pr_state.iq0(out)
                rg = self.pr_state.rg(out)
                pos = self.pr_state.get_positive(out)
                pos_err = self.pr_state.get_pos_err(out, cov)
                osc = self.pr_state.oscillations(out)

                results.d_max.append(self.pr_state.d_max)
                results.bck.append(self.pr_state.background)
                results.chi2.append(self.pr_state.chi2)
                results.iq0.append(iq0)
                results.rg.append(rg)
                results.pos.append(pos)
                results.pos_err.append(pos_err)
                results.osc.append(osc)
            except Exception as exc:
                # This inversion failed, skip this D_max value
                msg = "ExploreDialog: inversion failed for "
                msg += "D_max=%s\n %s" % (str(d), exc)
                results.errors.append(msg)

        return results
