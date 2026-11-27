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
import re

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

# Unit strings that loaders may declare alongside a value.
ANGSTROM_UNITS = frozenset({'a', 'ang', 'angstrom', 'angstroms',
                            '\u00c5', '\u212b'})
NANOMETRE_UNITS = frozenset({'nm', 'nanometer', 'nanometre',
                             'nanometers', 'nanometres'})
KELVIN_UNITS = frozenset({'k', 'kelvin'})
CELSIUS_UNITS = frozenset({'c', 'degc', 'degreec', 'celsius', '\u00b0c'})
METRE_UNITS = frozenset({'m', 'meter', 'metre', 'meters', 'metres'})
MILLIMETRE_UNITS = frozenset({
    'mm', 'millimeter', 'millimetre', 'millimeters', 'millimetres'})
CENTIMETRE_UNITS = frozenset({
    'cm', 'centimeter', 'centimetre', 'centimeters', 'centimetres'})

ANGSTROM_PER_NM = 10.0
KELVIN_OFFSET = 273.15
_BUFFER_PH = re.compile(r'\(pH\s*([0-9]*\.?[0-9]+)\)\s*$', re.IGNORECASE)
# Thresholds for the magnitude heuristics used when no unit is declared.
WAVELENGTH_ANGSTROM_THRESHOLD_NM = 1.0
TEMPERATURE_KELVIN_THRESHOLD_C = 100.0


def _declared_unit(obj: object, attribute: str) -> str | None:
    """
    Return the normalised unit string declared on an object, if any.

    :param obj: Object that may carry a ``*_unit`` attribute
    :param attribute: Name of the unit attribute to read
    :return: Lower-case unit string without spaces, or None if the object
        declares no usable unit
    """
    unit = getattr(obj, attribute, None)
    if not isinstance(unit, str):
        return None
    return unit.strip().lower().replace(' ', '') or None


def _wavelength_in_nm(wavelength: float, unit: str | None) -> float:
    """
    Convert a wavelength to nanometres.

    The declared unit is used when it is recognised. Otherwise the value is
    assumed to be in Angstrom when it exceeds
    ``WAVELENGTH_ANGSTROM_THRESHOLD_NM``; that guess can be wrong for, e.g.,
    long-wavelength neutrons quoted in nm.

    :param wavelength: Wavelength value as stored in the data object
    :param unit: Normalised unit string, or None if unknown
    :return: Wavelength in nm
    """
    if unit in NANOMETRE_UNITS:
        return wavelength
    if unit in ANGSTROM_UNITS:
        return wavelength / ANGSTROM_PER_NM
    if unit is not None:
        logger.debug("Unrecognised wavelength unit '%s'; "
                     "falling back to magnitude heuristic", unit)
    if wavelength > WAVELENGTH_ANGSTROM_THRESHOLD_NM:
        return wavelength / ANGSTROM_PER_NM
    return wavelength


def _temperature_in_celsius(temperature: float, unit: str | None) -> float:
    """
    Convert a temperature to degrees Celsius.

    The declared unit is used when it is recognised. Otherwise the value is
    assumed to be in Kelvin when it exceeds
    ``TEMPERATURE_KELVIN_THRESHOLD_C``; that guess can be wrong for, e.g.,
    cryogenic storage temperatures quoted in Kelvin below 100 K.

    :param temperature: Temperature value as stored in the data object
    :param unit: Normalised unit string, or None if unknown
    :return: Temperature in degrees Celsius
    """
    if unit in CELSIUS_UNITS:
        return temperature
    if unit in KELVIN_UNITS:
        return temperature - KELVIN_OFFSET
    if unit is not None:
        logger.debug("Unrecognised temperature unit '%s'; "
                     "falling back to magnitude heuristic", unit)
    if temperature > TEMPERATURE_KELVIN_THRESHOLD_C:
        return temperature - KELVIN_OFFSET
    return temperature


def _distance_in_m(distance: float, unit: str | None) -> float:
    """
    Convert a sample-to-detector distance to metres.

    A declared unit is used when it is recognised. sasdata stores this
    distance in millimetres unless ``distance_unit`` says otherwise, so a
    missing or unrecognised unit is treated as millimetres.

    :param distance: Distance value as stored on the detector
    :param unit: Normalised unit string, or None if unknown
    :return: Distance in metres
    """
    if unit in METRE_UNITS:
        return distance
    if unit in CENTIMETRE_UNITS:
        return distance / 100.0
    if unit in MILLIMETRE_UNITS:
        return distance / 1000.0
    if unit is not None:
        logger.debug("Unrecognised distance unit '%s'; assuming mm", unit)
    return distance / 1000.0


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
        "1/A",
        "1/a",
        "\u00c5^{-1}",  # Å^{-1} (Latin-1 capital A with ring)
        "\u00c5^-1",
        "\u00c5-1",
        "\u212b^{-1}",  # ANGSTROM SIGN U+212B
        "1/\u00c5",
        "1/\u212b",
    )
    return any(m in text for m in markers)


def _angular_units_from_label(text: str | None) -> str:
    """
    Map an x-axis label or unit string to a SASBDB angular-unit token.

    Recognises the same inverse-Angstrom spellings as Guinier scaling,
    including Unicode Å. A bare letter ``A`` is not enough: ``Arbitrary``
    must stay arbitrary.

    :param text: Axis label, unit string, or both
    :return: ``1/A``, ``1/nm``, or ``arbitrary``
    """
    if not text:
        return 'arbitrary'
    if _x_axis_label_is_inverse_angstrom(text):
        return '1/A'
    compact = text.lower().replace(' ', '')
    if 'angstrom' in compact or 'ångström' in text.lower():
        return '1/A'
    if 'nm' in compact or 'nanomet' in compact:
        return '1/nm'
    return 'arbitrary'


def _detail_map(sample_obj: object) -> dict[str, str]:
    """
    Parse ``sample.details`` lines written by the SASBDB loader.

    Each line is ``Label: value``. Non-list details (for example a mock)
    are ignored.

    :param sample_obj: Data sample, or None
    :return: Lower-case label to value
    """
    details = getattr(sample_obj, 'details', None)
    if not isinstance(details, (list, tuple)):
        return {}
    parsed: dict[str, str] = {}
    for line in details:
        if not isinstance(line, str) or ':' not in line:
            continue
        label, value = line.split(':', 1)
        value = value.strip()
        if value:
            parsed[label.strip().lower()] = value
    return parsed


def _concentration_from_detail(text: str | None) -> float | None:
    """Return the leading number in a ``Concentration:`` detail line."""
    if not text:
        return None
    token = text.split()[0]
    try:
        return float(token)
    except ValueError:
        return None


def _split_molecule_detail(text: str) -> tuple[str, str | None]:
    """Split ``Lysozyme (Protein)`` into name and optional type."""
    if text.endswith(')') and ' (' in text:
        name, _, rest = text.rpartition(' (')
        mol_type = rest[:-1].strip() or None
        return name.strip(), mol_type
    return text.strip(), None


def _original_curve_point(valid_indices, q, filtered_index: int):
    """
    Map a FreeSAS index in the filtered curve back to the original curve.

    :param valid_indices: Indices of points passed to FreeSAS
    :param q: Original q array
    :param filtered_index: Index into the filtered array
    :return: ``(original_index, q_value)`` or None when the index is outside
        the filtered curve
    """
    if filtered_index < 0 or filtered_index >= len(valid_indices):
        return None
    original = int(valid_indices[filtered_index])
    return original, float(q[original])


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

        # Angular and intensity units. Share the Guinier axis check so
        # Unicode Å^{-1} is 1/A, while a bare "A" in "Arbitrary" is not.
        xunit = getattr(data, '_xunit', None)
        sample.angular_units = _angular_units_from_label(
            xunit if isinstance(xunit, str) else None)

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
                    sample.wavelength = _wavelength_in_nm(
                        wavelength,
                        _declared_unit(data.source, 'wavelength_unit'))

        if hasattr(data, 'detector') and data.detector and len(data.detector) > 0:
            detector = data.detector[0]
            distance = getattr(detector, 'distance', None)
            if isinstance(distance, (int, float)) and distance:
                sample.sample_detector_distance = _distance_in_m(
                    float(distance),
                    _declared_unit(detector, 'distance_unit'))

        if hasattr(data, 'sample') and data.sample:
            if hasattr(data.sample, 'temperature') and data.sample.temperature:
                sample.cell_temperature = _temperature_in_celsius(
                    data.sample.temperature,
                    _declared_unit(data.sample, 'temperature_unit'))

        # Extract metadata dictionary if available. Leave experiment_date
        # empty when the file does not declare one.
        raw_meta = getattr(data, 'meta_data', None)
        meta = raw_meta if isinstance(raw_meta, dict) else {}
        if meta:
            sample.experiment_date = _meta_str(meta, 'experiment_date', 'date')
            beamline = _meta_str(meta, 'beamline', 'instrument')
            if beamline:
                sample.beamline_instrument = beamline
            sample.concentration = _meta_float(meta, 'concentration')
            sample.experimental_molecular_weight = _meta_float(
                meta, 'molecular_weight', 'mw')
            sample.exposure_time = _meta_float(meta, 'exposure_time')
            sample.number_of_frames = _meta_int(meta, 'number_of_frames', 'frames')

        self._apply_downloaded_sasbdb(sample, meta, getattr(data, 'sample', None))

        # Also check data.instrument attribute (shown in info panel)
        if hasattr(data, 'instrument') and data.instrument and not sample.beamline_instrument:
            sample.beamline_instrument = str(data.instrument)

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
            # Source type comes from the radiation string. Every sasdata
            # Source has a name attribute, so that must not imply synchrotron.
            radiation = getattr(source, 'radiation', None)
            if isinstance(radiation, str) and radiation.strip():
                radiation_l = radiation.lower()
                if 'neutron' in radiation_l:
                    instrument.source_type = "Neutron source"
                elif 'x-ray' in radiation_l or 'xray' in radiation_l:
                    if 'synchrotron' in radiation_l:
                        instrument.source_type = "X-ray synchrotron"
                    else:
                        instrument.source_type = "X-ray in house"
                else:
                    instrument.source_type = "Other"
                has_instrument_data = True

            # Source name might contain synchrotron/facility info
            source_name = getattr(source, 'name', None)
            if isinstance(source_name, str) and source_name.strip():
                source_name = source_name.strip()
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

        valid_indices = np.flatnonzero(valid_mask)
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

            # FreeSAS indices refer to the filtered array passed in.
            # Store the matching index on the original curve.
            if hasattr(result, 'start_point') and result.start_point is not None:
                mapped = _original_curve_point(valid_indices, q, int(result.start_point))
                if mapped is not None:
                    guinier.start_point, guinier.range_start = mapped

            if hasattr(result, 'end_point') and result.end_point is not None:
                mapped = _original_curve_point(valid_indices, q, int(result.end_point))
                if mapped is not None:
                    guinier.end_point, guinier.range_end = mapped

            # Only return if we got at least Rg
            if guinier.rg is not None:
                return guinier

        except Exception as exc:
            logger.warning("FreeSAS auto_guinier failed: %s", exc)
            logger.debug("FreeSAS auto_guinier traceback", exc_info=True)
            return None

        return None

    def _apply_downloaded_sasbdb(self, sample: SASBDBSample, meta: dict,
                                 sample_obj: object) -> None:
        """
        Fill fields written by the SASBDB download loader.

        The loader stores molecular weight, Guinier results, and publication
        ids under ``SASBDB_*`` metadata keys, and writes concentration,
        buffer, and sequence into ``sample.details``. SASBDB reports Guinier
        Rg in nm, which is the unit ``SASBDBGuinier.rg`` uses.

        :param sample: Sample being filled
        :param meta: Data metadata dictionary; may be empty
        :param sample_obj: Underlying data sample, used for detail lines
        """
        details = _detail_map(sample_obj)
        if sample.experimental_molecular_weight is None:
            sample.experimental_molecular_weight = _meta_float(meta, 'SASBDB_MW')
        if sample.concentration is None:
            sample.concentration = _concentration_from_detail(
                details.get('concentration'))
        self._apply_downloaded_molecule(sample, meta, details)
        self._apply_downloaded_buffer(sample, details)
        self._apply_downloaded_guinier(sample, meta)
        self._apply_downloaded_publication(meta)

    def _apply_downloaded_molecule(self, sample: SASBDBSample, meta: dict,
                                   details: dict[str, str]) -> None:
        """Copy molecule fields from SASBDB metadata and detail lines."""
        long_name = _meta_str(meta, 'SASBDB_molecule')
        mol_type = _meta_str(meta, 'SASBDB_molecule_type')
        molecule_line = details.get('molecule')
        if molecule_line and not long_name:
            long_name, detail_type = _split_molecule_detail(molecule_line)
            mol_type = mol_type or detail_type
        sequence = details.get('sequence')
        uniprot = details.get('uniprot')
        organism = details.get('source organism')
        oligomer = _meta_str(meta, 'SASBDB_oligomeric_state') or details.get(
            'oligomerization')
        n_molecules = details.get('number of molecules')
        if not any((long_name, mol_type, sequence, uniprot, organism,
                    oligomer, n_molecules)):
            return
        molecule = sample.molecule or SASBDBMolecule()
        molecule.long_name = molecule.long_name or long_name
        molecule.type = molecule.type or mol_type
        molecule.fasta_sequence = molecule.fasta_sequence or sequence
        molecule.uniprot_accession = molecule.uniprot_accession or uniprot
        molecule.source_organism = molecule.source_organism or organism
        molecule.oligomeric_state = molecule.oligomeric_state or oligomer
        if molecule.number_of_molecules is None and n_molecules:
            try:
                molecule.number_of_molecules = int(float(n_molecules))
            except ValueError:
                logger.debug("Could not parse number of molecules '%s'",
                             n_molecules)
        sample.molecule = molecule

    def _apply_downloaded_buffer(self, sample: SASBDBSample,
                                 details: dict[str, str]) -> None:
        """Copy buffer description and pH from a loader detail line."""
        buffer_line = details.get('buffer')
        if not buffer_line:
            return
        description = buffer_line
        ph = None
        match = _BUFFER_PH.search(buffer_line)
        if match:
            description = buffer_line[:match.start()].strip()
            try:
                ph = float(match.group(1))
            except ValueError:
                ph = None
        buffer = sample.buffer or SASBDBBuffer()
        buffer.description = buffer.description or description or None
        if buffer.ph is None:
            buffer.ph = ph
        sample.buffer = buffer

    def _apply_downloaded_guinier(self, sample: SASBDBSample, meta: dict) -> None:
        """Copy Guinier Rg (nm) and I(0) stored by the SASBDB loader."""
        rg = _meta_float(meta, 'SASBDB_Rg')
        i0 = _meta_float(meta, 'SASBDB_I0')
        if rg is None and i0 is None:
            return
        guinier = sample.guinier or SASBDBGuinier()
        if guinier.rg is None:
            guinier.rg = rg
        if guinier.rg_error is None:
            guinier.rg_error = _meta_float(meta, 'SASBDB_Rg_error')
        if guinier.i0 is None:
            guinier.i0 = i0
        sample.guinier = guinier

    def _apply_downloaded_publication(self, meta: dict) -> None:
        """Copy DOI and PubMed id onto the export project."""
        doi = _meta_str(meta, 'SASBDB_DOI')
        pmid = _meta_str(meta, 'SASBDB_PMID')
        if not doi and not pmid:
            return
        if self.export_data.project is None:
            self.export_data.project = SASBDBProject(published=True)
        project = self.export_data.project
        if doi and not project.doi:
            project.doi = doi
        if pmid and not project.pubmed_pmid:
            project.pubmed_pmid = pmid
        if project.doi or project.pubmed_pmid:
            project.published = True

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

