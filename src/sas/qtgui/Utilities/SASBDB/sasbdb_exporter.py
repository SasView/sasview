"""
Export functionality for SASBDB format.

This module provides functionality to export SASBDB data structures to JSON
format suitable for submission to the Small Angle Scattering Biological Data
Bank. The SASBDBExporter class handles:

- Converting SASBDBExportData objects to dictionary format
- Serializing to JSON with proper formatting
- Cleaning None values from the output
- Exporting experimental data files (.dat format)

The exporter ensures that the output JSON follows SASBDB submission format
requirements and produces clean, well-formatted files.
"""
import json
import logging
import os
from typing import Optional

from sas.qtgui.Utilities.SASBDB.sasbdb_data import SASBDBExportData

logger = logging.getLogger(__name__)


class SASBDBExporter:
    """
    Exports SASBDB data to JSON format.
    
    This class handles the conversion and export of SASBDBExportData objects
    to JSON files. It provides methods to:
    
    - Convert data structures to dictionary format
    - Remove None values for cleaner JSON output
    - Export to JSON files with proper formatting
    - Export experimental data to .dat files
    
    The exporter ensures that the output conforms to SASBDB submission
    format requirements.
    
    :param export_data: SASBDBExportData object containing all data to export
    """
    
    def __init__(self, export_data: SASBDBExportData):
        """
        Initialize exporter with data to export.
        
        :param export_data: SASBDBExportData object containing all data to export
        """
        self.export_data = export_data
    
    def to_dict(self) -> dict:
        """
        Convert SASBDBExportData to dictionary for JSON serialization
        
        :return: Dictionary representation of the export data
        """
        result = {}
        
        # Project information
        if self.export_data.project:
            result['project'] = {
                'published': self.export_data.project.published,
                'pubmed_pmid': self.export_data.project.pubmed_pmid,
                'doi': self.export_data.project.doi,
                'project_title': self.export_data.project.project_title,
            }
        
        # Samples
        result['samples'] = []
        for sample in self.export_data.samples:
            sample_dict = {
                'sample_title': sample.sample_title,
                'curve_type': sample.curve_type,
                'experimental_curve': sample.experimental_curve,
                'angular_units': sample.angular_units,
                'intensity_units': sample.intensity_units,
                'experimental_molecular_weight': sample.experimental_molecular_weight,
                'molecular_weight_from_i0': sample.molecular_weight_from_i0,
                'molecular_weight_from_i0_error': sample.molecular_weight_from_i0_error,
                'description': sample.description,
                'experiment_date': sample.experiment_date,
                'beamline_instrument': sample.beamline_instrument,
                'wavelength': sample.wavelength,
                'sample_detector_distance': sample.sample_detector_distance,
                'cell_temperature': sample.cell_temperature,
                'storage_temperature': sample.storage_temperature,
                'exposure_time': sample.exposure_time,
                'number_of_frames': sample.number_of_frames,
                'concentration': sample.concentration,
            }
            
            # Molecule
            if sample.molecule:
                sample_dict['molecule'] = {
                    'type': sample.molecule.type,
                    'uniprot_accession': sample.molecule.uniprot_accession,
                    'uniprot_range_from': sample.molecule.uniprot_range_from,
                    'uniprot_range_to': sample.molecule.uniprot_range_to,
                    'molecule_source': sample.molecule.molecule_source,
                    'long_name': sample.molecule.long_name,
                    'short_name': sample.molecule.short_name,
                    'source_organism': sample.molecule.source_organism,
                    'fasta_sequence': sample.molecule.fasta_sequence,
                    'monomer_mw_kda': sample.molecule.monomer_mw_kda,
                    'oligomeric_state': sample.molecule.oligomeric_state,
                    'number_of_molecules': sample.molecule.number_of_molecules,
                    'total_mw_kda': sample.molecule.total_mw_kda,
                    'molecule_description': sample.molecule.molecule_description,
                }
            
            # Buffer
            if sample.buffer:
                sample_dict['buffer'] = {
                    'description': sample.buffer.description,
                    'ph': sample.buffer.ph,
                    'comment': sample.buffer.comment,
                }
            
            # Guinier
            if sample.guinier:
                sample_dict['guinier'] = {
                    'rg': sample.guinier.rg,
                    'rg_error': sample.guinier.rg_error,
                    'i0': sample.guinier.i0,
                    'range_start': sample.guinier.range_start,
                    'range_end': sample.guinier.range_end,
                }
            
            # PDDF
            if sample.pddf:
                sample_dict['pddf'] = {
                    'software': sample.pddf.software,
                    'software_version': sample.pddf.software_version,
                    'pddf_file': sample.pddf.pddf_file,
                    'dmax': sample.pddf.dmax,
                    'dmax_error': sample.pddf.dmax_error,
                    'rg': sample.pddf.rg,
                    'rg_error': sample.pddf.rg_error,
                    'i0': sample.pddf.i0,
                    'porod_volume': sample.pddf.porod_volume,
                    'mw_from_porod_volume': sample.pddf.mw_from_porod_volume,
                }
            
            # Fits
            sample_dict['fits'] = []
            for fit in sample.fits:
                fit_dict = {
                    'software': fit.software,
                    'software_version': fit.software_version,
                    'fit_data': fit.fit_data,
                    'angular_units': fit.angular_units,
                    'chi_squared': fit.chi_squared,
                    'cormap_pvalue': fit.cormap_pvalue,
                    'log_file': fit.log_file,
                    'description': fit.description,
                }
                
                # Models
                fit_dict['models'] = []
                for model in fit.models:
                    model_dict = {
                        'software_or_db': model.software_or_db,
                        'software_version': model.software_version,
                        'model_data': model.model_data,
                        'symmetry': model.symmetry,
                        'log': model.log,
                        'comment': model.comment,
                    }
                    fit_dict['models'].append(model_dict)
                
                sample_dict['fits'].append(fit_dict)
            
            result['samples'].append(sample_dict)
        
        # Instruments
        result['instruments'] = []
        for instrument in self.export_data.instruments:
            instrument_dict = {
                'source_type': instrument.source_type,
                'beamline_name': instrument.beamline_name,
                'synchrotron_name': instrument.synchrotron_name,
                'detector_manufacturer': instrument.detector_manufacturer,
                'detector_type': instrument.detector_type,
                'detector_resolution': instrument.detector_resolution,
                'city': instrument.city,
                'country': instrument.country,
            }
            result['instruments'].append(instrument_dict)
        
        return result
    
    def export_to_json(self, filepath: str) -> bool:
        """
        Export data to JSON file
        
        :param filepath: Path to save JSON file
        :return: True if successful, False otherwise
        """
        try:
            data_dict = self.to_dict()
            
            # Remove None values for cleaner JSON
            cleaned_dict = self._remove_none_values(data_dict)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(cleaned_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"SASBDB data exported to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export SASBDB data: {e}")
            return False
    
    def _remove_none_values(self, d: dict) -> dict:
        """
        Recursively remove None values from dictionary
        
        :param d: Dictionary to clean
        :return: Cleaned dictionary
        """
        if not isinstance(d, dict):
            return d
        
        result = {}
        for key, value in d.items():
            if value is None:
                continue
            elif isinstance(value, dict):
                cleaned = self._remove_none_values(value)
                if cleaned:  # Only add if not empty
                    result[key] = cleaned
            elif isinstance(value, list):
                cleaned_list = []
                for item in value:
                    if isinstance(item, dict):
                        cleaned_item = self._remove_none_values(item)
                        if cleaned_item:
                            cleaned_list.append(cleaned_item)
                    elif item is not None:
                        cleaned_list.append(item)
                if cleaned_list:
                    result[key] = cleaned_list
            else:
                result[key] = value
        
        return result
    
    def export_experimental_data(self, data, filepath: str) -> bool:
        """
        Export experimental data to .dat file
        
        :param data: Data1D or Data2D object
        :param filepath: Path to save .dat file
        :return: True if successful, False otherwise
        """
        try:
            from sas.qtgui.Plotting.PlotterData import Data1D, Data2D
            
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write header
                f.write("# SASBDB Experimental Data Export\n")
                if hasattr(data, 'name'):
                    f.write(f"# Sample: {data.name}\n")
                if hasattr(data, 'filename'):
                    f.write(f"# File: {data.filename}\n")
                f.write("#\n")
                
                if isinstance(data, Data1D):
                    # Write 1D data
                    f.write("# Q\tI\tdI\n")
                    for i in range(len(data.x)):
                        q = data.x[i]
                        i_val = data.y[i] if i < len(data.y) else 0
                        di = data.dy[i] if hasattr(data, 'dy') and i < len(data.dy) else 0
                        f.write(f"{q}\t{i_val}\t{di}\n")
                elif isinstance(data, Data2D):
                    # Write 2D data header
                    f.write("# Qx\tQy\tI\tdI\n")
                    # For 2D, we'd need to flatten or sample the data
                    # This is a simplified version
                    if hasattr(data, 'qx_data') and hasattr(data, 'qy_data'):
                        qx = data.qx_data
                        qy = data.qy_data
                        i_data = data.data if hasattr(data, 'data') else None
                        err_data = data.err_data if hasattr(data, 'err_data') else None
                        
                        for i in range(min(len(qx), len(qy))):
                            qx_val = qx[i]
                            qy_val = qy[i]
                            i_val = i_data[i] if i_data is not None and i < len(i_data) else 0
                            di = err_data[i] if err_data is not None and i < len(err_data) else 0
                            f.write(f"{qx_val}\t{qy_val}\t{i_val}\t{di}\n")
            
            logger.info(f"Experimental data exported to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export experimental data: {e}")
            return False

