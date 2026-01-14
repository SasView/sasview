"""
SASBDB REST API client module.

Provides functions to interact with the SASBDB REST API for downloading
datasets and retrieving metadata.
"""

import logging
import os
import tempfile
from dataclasses import dataclass, field
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# Base API URL - SASBDB REST API
SASBDB_API_BASE = "https://www.sasbdb.org/rest-api"


@dataclass
class SASBDBDatasetInfo:
    """
    Parsed metadata from a SASBDB dataset entry.
    
    Contains key information extracted from the SASBDB REST API response.
    """
    # Identifiers
    entry_id: str = ""
    code: str = ""
    title: str = ""
    
    # Sample information
    sample_name: str = ""
    sample_description: str = ""
    concentration: Optional[float] = None
    concentration_unit: str = "mg/mL"
    
    # Molecule information
    molecule_name: str = ""
    molecule_type: str = ""
    molecular_weight: Optional[float] = None  # Experimental MW in kDa
    molecular_weight_method: str = ""
    oligomeric_state: str = ""
    
    # Buffer information
    buffer_description: str = ""
    ph: Optional[float] = None
    
    # Experimental parameters
    instrument: str = ""
    detector: str = ""
    wavelength: Optional[float] = None  # in Angstrom
    wavelength_unit: str = "Å"
    temperature: Optional[float] = None  # in Kelvin or Celsius
    temperature_unit: str = "K"
    
    # Analysis results
    rg: Optional[float] = None  # Radius of gyration in Angstrom
    rg_error: Optional[float] = None
    i0: Optional[float] = None  # I(0)
    i0_error: Optional[float] = None
    dmax: Optional[float] = None  # Maximum dimension in Angstrom
    porod_volume: Optional[float] = None
    
    # Q-range
    q_min: Optional[float] = None
    q_max: Optional[float] = None
    
    # Publication
    publication_title: str = ""
    publication_doi: str = ""
    publication_pmid: str = ""
    authors: list = field(default_factory=list)
    
    # Data files
    intensities_data_url: str = ""
    pddf_data_url: str = ""
    
    # Raw metadata for additional fields
    raw_metadata: dict = field(default_factory=dict)


def parseMetadata(metadata: dict) -> SASBDBDatasetInfo:
    """
    Parse SASBDB API response into a structured SASBDBDatasetInfo object.
    
    :param metadata: Raw JSON dictionary from SASBDB API
    :return: Parsed SASBDBDatasetInfo object
    """
    info = SASBDBDatasetInfo()
    
    if not isinstance(metadata, dict):
        return info
    
    # Store raw metadata for reference
    info.raw_metadata = metadata
    
    # Log top-level keys for debugging
    logger.debug(f"SASBDB API response keys: {list(metadata.keys())}")
    
    # Identifiers
    info.entry_id = _get_str(metadata, 'id', 'entry_id', 'sasbdb_id')
    info.code = _get_str(metadata, 'code', 'accession_code', 'entry_code')
    info.title = _get_str(metadata, 'title', 'entry_title', 'sample_title')
    
    # Sample information - try more variations
    info.sample_name = _get_str(metadata, 'sample_name', 'sample', 'name', 'sample_name_full')
    info.sample_description = _get_str(metadata, 'sample_description', 'description', 'sample_description_full')
    info.concentration = _get_float(metadata, 'concentration', 'sample_concentration', 'conc', 'sample_conc')
    info.concentration_unit = _get_str(metadata, 'concentration_unit', 'conc_unit', 'concentration_units') or "mg/mL"
    
    # Molecule information - try more variations
    info.molecule_name = _get_str(metadata, 'molecule_name', 'macromolecule_name', 'protein_name', 
                                  'molecule', 'macromolecule', 'protein', 'name')
    info.molecule_type = _get_str(metadata, 'molecule_type', 'macromolecule_type', 'sample_type',
                                  'type', 'molecule_type_full')
    info.molecular_weight = _get_float(metadata, 'molecular_weight', 'mw', 'exp_mw', 
                                        'experimental_mw', 'mw_kda')
    info.molecular_weight_method = _get_str(metadata, 'mw_method', 'molecular_weight_method')
    info.oligomeric_state = _get_str(metadata, 'oligomeric_state', 'oligomer_state', 'oligomerization')
    
    # Buffer information
    info.buffer_description = _get_str(metadata, 'buffer', 'buffer_description', 'buffer_composition')
    info.ph = _get_float(metadata, 'ph', 'buffer_ph')
    
    # Experimental parameters
    info.instrument = _get_str(metadata, 'instrument', 'beamline', 'instrument_name')
    info.detector = _get_str(metadata, 'detector', 'detector_name', 'detector_type')
    info.wavelength = _get_float(metadata, 'wavelength', 'xray_wavelength', 'neutron_wavelength')
    info.temperature = _get_float(metadata, 'temperature', 'sample_temperature', 'temp')
    
    # Analysis results - Guinier
    info.rg = _get_float(metadata, 'rg', 'radius_of_gyration', 'guinier_rg')
    info.rg_error = _get_float(metadata, 'rg_error', 'rg_err', 'guinier_rg_error')
    info.i0 = _get_float(metadata, 'i0', 'i_zero', 'guinier_i0')
    info.i0_error = _get_float(metadata, 'i0_error', 'i0_err', 'guinier_i0_error')
    
    # Analysis results - P(r)
    info.dmax = _get_float(metadata, 'dmax', 'd_max', 'maximum_dimension')
    info.porod_volume = _get_float(metadata, 'porod_volume', 'volume', 'porod_vol')
    
    # Q-range
    info.q_min = _get_float(metadata, 'q_min', 'qmin', 's_min', 'smin')
    info.q_max = _get_float(metadata, 'q_max', 'qmax', 's_max', 'smax')
    
    # Publication
    info.publication_title = _get_str(metadata, 'publication_title', 'pub_title', 'paper_title')
    info.publication_doi = _get_str(metadata, 'doi', 'publication_doi', 'pub_doi')
    info.publication_pmid = _get_str(metadata, 'pmid', 'publication_pmid', 'pubmed_id')
    
    # Authors
    authors = metadata.get('authors') or metadata.get('author_list') or []
    if isinstance(authors, list):
        info.authors = [str(a) for a in authors]
    elif isinstance(authors, str):
        info.authors = [authors]
    
    # Data file URLs
    info.intensities_data_url = _get_str(metadata, 'intensities_data', 'data_url', 'intensities_url')
    info.pddf_data_url = _get_str(metadata, 'pddf_data', 'pddf_url', 'pr_data')
    
    return info


def _get_str(data: dict, *keys: str) -> str:
    """
    Get string value from dictionary, trying multiple possible keys.
    Also searches in nested dictionaries (sample, molecule, experiment, etc.).
    
    :param data: Dictionary to search
    :param keys: Possible key names to try
    :return: String value or empty string if not found
    """
    # First try top-level keys
    for key in keys:
        if key in data and data[key] is not None:
            return str(data[key])
    
    # Then search in common nested structures
    nested_paths = ['sample', 'molecule', 'experiment', 'experimental', 'metadata', 'info']
    for path in nested_paths:
        if path in data and isinstance(data[path], dict):
            for key in keys:
                if key in data[path] and data[path][key] is not None:
                    return str(data[path][key])
    
    return ""


def _get_float(data: dict, *keys: str) -> Optional[float]:
    """
    Get float value from dictionary, trying multiple possible keys.
    Also searches in nested dictionaries (sample, molecule, experiment, etc.).
    
    :param data: Dictionary to search
    :param keys: Possible key names to try
    :return: Float value or None if not found
    """
    # First try top-level keys
    for key in keys:
        if key in data and data[key] is not None:
            try:
                return float(data[key])
            except (ValueError, TypeError):
                continue
    
    # Then search in common nested structures
    nested_paths = ['sample', 'molecule', 'experiment', 'experimental', 'metadata', 'info']
    for path in nested_paths:
        if path in data and isinstance(data[path], dict):
            for key in keys:
                if key in data[path] and data[path][key] is not None:
                    try:
                        return float(data[path][key])
                    except (ValueError, TypeError):
                        continue
    
    return None


def getDatasetMetadata(dataset_id: str) -> Optional[dict]:
    """
    Fetch dataset metadata from SASBDB API.
    
    :param dataset_id: SASBDB dataset identifier (e.g., "SASDN24" - full 7-character ID)
    :return: Dictionary containing dataset metadata, or None if error
    """
    # Normalize dataset ID (uppercase, strip whitespace, ensure 7 characters)
    normalized_id = _normalizeDatasetId(dataset_id)
    if not normalized_id:
        logger.error(f"Invalid dataset ID format: {dataset_id}")
        return None
    
    # Use the correct REST API endpoint: /rest-api/entry/summary/{id}/
    endpoint = f"{SASBDB_API_BASE}/entry/summary/{normalized_id}/"
    
    try:
        logger.info(f"Fetching dataset metadata from: {endpoint}")
        headers = {"accept": "application/json"}
        response = requests.get(endpoint, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse JSON response
        metadata = response.json()
        logger.info(f"Successfully retrieved metadata for dataset {normalized_id}")
        return metadata
                
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.error(f"Dataset {normalized_id} not found (404)")
        else:
            logger.error(f"HTTP error fetching dataset {normalized_id}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching dataset {normalized_id}: {e}")
        return None
    except ValueError as e:
        logger.error(f"Invalid JSON response for dataset {normalized_id}: {e}")
        return None


def getDataFileUrl(metadata: dict) -> Optional[str]:
    """
    Extract data file URL from dataset metadata.
    
    Looks for common field names in the metadata JSON that might contain
    the data file URL or path. Also checks for SASBDB-specific fields.
    
    :param metadata: Dictionary containing dataset metadata
    :return: URL string for the data file, or None if not found
    """
    if not isinstance(metadata, dict):
        return None
    
    # SASBDB-specific field names that might contain data file URLs
    # Priority: intensities_data is the primary field for SASBDB
    possible_fields = [
        # SASBDB primary data field
        'intensities_data',
        'intensitiesData',
        # Direct URL fields
        'data_file_url',
        'dataFileUrl',
        'data_file',
        'dataFile',
        'scattering_data_url',
        'scatteringDataUrl',
        'experimental_data_url',
        'experimentalDataUrl',
        'download_url',
        'downloadUrl',
        'file_url',
        'fileUrl',
        # File list fields
        'files',
        'data_files',
        'dataFiles',
        'experimental_files',
        'scattering_files',
        # SASBDB API specific fields
        'experimental_data',
        'experimentalData',
        'scattering_data',
        'scatteringData',
    ]
    
    # Check top-level fields
    for field in possible_fields:
        if field in metadata:
            value = metadata[field]
            if isinstance(value, str) and (value.startswith('http') or value.startswith('/')):
                # If relative URL, make it absolute
                if value.startswith('/'):
                    return f"https://www.sasbdb.org{value}"
                return value
            elif isinstance(value, list) and len(value) > 0:
                # If it's a list, take the first item
                first_item = value[0]
                if isinstance(first_item, str):
                    if first_item.startswith('/'):
                        return f"https://www.sasbdb.org{first_item}"
                    elif first_item.startswith('http'):
                        return first_item
                elif isinstance(first_item, dict):
                    # Check for 'url' or 'path' in the item
                    for url_field in ['url', 'path', 'file', 'file_url', 'download_url']:
                        if url_field in first_item:
                            url = first_item[url_field]
                            if isinstance(url, str):
                                if url.startswith('/'):
                                    return f"https://www.sasbdb.org{url}"
                                elif url.startswith('http'):
                                    return url
    
    # Check nested structures (common in REST APIs)
    for nested_key in ['entry', 'data', 'files', 'experimental_data', 'scattering_data']:
        if nested_key in metadata and isinstance(metadata[nested_key], dict):
            result = getDataFileUrl(metadata[nested_key])
            if result:
                return result
    
    # If we have an entry ID, try constructing a download URL
    # Format might be: /rest-api/entry/{id}/download/ or similar
    entry_id = metadata.get('entry_id') or metadata.get('id') or metadata.get('sasbdb_id')
    if entry_id:
        # Try common download endpoint patterns
        download_endpoints = [
            f"{SASBDB_API_BASE}/entry/{entry_id}/download/",
            f"{SASBDB_API_BASE}/entry/{entry_id}/data/",
            f"{SASBDB_API_BASE}/entry/{entry_id}/file/",
        ]
        # Return first endpoint (we'll try them in downloadDataFile if needed)
        return download_endpoints[0]
    
    logger.warning("Could not find data file URL in metadata")
    logger.debug(f"Metadata keys: {list(metadata.keys())}")
    return None


def downloadDataFile(url: str, filepath: str) -> bool:
    """
    Download a data file from the given URL to the specified filepath.
    
    :param url: URL of the data file to download
    :param filepath: Local filepath where the file should be saved
    :return: True if download successful, False otherwise
    """
    try:
        logger.info(f"Downloading data file from: {url}")
        response = requests.get(url, timeout=60, stream=True)
        response.raise_for_status()
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Write file in chunks to handle large files
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"Successfully downloaded data file to: {filepath}")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading data file from {url}: {e}")
        return False
    except IOError as e:
        logger.error(f"Error writing data file to {filepath}: {e}")
        return False


def _normalizeDatasetId(dataset_id: str) -> Optional[str]:
    """
    Normalize a SASBDB dataset identifier.
    
    SASBDB identifiers are 7 characters long, typically in format:
    - "SASDN24" (prefix + number)
    - "SASDB1234" (if 4-digit number)
    - etc.
    
    The API requires the full 7-character identifier.
    
    :param dataset_id: Input dataset identifier
    :return: Normalized identifier (uppercase, stripped), or None if invalid
    """
    if not dataset_id:
        return None
    
    # Remove whitespace and convert to uppercase
    normalized = dataset_id.strip().upper()
    
    # SASBDB identifiers are typically 7 characters
    # Accept identifiers that are 4-10 characters to be flexible
    if len(normalized) < 4 or len(normalized) > 10:
        logger.warning(f"Dataset ID length unusual: {len(normalized)} characters for '{normalized}'")
        # Still try it, but warn
    
    # Return the normalized identifier as-is (API expects full identifier)
    return normalized


def downloadDataset(dataset_id: str, output_dir: Optional[str] = None) -> tuple[Optional[str], Optional[SASBDBDatasetInfo]]:
    """
    Download a complete dataset from SASBDB.
    
    This is a convenience function that:
    1. Fetches metadata
    2. Extracts data file URL
    3. Downloads the data file
    4. Returns the local filepath and parsed metadata
    
    :param dataset_id: SASBDB dataset identifier
    :param output_dir: Directory to save the file (defaults to temp directory)
    :return: Tuple of (path to downloaded file, parsed metadata info) or (None, None) if error
    """
    # Get metadata
    metadata = getDatasetMetadata(dataset_id)
    if not metadata:
        return None, None
    
    # Parse metadata into structured object
    dataset_info = parseMetadata(metadata)
    
    # Get data file URL
    data_url = getDataFileUrl(metadata)
    if not data_url:
        logger.error(f"Could not find data file URL in metadata for dataset {dataset_id}")
        return None, dataset_info  # Return metadata even if download fails
    
    # Store the data URL in the info object
    if not dataset_info.intensities_data_url:
        dataset_info.intensities_data_url = data_url
    
    # Determine output directory
    if output_dir is None:
        output_dir = tempfile.gettempdir()
    
    # Generate filename
    normalized_id = _normalizeDatasetId(dataset_id)
    # Try to determine file extension from URL or metadata
    file_extension = _guessFileExtension(data_url, metadata)
    filename = f"SASBDB_{normalized_id}{file_extension}"
    filepath = os.path.join(output_dir, filename)
    
    # Download the file
    if downloadDataFile(data_url, filepath):
        return filepath, dataset_info
    
    return None, dataset_info


def _guessFileExtension(url: str, metadata: dict) -> str:
    """
    Guess the file extension from URL or metadata.
    
    :param url: Data file URL
    :param metadata: Dataset metadata
    :return: File extension (e.g., ".dat", ".txt", ".csv")
    """
    # Check URL for extension
    if '.' in url:
        parts = url.split('.')
        if len(parts) > 1:
            ext = '.' + parts[-1].split('?')[0]  # Remove query parameters
            if ext.lower() in ['.dat', '.txt', '.csv', '.out', '.asc']:
                return ext
    
    # Check metadata for file type hints
    if isinstance(metadata, dict):
        file_type_fields = ['file_type', 'fileType', 'format', 'data_format']
        for field in file_type_fields:
            if field in metadata:
                file_type = str(metadata[field]).lower()
                if 'csv' in file_type:
                    return '.csv'
                elif 'txt' in file_type or 'text' in file_type:
                    return '.txt'
                elif 'dat' in file_type or 'data' in file_type:
                    return '.dat'
    
    # Default to .dat for scattering data
    return '.dat'

