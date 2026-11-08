"""
FittingController: Handles the business logic for fitting operations.

This module separates fitting-related business logic from the FittingWidget UI,
making the code more maintainable and testable.
"""

import logging
from typing import Any

import numpy as np

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Perspectives.Fitting.model import rules
from sas.sascalc.fit.BumpsFitting import BumpsFit as Fit

logger = logging.getLogger(__name__)


class FittingController:
    """
    Controller class that manages fitting operations separately from the UI.

    This class handles:
    - Preparing fitters for single/batch/simultaneous fitting
    - Processing fitting results
    - Updating model parameters from fit results
    """

    def __init__(self, widget):
        """
        Initialize the FittingController.

        Parameters
        ----------
        widget : FittingWidget
            The parent FittingWidget instance for accessing UI state and logic
        """
        self.widget = widget

    @property
    def logic(self):
        """Convenience accessor for the widget's FittingLogic instance."""
        return self.widget.logic

    @property
    def all_logic(self):
        """Convenience accessor for all FittingLogic instances (for batch fitting)."""
        return self.widget._logic

    def prepareFitters(
        self,
        fitter: Fit | None = None,
        fit_id: int = 0,
        weight_increase: int = 1
    ) -> tuple[list[Fit], int]:
        """
        Prepare the Fitter object(s) for use in fitting.

        Parameters
        ----------
        fitter : Fit | None
            None for single/batch fitting, Fit() instance for simultaneous fitting
        fit_id : int
            Starting fit ID
        weight_increase : int
            Weight increase factor

        Returns
        -------
        tuple[list[Fit], int]
            List of prepared Fit objects and the next fit_id

        Raises
        ------
        ValueError
            If no parameters are selected for fitting or if model setup fails
        """
        # Data going in: an engine instance of its own, with the document's effective state
        model = self.widget.kernel_builder.build(self.widget.document)
        qmin, qmax, params_to_fit = self.document_fit_inputs()

        if not params_to_fit:
            raise ValueError('Fitting requires at least one parameter to optimize.')

        # Get the constraints
        constraints = []
        for model_key in self.widget.model_dict:
            constraints += self.widget.getComplexConstraintsForModel(model_key=model_key)
        if fitter is None:
            # For single fits - check for inter-model constraints
            constraints = self.widget.getConstraintsForFitting()

        smearer = self.widget.smearing_widget.smearer()

        fitters = []
        # Order datasets if chain fit
        order = self.widget.all_data
        if self.widget.is_chain_fitting:
            order = self.widget.order_widget.ordering()

        for fit_index in order:
            fitter_single = Fit() if fitter is None else fitter
            data = GuiUtils.dataFromItem(fit_index)
            # Potential weights added directly to data
            weighted_data = self.widget.addWeightingToData(data)

            try:
                fitter_single.set_model(
                    model, fit_id, params_to_fit,
                    data=weighted_data,
                    constraints=constraints
                )
            except ValueError as ex:
                raise ValueError("Setting model parameters failed with: %s" % ex)

            fitter_single.set_data(
                data=weighted_data, id=fit_id, smearer=smearer,
                qmin=qmin, qmax=qmax
            )
            fitter_single.select_problem_for_fit(id=fit_id, value=1)
            fitter_single.set_weight_increase(fit_id, weight_increase)

            if fitter is None:
                # Assign id to the new fitter only
                fitter_single.fitter_id = [self.widget.page_id]
            fit_id += 1
            fitters.append(fitter_single)

        return fitters, fit_id

    def document_fit_inputs(self) -> tuple[float, float, list[str]]:
        """Q range and parameters to fit (by their legacy row names) from the page's document (Phase 3)."""
        doc = self.widget.document
        return doc.options.qmin, doc.options.qmax, [doc.parameters.legacy_key(k) for k in rules.keys_to_fit(doc)]

    def paramDictFromResults(self, results: Any) -> dict[str, tuple[float, float]] | None:
        """
        Extract optimized parameters from fit results.

        Parameters
        ----------
        results : Any
            Fit results structure from bumps

        Returns
        -------
        dict[str, tuple[float, float]] | None
            Dictionary mapping parameter names to (value, error) tuples,
            or None if fitting did not converge
        """
        pvec = [float(p) for p in results.pvec]
        if results.fitness is None or \
            not np.isfinite(results.fitness) or \
            np.any(pvec is None) or \
            not np.all(np.isfinite(pvec)):
            msg = "Fitting did not converge!"
            GuiUtils.communicator.statusBarUpdateSignal.emit(msg)
            msg += results.mesg
            logger.error(msg)
            return None

        if results.mesg:
            logger.warning(results.mesg)

        param_list = results.param_list  # ['radius', 'radius.width']
        param_values = pvec                # array([ 0.36221662,  0.0146783 ])
        param_stderr = results.stderr      # array([ 1.71293015,  1.71294233])
        params_and_errors = list(zip(param_values, param_stderr))
        param_dict = dict(zip(param_list, params_and_errors))

        return param_dict
