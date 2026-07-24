"""
SASBDB REST API client module.
"""

import logging
import os
import re
import tempfile

import requests

from .sasbdb_parse import SASBDBDatasetInfo, parseMetadata

logger = logging.getLogger(__name__)

SASBDB_API_BASE = "https://www.sasbdb.org/rest-api"
SASBDB_SITE_BASE = "https://www.sasbdb.org"
_SASBDB_ID_PATTERN = re.compile(r"^SAS[A-Z]{2}\d+$")
INVALID_DATASET_ID_MESSAGE = "Enter the full 7-character SASBDB code (e.g. SASDN24)."

_URL_FIELDS = (
    "intensities_data", "intensitiesData", "data_file_url", "dataFileUrl",
    "data_file", "dataFile", "scattering_data_url", "scatteringDataUrl",
    "experimental_data_url", "experimentalDataUrl", "download_url", "downloadUrl",
    "file_url", "fileUrl", "files", "data_files", "dataFiles",
    "experimental_files", "scattering_files", "experimental_data",
    "experimentalData", "scattering_data", "scatteringData",
)
_URL_NESTED = ("entry", "data", "files", "experimental_data", "scattering_data")
_URL_ITEM_KEYS = ("url", "path", "file", "file_url", "download_url")
_KNOWN_EXTENSIONS = {".dat", ".txt", ".csv", ".out", ".asc"}


def getDatasetMetadata(dataset_id: str) -> dict | None:
    """Fetch dataset metadata from the SASBDB API."""
    normalized_id = _normalizeDatasetId(dataset_id)
    if not normalized_id:
        logger.error("Invalid dataset ID format: %s", dataset_id)
        return None

    endpoint = f"{SASBDB_API_BASE}/entry/summary/{normalized_id}/"
    try:
        logger.info("Fetching dataset metadata from: %s", endpoint)
        response = requests.get(endpoint, headers={"accept": "application/json"}, timeout=30)
        response.raise_for_status()
        logger.info("Successfully retrieved metadata for dataset %s", normalized_id)
        return response.json()
    except requests.exceptions.HTTPError as error:
        if error.response is not None and error.response.status_code == 404:
            logger.error("Dataset %s not found (404)", normalized_id)
        else:
            logger.error("HTTP error fetching dataset %s: %s", normalized_id, error)
    except requests.exceptions.RequestException as error:
        logger.error("Network error fetching dataset %s: %s", normalized_id, error)
    except ValueError as error:
        logger.error("Invalid JSON response for dataset %s: %s", normalized_id, error)
    return None


def getDataFileUrl(metadata: dict) -> str | None:
    """Extract a data file URL from dataset metadata."""
    if not isinstance(metadata, dict):
        return None

    for field_name in _URL_FIELDS:
        if field_name in metadata:
            url = _resolve_url_value(metadata[field_name])
            if url:
                return url

    for nested_key in _URL_NESTED:
        nested = metadata.get(nested_key)
        if isinstance(nested, dict):
            url = getDataFileUrl(nested)
            if url:
                return url

    logger.warning("Could not find data file URL in metadata")
    logger.debug("Metadata keys: %s", list(metadata.keys()))
    return None


def downloadDataFile(url: str, filepath: str) -> bool:
    """Download a data file from the given URL."""
    try:
        logger.info("Downloading data file from: %s", url)
        response = requests.get(url, timeout=60, stream=True)
        response.raise_for_status()
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as handle:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    handle.write(chunk)
        logger.info("Successfully downloaded data file to: %s", filepath)
        return True
    except requests.exceptions.RequestException as error:
        logger.error("Error downloading data file from %s: %s", url, error)
    except OSError as error:
        logger.error("Error writing data file to %s: %s", filepath, error)
    return False


def validateDatasetId(dataset_id: str) -> tuple[str | None, str | None]:
    """Validate and normalize a SASBDB dataset identifier."""
    normalized = _normalizeDatasetId(dataset_id)
    if normalized:
        return normalized, None
    return None, INVALID_DATASET_ID_MESSAGE


def downloadDataset(
    dataset_id: str, output_dir: str | None = None,
) -> tuple[str | None, SASBDBDatasetInfo | None]:
    """Fetch metadata, download the intensity file, and return path + parsed info."""
    metadata = getDatasetMetadata(dataset_id)
    if not metadata:
        return None, None

    dataset_info = parseMetadata(metadata)
    data_url = dataset_info.intensities_data_url or getDataFileUrl(metadata)
    if not data_url:
        logger.error("Could not find data file URL in metadata for dataset %s", dataset_id)
        return None, dataset_info

    dataset_info.intensities_data_url = data_url
    output_dir = output_dir or tempfile.gettempdir()
    normalized_id = _normalizeDatasetId(dataset_id)
    filename = f"SASBDB_{normalized_id}{_guessFileExtension(data_url, metadata)}"
    filepath = os.path.join(output_dir, filename)

    if downloadDataFile(data_url, filepath):
        return filepath, dataset_info
    return None, dataset_info


def _normalizeDatasetId(dataset_id: str) -> str | None:
    if not dataset_id:
        return None
    normalized = dataset_id.strip().upper()
    if len(normalized) != 7 or not _SASBDB_ID_PATTERN.match(normalized):
        logger.warning("Invalid SASBDB dataset ID: %r", dataset_id)
        return None
    return normalized


def _resolve_url_value(value) -> str | None:
    if isinstance(value, str):
        return _absolute_url(value)
    if isinstance(value, list) and value:
        return _resolve_url_value(value[0])
    if isinstance(value, dict):
        for key in _URL_ITEM_KEYS:
            if key in value:
                return _resolve_url_value(value[key])
    return None


def _absolute_url(url: str) -> str | None:
    if url.startswith("/"):
        return f"{SASBDB_SITE_BASE}{url}"
    if url.startswith("http"):
        return url
    return None


def _guessFileExtension(url: str, metadata: dict) -> str:
    if "." in url:
        ext = "." + url.split(".")[-1].split("?")[0]
        if ext.lower() in _KNOWN_EXTENSIONS:
            return ext

    if isinstance(metadata, dict):
        for field_name in ("file_type", "fileType", "format", "data_format"):
            file_type = metadata.get(field_name)
            if file_type is None:
                continue
            file_type = str(file_type).lower()
            if "csv" in file_type:
                return ".csv"
            if "txt" in file_type or "text" in file_type:
                return ".txt"
            if "dat" in file_type or "data" in file_type:
                return ".dat"
    return ".dat"
