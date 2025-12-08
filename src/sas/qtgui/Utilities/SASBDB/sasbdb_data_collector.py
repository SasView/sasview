"""
Data collector for SASBDB export

This module collects available data from SasView data objects, fit results,
and metadata to populate SASBDB export structures.
"""
import logging
from datetime import datetime
from typing import Optional

from sas.qtgui.Plotting.PlotterData import Data1D, Data2D
from sas.qtgui.Utilities.SASBDB.sasbdb_data import (
    SASBDBExportData,
    SASBDBProject,
    SASBDBSample,
    SASBDBMolecule,
    SASBDBBuffer,
    SASBDBGuinier,
    SASBDBPDDF,
    SASBDBInstrument,
    SASBDBFit,
    SASBDBModel,
)

try:
    from sas.system.version import __version__ as SASVIEW_VERSION
except ImportError:
    SASVIEW_VERSION = "unknown"

logger = logging.getLogger(__name__)


class SASBDBDataCollector:
    """
    Collects data from SasView for SASBDB export
    """
    
    def __init__(self):
        """Initialize the collector"""
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
            
            # Try to extract common metadata fields
            if 'experiment_date' in meta:
                sample.experiment_date = str(meta['experiment_date'])
            elif 'date' in meta:
                sample.experiment_date = str(meta['date'])
            
            if 'beamline' in meta:
                sample.beamline_instrument = str(meta['beamline'])
            elif 'instrument' in meta:
                sample.beamline_instrument = str(meta['instrument'])
            
            if 'concentration' in meta:
                try:
                    sample.concentration = float(meta['concentration'])
                except (ValueError, TypeError):
                    pass
            
            if 'molecular_weight' in meta or 'mw' in meta:
                try:
                    mw_key = 'molecular_weight' if 'molecular_weight' in meta else 'mw'
                    sample.experimental_molecular_weight = float(meta[mw_key])
                except (ValueError, TypeError):
                    pass
            
            if 'exposure_time' in meta:
                try:
                    sample.exposure_time = float(meta['exposure_time'])
                except (ValueError, TypeError):
                    pass
            
            if 'number_of_frames' in meta or 'frames' in meta:
                try:
                    frames_key = 'number_of_frames' if 'number_of_frames' in meta else 'frames'
                    sample.number_of_frames = int(meta[frames_key])
                except (ValueError, TypeError):
                    pass
        
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
            
            # Common metadata keys for instrument information
            if 'instrument' in meta and not instrument.beamline_name:
                instrument.beamline_name = str(meta['instrument'])
                has_instrument_data = True
            
            if 'beamline' in meta and not instrument.beamline_name:
                instrument.beamline_name = str(meta['beamline'])
                has_instrument_data = True
            
            if 'facility' in meta and not instrument.synchrotron_name:
                instrument.synchrotron_name = str(meta['facility'])
                has_instrument_data = True
            
            if 'synchrotron' in meta and not instrument.synchrotron_name:
                instrument.synchrotron_name = str(meta['synchrotron'])
                has_instrument_data = True
            
            if 'detector' in meta and not instrument.detector_manufacturer:
                instrument.detector_manufacturer = str(meta['detector'])
                has_instrument_data = True
            
            if 'city' in meta:
                instrument.city = str(meta['city'])
                has_instrument_data = True
            
            if 'country' in meta:
                instrument.country = str(meta['country'])
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
        :param optimizer_name: Name of the optimizer used
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
    
    def collect_guinier_from_linear_fit(self, rg: float, i0: float = None, 
                                         range_start: float = None, 
                                         range_end: float = None) -> SASBDBGuinier:
        """
        Collect Guinier analysis results
        
        :param rg: Radius of gyration in nm
        :param i0: Forward scattering intensity
        :param range_start: Start of Guinier range
        :param range_end: End of Guinier range
        :return: SASBDBGuinier object
        """
        guinier = SASBDBGuinier()
        guinier.rg = rg
        guinier.i0 = i0
        guinier.range_start = range_start
        guinier.range_end = range_end
        return guinier
    
    def collect_guinier_from_freesas(self, data) -> SASBDBGuinier | None:
        """
        Collect Guinier analysis results using FreeSAS auto_guinier
        
        :param data: Data1D object with x (q), y (I), and dy (errors)
        :return: SASBDBGuinier object or None if analysis fails
        """
        try:
            from freesas.autorg import auto_guinier
            import numpy as np
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
        
        # Determine unit conversion - FreeSAS expects q in nm^-1
        # Check if data is in 1/A (Angstrom^-1) and convert to nm^-1
        # 1 A^-1 = 10 nm^-1
        unit_conversion = 1.0
        if hasattr(data, 'get_xaxis'):
            try:
                xaxis_label, xaxis_units = data.get_xaxis()
                xaxis_label = str(xaxis_label) if xaxis_label else ''
                xaxis_units = str(xaxis_units) if xaxis_units else ''
                if 'A^{-1}' in xaxis_label or 'A^-1' in xaxis_label or 'A^{-1}' in xaxis_units or 'A^-1' in xaxis_units:
                    # Data is in 1/A, convert to 1/nm
                    unit_conversion = 10.0
            except (AttributeError, TypeError, ValueError):
                # Fallback: check _xunit attribute if available
                if hasattr(data, '_xunit'):
                    xunit = str(data._xunit)
                    if 'A^{-1}' in xunit or 'A^-1' in xunit:
                        unit_conversion = 10.0
        
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
                if 0 <= start_idx < len(q_valid):
                    # Return q in original units
                    guinier.range_start = float(q_valid[start_idx])
            
            if hasattr(result, 'end_point') and result.end_point is not None:
                end_idx = int(result.end_point)
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
    
    def collect_pddf_from_corfunc(self, dmax: float = None, rg: float = None,
                                   i0: float = None, porod_volume: float = None,
                                   software: str = "ATSAS") -> SASBDBPDDF:
        """
        Collect PDDF information from Corfunc analysis
        
        :param dmax: Maximum distance in nm
        :param rg: Radius of gyration from PDDF in nm
        :param i0: Forward scattering intensity
        :param porod_volume: Porod volume in nm^3
        :param software: Software used for PDDF calculation
        :return: SASBDBPDDF object
        """
        pddf = SASBDBPDDF()
        pddf.software = software
        pddf.dmax = dmax
        pddf.rg = rg
        pddf.i0 = i0
        pddf.porod_volume = porod_volume
        return pddf
    
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
    
    def create_default_instrument(self) -> SASBDBInstrument:
        """
        Create a default instrument structure
        
        :return: SASBDBInstrument with default values
        """
        instrument = SASBDBInstrument()
        instrument.source_type = "X-ray synchrotron"
        return instrument

