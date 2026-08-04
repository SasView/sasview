"""
Data collector for SASBDB export.

This module provides functionality to automatically collect and extract data
from SasView data objects, fit results, and metadata to populate SASBDB export
structures. The SASBDBDataCollector class handles:

- Extracting sample and instrument information from Data1D/Data2D objects
- Collecting fit results and model parameters from fitting widgets
- Guinier analysis via FreeSAS or q-range linear fit (from SASBDB dialog)
- Creating default structures for missing data

The collector is designed to minimize manual data entry by automatically
populating fields from available sources in the SasView session.
"""
import logging
from datetime import datetime

import numpy as np

from sas.qtgui.Plotting.PlotterData import Data1D, Data2D
from sas.qtgui.Utilities.SASBDB.sasbdb_data import (
    SASBDBBuffer,
    SASBDBExportData,
    SASBDBFit,
    SASBDBGuinier,
    SASBDBInstrument,
    SASBDBModel,
    SASBDBMolecule,
    SASBDBProject,
    SASBDBSample,
)

try:
    from sas.system.version import __version__ as SASVIEW_VERSION
except ImportError:
    SASVIEW_VERSION = "unknown"

logger = logging.getLogger(__name__)


def _meta_str(meta: dict, *keys: str) -> str | None:
    for key in keys:
        if key in meta and meta[key] not in (None, ""):
            return str(meta[key])
    return None


def _meta_float(meta: dict, *keys: str) -> float | None:
    for key in keys:
        if key in meta:
            try:
                return float(meta[key])
            except (ValueError, TypeError):
                pass
    return None


def _meta_int(meta: dict, *keys: str) -> int | None:
    for key in keys:
        if key in meta:
            try:
                return int(meta[key])
            except (ValueError, TypeError):
                pass
    return None


def _x_axis_label_is_inverse_angstrom(text: str) -> bool:
    """
    True if axis label/units indicate q in inverse Angstrom (Å\\ :sup:`-1`).

    Accepts common Sphinx/HTML and plain variants including Unicode Å.
    """
    if not text:
        return False
    markers = (
        "A^{-1}",
        "A^-1",
        "\u00c5^{-1}",  # Å^{-1} (Latin-1 capital A with ring)
        "\u00c5^-1",
        "\u00c5-1",
        "\u212b^{-1}",  # ANGSTROM SIGN U+212B
        "1/\u00c5",
    )
    return any(m in text for m in markers)


class SASBDBDataCollector:
    """
    Collects data from SasView for SASBDB export.
    
    This class provides methods to extract and organize data from various
    sources in SasView (data objects, fit results, metadata) into SASBDB
    export structures. It creates an empty SASBDBExportData object on
    initialization that can be populated using the various collection methods.
    
    The collector handles unit conversions, metadata extraction, and provides
    default values where appropriate.
    """

    def __init__(self):
        """
        Initialize the collector.
        
        Creates an empty SASBDBExportData object that will be populated
        by calling collection methods.
        """
        self.export_data = SASBDBExportData()

    def collect_from_data(self, data: Data1D | Data2D) -> tuple[SASBDBSample, SASBDBInstrument | None]:
        """
        Collect sample data and instrument information from a Data1D or Data2D object
        
        :param data: Data object to extract information from
        :return: Tuple of (SASBDBSample, SASBDBInstrument or None)
        """
        sample = SASBDBSample()
        instrument = None

        # Basic sample information
        sample.sample_title = getattr(data, 'name', None) or getattr(data, 'title', None) or getattr(data, 'filename', 'Untitled')
        sample.experimental_curve = getattr(data, 'filename', None)

        # Angular and intensity units
        if hasattr(data, '_xunit'):
            xunit = data._xunit
            if 'A' in xunit or 'angstrom' in xunit.lower():
                sample.angular_units = '1/A'
            elif 'nm' in xunit.lower():
                sample.angular_units = '1/nm'
            else:
                sample.angular_units = 'arbitrary'
        else:
            sample.angular_units = 'arbitrary'

        if hasattr(data, '_yunit'):
            yunit = data._yunit
            if 'cm' in yunit.lower():
                sample.intensity_units = '1/cm'
            else:
                sample.intensity_units = 'arbitrary'
        else:
            sample.intensity_units = 'arbitrary'

        # Instrument metadata
        if hasattr(data, 'source') and data.source:
            if hasattr(data.source, 'wavelength'):
                wavelength = data.source.wavelength
                if wavelength:
                    # Convert from Angstrom to nm if needed
                    if wavelength > 1:  # Likely in Angstrom
                        sample.wavelength = wavelength / 10.0  # Convert to nm
                    else:
                        sample.wavelength = wavelength

        if hasattr(data, 'detector') and data.detector and len(data.detector) > 0:
            detector = data.detector[0]
            if hasattr(detector, 'distance') and detector.distance:
                # Convert from mm to m
                sample.sample_detector_distance = detector.distance / 1000.0

            if hasattr(detector, 'pixel_size'):
                pixel_size = detector.pixel_size
                if hasattr(pixel_size, 'x') and pixel_size.x:
                    # Store pixel size in mm as string
                    sample.beamline_instrument = f"Pixel size: {pixel_size.x} mm"

        if hasattr(data, 'sample') and data.sample:
            if hasattr(data.sample, 'temperature') and data.sample.temperature:
                temp = data.sample.temperature
                # Check if conversion needed (assuming Celsius if reasonable, Kelvin if > 100)
                if temp > 100:
                    sample.cell_temperature = temp - 273.15  # Convert from Kelvin
                else:
                    sample.cell_temperature = temp

        # Extract metadata dictionary if available
        if hasattr(data, 'meta_data') and data.meta_data:
            meta = data.meta_data
            sample.experiment_date = _meta_str(meta, 'experiment_date', 'date')
            sample.beamline_instrument = _meta_str(meta, 'beamline', 'instrument')
            sample.concentration = _meta_float(meta, 'concentration')
            sample.experimental_molecular_weight = _meta_float(
                meta, 'molecular_weight', 'mw')
            sample.exposure_time = _meta_float(meta, 'exposure_time')
            sample.number_of_frames = _meta_int(meta, 'number_of_frames', 'frames')

        # Also check data.instrument attribute (shown in info panel)
        if hasattr(data, 'instrument') and data.instrument and not sample.beamline_instrument:
            sample.beamline_instrument = str(data.instrument)

        # Set default experiment date if not found
        if not sample.experiment_date:
            sample.experiment_date = datetime.now().strftime("%Y-%m-%d")

        # Curve type - default to "Single concentration" if we can't determine
        sample.curve_type = "Single concentration"

        # Extract instrument information
        instrument = self.collect_instrument_from_data(data)

        return sample, instrument

    def collect_instrument_from_data(self, data: Data1D | Data2D) -> SASBDBInstrument | None:
        """
        Collect instrument information from data object
        
        :param data: Data object to extract instrument information from
        :return: SASBDBInstrument object or None
        """
        instrument = SASBDBInstrument()
        has_instrument_data = False

        # Extract instrument string from data (shown in info panel)
        if hasattr(data, 'instrument') and data.instrument:
            instrument_str = str(data.instrument).strip()
            if instrument_str:
                # Try to parse instrument string - it might contain beamline/facility info
                # For now, use it as beamline_name
                instrument.beamline_name = instrument_str
                has_instrument_data = True

        # Extract from source object
        if hasattr(data, 'source') and data.source:
            source = data.source
            # Try to determine source type from source attributes
            if hasattr(source, 'radiation'):
                radiation = str(source.radiation).lower()
                if 'x-ray' in radiation or 'xray' in radiation:
                    if 'synchrotron' in radiation or hasattr(source, 'name'):
                        instrument.source_type = "X-ray synchrotron"
                    else:
                        instrument.source_type = "X-ray in house"
                elif 'neutron' in radiation:
                    instrument.source_type = "Neutron source"
                else:
                    instrument.source_type = "Other"
                has_instrument_data = True

            # Source name might contain synchrotron/facility info
            if hasattr(source, 'name') and source.name:
                source_name = str(source.name).strip()
                if source_name:
                    # Check if it looks like a synchrotron/facility name
                    if not instrument.synchrotron_name:
                        instrument.synchrotron_name = source_name
                    has_instrument_data = True

        # Extract from detector object
        if hasattr(data, 'detector') and data.detector and len(data.detector) > 0:
            detector = data.detector[0]

            # Detector pixel size for resolution
            if hasattr(detector, 'pixel_size'):
                pixel_size = detector.pixel_size
                if hasattr(pixel_size, 'x') and pixel_size.x:
                    instrument.detector_resolution = f"{pixel_size.x} mm"
                    has_instrument_data = True

            # Detector name/manufacturer if available
            if hasattr(detector, 'name') and detector.name:
                instrument.detector_manufacturer = str(detector.name)
                has_instrument_data = True

        # Extract from metadata dictionary
        if hasattr(data, 'meta_data') and data.meta_data:
            meta = data.meta_data
            if not instrument.beamline_name:
                val = _meta_str(meta, 'instrument', 'beamline')
                if val:
                    instrument.beamline_name = val
                    has_instrument_data = True
            if not instrument.synchrotron_name:
                val = _meta_str(meta, 'facility', 'synchrotron')
                if val:
                    instrument.synchrotron_name = val
                    has_instrument_data = True
            if not instrument.detector_manufacturer:
                val = _meta_str(meta, 'detector')
                if val:
                    instrument.detector_manufacturer = val
                    has_instrument_data = True
            city = _meta_str(meta, 'city')
            if city:
                instrument.city = city
                has_instrument_data = True
            country = _meta_str(meta, 'country')
            if country:
                instrument.country = country
                has_instrument_data = True

        # Return instrument only if we found some data
        if has_instrument_data:
            return instrument
        return None

    def collect_from_fit(self, fit_data: dict, model_name: str = None, optimizer_name: str = None,
                        model_parameters: list = None) -> SASBDBFit:
        """
        Collect fit information from fit results
        
        :param fit_data: Dictionary containing fit results (chi2, etc.)
        :param model_name: Name of the fitted model
        :param optimizer_name: Name of the optimizer used (stored in description)
        :param model_parameters: List of parameter tuples/lists from fitting widget
        :return: SASBDBFit object with collected data
        """
        fit = SASBDBFit()

        # Software information - always use SasView
        fit.software = "SasView"
        fit.software_version = SASVIEW_VERSION

        # Chi-squared
        if 'chi2' in fit_data:
            fit.chi_squared = float(fit_data['chi2'])
        elif 'chi_squared' in fit_data:
            fit.chi_squared = float(fit_data['chi_squared'])
        elif 'chi2_value' in fit_data:
            fit.chi_squared = float(fit_data['chi2_value'])

        # CorMap p-value
        if 'cormap_pvalue' in fit_data:
            fit.cormap_pvalue = float(fit_data['cormap_pvalue'])

        # Angular units (should match sample)
        fit.angular_units = '1/A'  # Default, will be updated from sample

        if optimizer_name:
            fit.description = f"Optimizer: {optimizer_name}"

        # Model information
        if model_name:
            model = SASBDBModel()
            model.software_or_db = model_name
            model.software_version = SASVIEW_VERSION

            # Format parameters if available
            if model_parameters:
                param_lines = []
                for param in model_parameters:
                    # Parameter format: [checkbox_state, param_name, value, "", [error_state, error_value], ...]
                    if len(param) >= 3:
                        param_name = str(param[1])
                        param_value = str(param[2])
                        param_str = f"{param_name} = {param_value}"

                        # Add error if available
                        if len(param) >= 5 and param[4] and len(param[4]) >= 2:
                            error_state, error_value = param[4]
                            if error_state and error_value:
                                param_str += f" ± {error_value}"

                        # Add unit if available
                        if len(param) >= 8 and param[7]:
                            param_str += f" {param[7]}"

                        param_lines.append(param_str)

                if param_lines:
                    model.log = "\n".join(param_lines)

            fit.models.append(model)

        return fit

    @staticmethod
    def _guinier_native_q_to_nm_scale(data) -> float:
        """
        Factor to convert q from data native units to nm\\ :sup:`-1`.

        Returns 10.0 when the x axis is \\AA\\ :sup:`-1`, else 1.0 for nm\\ :sup:`-1`.
        """
        if data is None:
            return 1.0
        if hasattr(data, "get_xaxis"):
            try:
                xaxis_label, xaxis_units = data.get_xaxis()
                xaxis_label = str(xaxis_label) if xaxis_label else ""
                xaxis_units = str(xaxis_units) if xaxis_units else ""
                combined = f"{xaxis_label} {xaxis_units}"
                if _x_axis_label_is_inverse_angstrom(combined):
                    return 10.0
            except (AttributeError, TypeError, ValueError):
                pass
        if hasattr(data, "_xunit"):
            xunit = str(data._xunit)
            if _x_axis_label_is_inverse_angstrom(xunit):
                return 10.0
        return 1.0

    @staticmethod
    def collect_guinier_from_q_range(
        data, q_min: float, q_max: float
    ) -> tuple[SASBDBGuinier | None, dict | None]:
        """
        Guinier analysis by weighted linear least squares of ln(I) vs q\\ :sup:`2`.

        Uses points with q in [min(q_min, q_max), max(q_min, q_max)], I > 0.
        Fits ln(I) = a + b q\\ :sup:`2`; then I(0) = exp(a) and
        R\\ :sub:`g` = sqrt(-3 b) in native length units, stored in **nm**
        (divide by 10 when q is in \\AA\\ :sup:`-1`).

        :param data: Object with ``x`` (q), ``y`` (I), optional ``dy``
        :param q_min: Range boundary in the same q units as ``data.x``
        :param q_max: Other range boundary
        :return: ``(guinier, fit_info)``. ``fit_info`` is ``None`` on failure,
                 otherwise ``{"a": intercept, "b": slope, "q_start": q_lo,
                 "q_end": q_hi}`` for plotting (native q units).
        """
        if not hasattr(data, "x") or not hasattr(data, "y"):
            return None, None

        q = np.asarray(data.x, dtype=float)
        I = np.asarray(data.y, dtype=float)
        if len(q) == 0 or len(I) == 0:
            return None, None

        if hasattr(data, "dy") and data.dy is not None and len(data.dy) == len(q):
            dy = np.asarray(data.dy, dtype=float)
        else:
            dy = np.ones_like(I)

        q_lo = float(min(q_min, q_max))
        q_hi = float(max(q_min, q_max))

        mask = (
            (q >= q_lo)
            & (q <= q_hi)
            & (q > 0)
            & (I > 0)
            & np.isfinite(q)
            & np.isfinite(I)
            & np.isfinite(dy)
        )
        idx = np.flatnonzero(mask)
        if idx.size < 2:
            return None, None

        q_s = q[mask]
        I_s = I[mask]
        dy_s = dy[mask]
        y = np.log(I_s)
        x = q_s**2
        sig_y = np.abs(dy_s / np.maximum(I_s, np.finfo(float).tiny))
        sig_y = np.maximum(sig_y, 1e-12)
        w = 1.0 / (sig_y**2)

        x_design = np.column_stack((np.ones_like(x), x))
        xtw = x_design.T * w
        xtw_x = xtw @ x_design
        xtw_y = xtw @ y
        try:
            params = np.linalg.solve(xtw_x, xtw_y)
        except np.linalg.LinAlgError:
            return None, None

        a, b = float(params[0]), float(params[1])
        try:
            cov = np.linalg.inv(xtw_x)
        except np.linalg.LinAlgError:
            cov = np.zeros((2, 2))
        sigma_b = float(np.sqrt(max(cov[1, 1], 0.0)))

        if b >= 0:
            return None, None

        rg_native = float(np.sqrt(-3.0 * b))
        q_to_nm = SASBDBDataCollector._guinier_native_q_to_nm_scale(data)
        if q_to_nm == 10.0:
            rg_nm = rg_native / 10.0
        else:
            rg_nm = rg_native

        if rg_nm > 0 and sigma_b > 0:
            sigma_rg = float(3.0 * sigma_b / (2.0 * rg_native))
            if q_to_nm == 10.0:
                sigma_rg /= 10.0
        else:
            sigma_rg = 0.0

        i0 = float(np.exp(a))

        guinier = SASBDBGuinier()
        guinier.rg = rg_nm
        guinier.rg_error = sigma_rg
        guinier.i0 = i0
        guinier.range_start = q_lo
        guinier.range_end = q_hi
        guinier.start_point = int(idx[0])
        guinier.end_point = int(idx[-1])

        fit_info = {
            "a": a,
            "b": b,
            "q_start": q_lo,
            "q_end": q_hi,
        }
        return guinier, fit_info

    @staticmethod
    def collect_guinier_from_freesas(data) -> SASBDBGuinier | None:
        """
        Collect Guinier analysis results using FreeSAS auto_guinier
        
        :param data: Data1D object with x (q), y (I), and dy (errors)
        :return: SASBDBGuinier object or None if analysis fails
        """
        try:
            from freesas.autorg import auto_guinier
        except ImportError:
            logger.warning("FreeSAS not available, skipping auto_guinier")
            return None

        # Check if we have 1D data with required attributes
        if not hasattr(data, 'x') or not hasattr(data, 'y'):
            return None

        q = np.array(data.x)
        I = np.array(data.y)

        # Get errors, use ones if not available
        if hasattr(data, 'dy') and data.dy is not None and len(data.dy) > 0:
            err = np.array(data.dy)
        else:
            err = np.ones_like(I)

        # Check for valid data
        if len(q) == 0 or len(I) == 0:
            return None

        # Filter out invalid values
        valid_mask = np.isfinite(q) & np.isfinite(I) & np.isfinite(err)
        valid_mask = valid_mask & (I > 0) & (err > 0) & (q > 0)

        if not np.any(valid_mask):
            return None

        q_valid = q[valid_mask]
        I_valid = I[valid_mask]
        err_valid = err[valid_mask]

        # FreeSAS expects q in nm^-1; scale native q when axis is in Å^-1.
        unit_conversion = SASBDBDataCollector._guinier_native_q_to_nm_scale(data)

        # Convert q to nm^-1 for FreeSAS
        q_for_freesas = q_valid * unit_conversion

        # Prepare data in format expected by FreeSAS: (q, I, err)
        # FreeSAS expects q in nm^-1
        data_array = np.column_stack((q_for_freesas, I_valid, err_valid))

        try:
            # Call FreeSAS auto_guinier
            result = auto_guinier(data_array)

            if result is None:
                return None

            # Extract results from RG_RESULT object
            guinier = SASBDBGuinier()

            # Rg is in nm (FreeSAS returns in nm)
            if hasattr(result, 'Rg') and result.Rg is not None:
                guinier.rg = float(result.Rg)

            # Rg error
            if hasattr(result, 'sigma_Rg') and result.sigma_Rg is not None:
                guinier.rg_error = float(result.sigma_Rg)

            # I0
            if hasattr(result, 'I0') and result.I0 is not None:
                guinier.i0 = float(result.I0)

            # Range start and end (indices converted back to q values in original units)
            if hasattr(result, 'start_point') and result.start_point is not None:
                start_idx = int(result.start_point)
                guinier.start_point = start_idx
                if 0 <= start_idx < len(q_valid):
                    # Return q in original units
                    guinier.range_start = float(q_valid[start_idx])

            if hasattr(result, 'end_point') and result.end_point is not None:
                end_idx = int(result.end_point)
                guinier.end_point = end_idx
                if 0 <= end_idx < len(q_valid):
                    # Return q in original units
                    guinier.range_end = float(q_valid[end_idx])

            # Only return if we got at least Rg
            if guinier.rg is not None:
                return guinier

        except Exception as e:
            logger.warning(f"FreeSAS auto_guinier failed: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None

        return None

    def create_default_project(self) -> SASBDBProject:
        """
        Create a default project structure
        
        :return: SASBDBProject with default values
        """
        return SASBDBProject(published=False, project_title="Untitled Project")

    def create_default_molecule(self) -> SASBDBMolecule:
        """
        Create a default molecule structure
        
        :return: SASBDBMolecule with default values
        """
        molecule = SASBDBMolecule()
        molecule.type = "Protein"
        molecule.molecule_source = "Biological"
        molecule.oligomeric_state = "monomer"
        molecule.number_of_molecules = 1
        return molecule

    def create_default_buffer(self) -> SASBDBBuffer:
        """
        Create a default buffer structure
        
        :return: SASBDBBuffer with default values
        """
        buffer = SASBDBBuffer()
        buffer.description = "Not specified"
        buffer.ph = 7.0
        return buffer

