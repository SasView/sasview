"""
Export functionality for SASBDB format.

This module provides functionality to export SASBDB data structures to JSON
format suitable for submission to the Small Angle Scattering Biological Data
Bank. The SASBDBExporter class handles:

- Converting SASBDBExportData objects to dictionary format
- Serializing to JSON with proper formatting
- Cleaning None values from the output

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
        return asdict(self.export_data)

    def export_to_json(self, filepath: str) -> bool:
        """
        Export data to JSON file.

        Failures such as a missing directory or unserialisable values are
        raised to the caller. The method does not turn them into ``False``.

        :param filepath: Path to save JSON file
        :return: True when the file has been written
        :raises OSError: when the file cannot be created
        :raises TypeError: when the export data cannot be serialised
        """
        data_dict = self.to_dict()
        cleaned_dict = self._remove_none_values(data_dict)

        with open(filepath, 'w', encoding='utf-8') as handle:
            json.dump(cleaned_dict, handle, indent=2, ensure_ascii=False)

        logger.info("SASBDB data exported to %s", filepath)
        return True

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

