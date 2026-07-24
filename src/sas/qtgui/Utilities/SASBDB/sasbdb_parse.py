"""Parse SASBDB REST API metadata into structured objects."""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

_NESTED_PATHS = ("sample", "molecule", "experiment", "experimental", "metadata", "info")
_SEQUENCE_KEYS = frozenset(
    {"sequence", "fasta_sequence", "fasta", "primary_sequence", "sequence_string"}
)

_STR_FIELDS = {
    "entry_id": ("id", "entry_id", "sasbdb_id"),
    "code": ("code", "accession_code", "entry_code"),
    "title": ("title", "entry_title", "sample_title"),
    "sample_name": ("sample_name", "sample", "name", "sample_name_full"),
    "sample_description": ("sample_description", "description", "sample_description_full"),
    "concentration_unit": ("concentration_unit", "conc_unit", "concentration_units"),
    "molecule_name": (
        "molecule_name", "macromolecule_name", "protein_name", "molecule",
        "macromolecule", "protein", "name", "long_name",
    ),
    "molecule_short_name": ("short_name", "molecule_short_name", "shortName", "short"),
    "molecule_type": (
        "molecule_type", "macromolecule_type", "sample_type", "type",
        "molecule_type_full", "molecular_type",
    ),
    "uniprot_code": ("uniprot_code", "uniprot", "uniprot_id", "uniprot_accession", "uniprot_ac"),
    "source_organism": ("source_organism", "organism", "organism_name"),
    "number_of_molecules": (
        "number_of_molecules", "num_molecules", "copy_number", "number_molecules",
    ),
    "oligomerization": (
        "oligomerization", "oligomeric_state", "oligomer_state", "complex_state",
    ),
    "molecular_weight_method": ("mw_method", "molecular_weight_method"),
    "buffer_description": ("buffer", "buffer_description", "buffer_composition"),
    "instrument": ("instrument", "beamline", "instrument_name"),
    "detector": ("detector", "detector_name", "detector_type"),
    "publication_title": ("publication_title", "pub_title", "paper_title"),
    "publication_doi": ("doi", "publication_doi", "pub_doi"),
    "publication_pmid": ("pmid", "publication_pmid", "pubmed_id"),
    "intensities_data_url": ("intensities_data", "data_url", "intensities_url"),
    "pddf_data_url": ("pddf_data", "pddf_url", "pr_data"),
}

_FLOAT_FIELDS = {
    "concentration": ("concentration", "sample_concentration", "conc", "sample_conc"),
    "molecular_weight": ("molecular_weight", "mw", "exp_mw", "experimental_mw", "mw_kda"),
    "ph": ("ph", "buffer_ph"),
    "wavelength": ("wavelength", "xray_wavelength", "neutron_wavelength"),
    "temperature": ("temperature", "sample_temperature", "temp"),
    "rg": ("rg", "radius_of_gyration", "guinier_rg"),
    "rg_error": ("rg_error", "rg_err", "guinier_rg_error"),
    "i0": ("i0", "i_zero", "guinier_i0"),
    "i0_error": ("i0_error", "i0_err", "guinier_i0_error"),
    "dmax": ("dmax", "d_max", "maximum_dimension"),
    "porod_volume": ("porod_volume", "volume", "porod_vol"),
    "q_min": ("q_min", "qmin", "s_min", "smin"),
    "q_max": ("q_max", "qmax", "s_max", "smax"),
}


@dataclass
class SASBDBDatasetInfo:
    """Parsed metadata from a SASBDB dataset entry."""
    entry_id: str = ""
    code: str = ""
    title: str = ""
    sample_name: str = ""
    sample_description: str = ""
    concentration: float | None = None
    concentration_unit: str = "mg/mL"
    molecule_name: str = ""
    molecule_short_name: str = ""
    molecule_type: str = ""
    sequence: str = ""
    uniprot_code: str = ""
    source_organism: str = ""
    number_of_molecules: str = ""
    oligomerization: str = ""
    molecular_weight: float | None = None
    molecular_weight_method: str = ""
    oligomeric_state: str = ""
    buffer_description: str = ""
    ph: float | None = None
    instrument: str = ""
    detector: str = ""
    wavelength: float | None = None
    wavelength_unit: str = "Å"
    temperature: float | None = None
    temperature_unit: str = "K"
    rg: float | None = None
    rg_error: float | None = None
    i0: float | None = None
    i0_error: float | None = None
    dmax: float | None = None
    porod_volume: float | None = None
    q_min: float | None = None
    q_max: float | None = None
    publication_title: str = ""
    publication_doi: str = ""
    publication_pmid: str = ""
    authors: list = field(default_factory=list)
    intensities_data_url: str = ""
    pddf_data_url: str = ""
    raw_metadata: dict = field(default_factory=dict)


def parseMetadata(metadata: dict) -> SASBDBDatasetInfo:
    """Parse SASBDB API response into a structured SASBDBDatasetInfo object."""
    info = SASBDBDatasetInfo()
    if not isinstance(metadata, dict):
        return info

    info.raw_metadata = metadata
    logger.debug("SASBDB API response keys: %s", list(metadata.keys()))

    for attr, keys in _STR_FIELDS.items():
        setattr(info, attr, _get_str(metadata, *keys))
    for attr, keys in _FLOAT_FIELDS.items():
        setattr(info, attr, _get_float(metadata, *keys))

    info.sequence = _get_sequence(metadata)
    info.concentration_unit = info.concentration_unit or "mg/mL"
    info.oligomeric_state = info.oligomerization or _get_str(
        metadata, "oligomeric_state", "oligomer_state", "oligomerization"
    )

    authors = metadata.get("authors") or metadata.get("author_list") or []
    if isinstance(authors, list):
        info.authors = [str(author) for author in authors]
    elif isinstance(authors, str):
        info.authors = [authors]

    return info


def _get_str(data: dict, *keys: str) -> str:
    value = _find_shallow(data, keys, as_float=False)
    return value if isinstance(value, str) else _find_deep(data, keys, as_float=False) or ""


def _get_float(data: dict, *keys: str) -> float | None:
    value = _find_shallow(data, keys, as_float=True)
    return value if isinstance(value, float) else _find_deep(data, keys, as_float=True)


def _find_shallow(data: dict, keys: tuple[str, ...], *, as_float: bool):
    for key in keys:
        if key in data and data[key] is not None:
            converted = _convert_value(data[key], as_float=as_float)
            if _is_present(converted, as_float):
                return converted

    for path in _NESTED_PATHS:
        nested = data.get(path)
        if isinstance(nested, dict):
            for key in keys:
                if key in nested and nested[key] is not None:
                    converted = _convert_value(nested[key], as_float=as_float)
                    if _is_present(converted, as_float):
                        return converted
    return None


def _find_deep(data, keys: tuple[str, ...], *, as_float: bool):
    key_set = set(keys)

    def walk(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in key_set:
                    converted = _convert_value(value, as_float=as_float)
                    if _is_present(converted, as_float):
                        return converted
            for value in obj.values():
                found = walk(value)
                if found is not None:
                    return found
        elif isinstance(obj, list):
            for item in obj:
                found = walk(item)
                if found is not None:
                    return found
        return None

    return walk(data)


def _convert_value(value, *, as_float: bool):
    if value is None:
        return None
    if as_float:
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    return ""


def _is_present(value, as_float: bool) -> bool:
    if as_float:
        return value is not None
    return bool(value)


def _get_sequence(data: dict) -> str:
    def walk(obj) -> str:
        if isinstance(obj, dict):
            for key in _SEQUENCE_KEYS:
                if key in obj and isinstance(obj[key], str) and obj[key].strip():
                    return obj[key].strip()
            for value in obj.values():
                found = walk(value)
                if found:
                    return found
        elif isinstance(obj, list):
            for item in obj:
                found = walk(item)
                if found:
                    return found
        return ""

    return walk(data) if isinstance(data, dict) else ""
