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
from dataclasses import asdict

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
        result = asdict(self.export_data)
        for sample in result.get('samples', []):
            for fit in sample.get('fits', []):
                for model in fit.get('models', []):
                    model.pop('visualization_params', None)
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

            if not isinstance(data, (Data1D, Data2D)):
                logger.error(
                    "export_experimental_data requires Data1D or Data2D, got %s",
                    type(data).__name__,
                )
                return False

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

