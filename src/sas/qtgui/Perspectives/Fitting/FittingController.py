"""
FittingController: Handles the business logic for fitting operations.

This module separates fitting-related business logic from the FittingWidget UI,
making the code more maintainable and testable.
"""

import copy
import logging
from typing import Any

import numpy as np
from PySide6 import QtGui

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Perspectives.Fitting import FittingUtilities
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
        # Data going in
        data = self.logic.data
        model = self.logic.kernel_module
        qmin = self.widget.q_range_min
        qmax = self.widget.q_range_max

        # Update the model with extra parameters (polydispersity, magnetism)
        # This ensures that values from the PolydispersityWidget and MagnetismWidget
        # are applied to the kernel_module before fitting
        self.widget.updateKernelModelWithExtraParams(model)

        # Gather all parameters to fit
        params_to_fit = copy.deepcopy(self.widget.main_params_to_fit)

        # Add polydispersity parameters if enabled
        if self.widget.chkPolydispersity.isChecked():
            for p in self.widget.polydispersity_widget.poly_params_to_fit:
                if "Distribution of" in p:
                    params_to_fit += [self.widget.polydispersity_widget.polyNameToParam(p)]
                else:
                    params_to_fit += [p]

        # Add magnetism parameters if enabled
        if self.widget.chkMagnetism.isChecked() and self.widget.canHaveMagnetism():
            params_to_fit += self.widget.magnetism_widget.magnet_params_to_fit

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

    def updateModelFromList(self, param_dict: dict[str, tuple[float, float]]) -> None:
        """
        Update the model with new parameters and create the errors column.

        Parameters
        ----------
        param_dict : dict[str, tuple[float, float]]
            Dictionary mapping parameter names to (value, error) tuples
        """
        assert isinstance(param_dict, dict)

        def updateFittedValues(row):
            """Update fitted values in the main model."""
            param_name = str(self.widget._model_model.item(row, 0).text())
            if not self.widget.isCheckable(row) or param_name not in list(param_dict.keys()):
                return
            # Modify the param value
            param_repr = GuiUtils.formatNumber(param_dict[param_name][0], high=True)
            self.widget._model_model.item(row, 1).setText(param_repr)
            self.logic.kernel_module.setParam(param_name, param_dict[param_name][0])
            if self.widget.has_error_column:
                error_repr = GuiUtils.formatNumber(param_dict[param_name][1], high=True)
                self.widget._model_model.item(row, 2).setText(error_repr)

        def updatePolyValues(row):
            """Update polydispersity values in the main model."""
            param_name = str(self.widget._model_model.item(row, 0).text()) + '.width'
            if not self.widget.isCheckable(row) or param_name not in list(param_dict.keys()):
                return
            # Modify the param value
            param_repr = GuiUtils.formatNumber(param_dict[param_name][0], high=True)
            self.widget._model_model.item(row, 0).child(0).child(0, 1).setText(param_repr)
            # Modify the param error
            if self.widget.has_error_column:
                error_repr = GuiUtils.formatNumber(param_dict[param_name][1], high=True)
                self.widget._model_model.item(row, 0).child(0).child(0, 2).setText(error_repr)

        def createErrorColumn(row):
            """Create error column items for the main model."""
            item = QtGui.QStandardItem()

            def createItem(param_name):
                if param_name not in self.widget.main_params_to_fit:
                    error_repr = ""
                else:
                    error_repr = GuiUtils.formatNumber(param_dict[param_name][1], high=True)
                item.setText(error_repr)

            def curr_param():
                return str(self.widget._model_model.item(row, 0).text())

            [createItem(param_name) for param_name in list(param_dict.keys()) if curr_param() == param_name]

            error_column.append(item)

        def createPolyErrorColumn(row):
            """Create error column in polydispersity sub-rows."""
            item = self.widget._model_model.item(row, 0)
            if not item.hasChildren():
                return
            poly_item = item.child(0)
            if not poly_item.hasChildren():
                return
            poly_item.insertColumn(2, [QtGui.QStandardItem("")])

        def deletePolyErrorColumn(row):
            """Remove error column from polydispersity sub-rows."""
            item = self.widget._model_model.item(row, 0)
            if not item.hasChildren():
                return
            poly_item = item.child(0)
            if not poly_item.hasChildren():
                return
            poly_item.removeColumn(2)

        if self.widget.has_error_column:
            # Remove previous entries
            self.widget._model_model.removeColumn(2)
            self.widget.iterateOverModel(deletePolyErrorColumn)

        # Create top-level error column
        error_column = []
        self.widget.lstParams.itemDelegate().addErrorColumn()
        self.widget.iterateOverModel(createErrorColumn)

        self.widget._model_model.insertColumn(2, error_column)

        FittingUtilities.addErrorHeadersToModel(self.widget._model_model)

        # Create error column in polydispersity sub-rows
        self.widget.iterateOverModel(createPolyErrorColumn)

        self.widget.has_error_column = True

        # Block signals temporarily so we don't update charts with every model change
        self.widget._model_model.dataChanged.disconnect()
        self.widget.iterateOverModel(updateFittedValues)
        self.widget.iterateOverModel(updatePolyValues)
        self.widget._model_model.dataChanged.connect(self.widget.onMainParamsChange)
