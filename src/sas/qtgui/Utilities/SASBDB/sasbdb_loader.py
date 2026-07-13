"""
Load SASBDB datasets into SasView.
"""

import logging
import os

from PySide6.QtWidgets import QMessageBox

from sasdata.dataloader.data_info import Sample, Source

from .sasbdb_api import SASBDBDatasetInfo

logger = logging.getLogger(__name__)

_META_FIELDS = (
    ("SASBDB_Rg", "rg", ("SASBDB_Rg_error", "rg_error")),
    ("SASBDB_I0", "i0", ("SASBDB_I0_error", "i0_error")),
    ("SASBDB_Dmax", "dmax", None),
    ("SASBDB_MW", "molecular_weight", ("SASBDB_MW_method", "molecular_weight_method")),
    ("SASBDB_Porod_volume", "porod_volume", None),
    ("SASBDB_molecule", "molecule_name", None),
    ("SASBDB_molecule_type", "molecule_type", None),
    ("SASBDB_oligomeric_state", "oligomeric_state", None),
    ("SASBDB_DOI", "publication_doi", None),
    ("SASBDB_PMID", "publication_pmid", None),
)


def metadata_summary(info: SASBDBDatasetInfo) -> str:
    """Format dataset metadata for display or logging."""
    lines = []
    if info.title:
        lines.append(f"Title: {info.title}")
    if info.sample_name:
        lines.append(f"Sample: {info.sample_name}")
    if info.molecule_name:
        lines.append(f"Molecule: {info.molecule_name}")
    if info.concentration:
        lines.append(f"Concentration: {info.concentration} {info.concentration_unit}")
    if info.buffer_description:
        lines.append(f"Buffer: {info.buffer_description}")
    if info.instrument:
        lines.append(f"Instrument: {info.instrument}")
    if info.wavelength:
        lines.append(f"Wavelength: {info.wavelength} {info.wavelength_unit}")
    if info.temperature:
        lines.append(f"Temperature: {info.temperature} {info.temperature_unit}")
    if info.rg is not None:
        rg = f"Rg: {info.rg:.2f}"
        if info.rg_error:
            rg += f" ± {info.rg_error:.2f}"
        lines.append(f"{rg} Å")
    if info.i0 is not None:
        i0 = f"I(0): {info.i0}"
        if info.i0_error:
            i0 += f" ± {info.i0_error}"
        lines.append(i0)
    if info.dmax is not None:
        lines.append(f"Dmax: {info.dmax} Å")
    if info.molecular_weight is not None:
        lines.append(f"MW: {info.molecular_weight:.1f} kDa")
    if info.publication_doi:
        lines.append(f"DOI: {info.publication_doi}")
    return "\n".join(lines)


def load_downloaded_dataset(files_widget, parent, filepath: str | None,
                            dataset_info: SASBDBDatasetInfo | None) -> None:
    """Load a downloaded SASBDB file and apply metadata."""
    if not filepath or not os.path.exists(filepath):
        return

    try:
        loaded_data, _ = files_widget.readData([filepath])
        if dataset_info and loaded_data:
            populate_metadata(loaded_data, dataset_info)

        entry_id = dataset_info.code or dataset_info.entry_id if dataset_info else None
        logger.info(
            "Successfully loaded SASBDB dataset %s from %s",
            entry_id or "unknown",
            filepath,
        )
        if dataset_info:
            for line in metadata_summary(dataset_info).splitlines():
                logger.info("  %s", line)
    except Exception as e:
        logger.error(f"Error loading downloaded SASBDB dataset: {e}", exc_info=True)
        QMessageBox.warning(parent, "Load Error", f"Failed to load downloaded dataset:\n{e}")


def populate_metadata(loaded_data: dict, dataset_info: SASBDBDatasetInfo) -> None:
    """Populate SASBDB metadata into loaded data objects."""
    for data_id, data in loaded_data.items():
        try:
            _apply_metadata(data, dataset_info)
        except Exception as e:
            logger.warning(f"Error populating metadata for data {data_id}: {e}")


def _apply_metadata(data, info: SASBDBDatasetInfo) -> None:
    if info.title and not data.title:
        data.title = info.title
    if info.instrument and not data.instrument:
        data.instrument = info.instrument
    if info.code:
        data.run = data.run or []
        if info.code not in data.run:
            data.run.append(info.code)

    if data.sample is None:
        data.sample = Sample()
    if not getattr(data.sample, "details", None):
        data.sample.details = []

    sample_id = info.molecule_short_name or info.sample_name or info.code
    if sample_id:
        data.sample.ID = sample_id

    details = []
    if info.molecule_name:
        detail = f"Molecule: {info.molecule_name}"
        if info.molecule_type:
            detail += f" ({info.molecule_type})"
        details.append(detail)
    elif info.sample_name:
        details.append(f"Sample: {info.sample_name}")
    if info.sample_description:
        details.append(f"Description: {info.sample_description}")
    if info.sequence:
        details.append(f"Sequence: {info.sequence}")
    if info.uniprot_code:
        details.append(f"UniProt: {info.uniprot_code}")
    oligomerization = info.oligomerization or info.oligomeric_state
    if oligomerization:
        details.append(f"Oligomerization: {oligomerization}")
    if info.number_of_molecules:
        details.append(f"Number of molecules: {info.number_of_molecules}")
    if info.source_organism:
        details.append(f"Source organism: {info.source_organism}")
    if info.temperature is not None:
        data.sample.temperature = info.temperature
        if info.temperature_unit:
            data.sample.temperature_unit = info.temperature_unit
        temp = f"Temperature: {info.temperature}"
        if info.temperature_unit:
            temp += f" {info.temperature_unit}"
        details.append(temp)
    if info.concentration is not None:
        conc = f"Concentration: {info.concentration}"
        if info.concentration_unit:
            conc += f" {info.concentration_unit}"
        details.append(conc)
    if info.buffer_description:
        buffer = f"Buffer: {info.buffer_description}"
        if info.ph is not None:
            buffer += f" (pH {info.ph})"
        details.append(buffer)

    for detail in details:
        if detail not in data.sample.details:
            data.sample.details.append(detail)

    if data.source is None:
        data.source = Source()
    if info.wavelength is not None:
        data.source.wavelength = info.wavelength
        data.source.wavelength_unit = info.wavelength_unit

    if not getattr(data, "meta_data", None):
        data.meta_data = {}
    data.meta_data["SASBDB_code"] = info.code or info.entry_id
    for key, attr, extra in _META_FIELDS:
        value = getattr(info, attr, None)
        if value is None:
            continue
        data.meta_data[key] = value
        if extra:
            extra_key, extra_attr = extra
            extra_value = getattr(info, extra_attr, None)
            if extra_value is not None:
                data.meta_data[extra_key] = extra_value
    if info.authors:
        data.meta_data["SASBDB_authors"] = ", ".join(info.authors)
