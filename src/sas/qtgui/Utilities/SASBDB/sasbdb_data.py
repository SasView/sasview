"""
Data structures for SASBDB export.

This module defines dataclasses that match the SASBDB (Small Angle Scattering
Biological Data Bank) submission structure. These data structures are used
throughout the SASBDB export functionality to represent and organize all
information required for data submission.

The main container class is SASBDBExportData, which holds:
- Project information (SASBDBProject)
- Sample data (SASBDBSample), which includes molecule, buffer, fits, etc.
- Instrument information (SASBDBInstrument)

All dataclasses use Optional fields to allow for partial data entry, with
required fields enforced during validation before export.
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SASBDBProject:
    """Project information for SASBDB submission"""
    published: bool = False  # Required
    pubmed_pmid: str | None = None  # Required if published
    doi: str | None = None  # Required if published
    project_title: str | None = None  # Required if not published


@dataclass
class SASBDBMolecule:
    """Molecule information for SASBDB submission"""
    type: str | None = None  # Protein / DNA / RNA / Lipid / Other bound molecules
    uniprot_accession: str | None = None
    uniprot_range_from: int | None = None
    uniprot_range_to: int | None = None
    molecule_source: str | None = None  # Biological / synthetic
    long_name: str | None = None  # Required
    short_name: str | None = None
    source_organism: str | None = None
    fasta_sequence: str | None = None  # Required (AA sequence)
    monomer_mw_kda: float | None = None  # Required
    oligomeric_state: str | None = None  # monomer / dimer / ... / other
    number_of_molecules: int | None = None  # Required
    total_mw_kda: float | None = None
    molecule_description: str | None = None


@dataclass
class SASBDBBuffer:
    """Buffer information for SASBDB submission"""
    description: str | None = None  # Required
    ph: float | None = None  # Required
    comment: str | None = None


@dataclass
class SASBDBGuinier:
    """Guinier analysis results"""
    rg: float | None = None  # Required (nm)
    rg_error: float | None = None
    i0: float | None = None
    range_start: float | None = None
    range_end: float | None = None


@dataclass
class SASBDBPDDF:
    """Pair Distance Distribution Function information"""
    software: str | None = None  # ATSAS / BayesApp / ... / Other
    software_version: str | None = None
    pddf_file: str | None = None
    dmax: float | None = None  # nm
    dmax_error: float | None = None
    rg: float | None = None  # nm
    rg_error: float | None = None
    i0: float | None = None
    porod_volume: float | None = None  # nm^3
    mw_from_porod_volume: float | None = None


@dataclass
class SASBDBInstrument:
    """Instrument information for SASBDB submission"""
    source_type: str | None = None  # Required: X-ray synchrotron / X-ray in house / Neutron source / Other
    beamline_name: str | None = None  # Required: Beamline name or Instrument manufacturer / Model
    synchrotron_name: str | None = None  # Required: Synchrotron name or Institute / Facility
    detector_manufacturer: str | None = None  # Required: Detector manufacturer / Model
    detector_type: str | None = None
    detector_resolution: str | None = None  # Required: pixel size
    city: str | None = None  # Required
    country: str | None = None  # Required


@dataclass
class SASBDBModel:
    """Model information for SASBDB submission"""
    software_or_db: str | None = None  # Required: ATSAS software / Multifoxs / BilboMD / ... / other / other(static image)
    software_version: str | None = None
    model_data: str | None = None  # Required: file in accordance with software
    symmetry: str | None = None
    log: str | None = None
    comment: str | None = None
    # For shape visualization (not exported to JSON, only used for UI display)
    visualization_params: dict[str, Any] | None = field(default=None, repr=False)


@dataclass
class SASBDBFit:
    """Fit information for SASBDB submission"""
    software: str | None = None  # ATSAS software / Pepsi / Foxis / ... / Other
    software_version: str | None = None
    fit_data: str | None = None  # fit file
    angular_units: str | None = None  # 1/A / 1/nm / other
    chi_squared: float | None = None
    cormap_pvalue: float | None = None
    log_file: str | None = None
    description: str | None = None
    models: list[SASBDBModel] = field(default_factory=list)  # One fit can have several models


@dataclass
class SASBDBSample:
    """Sample/Data information for SASBDB submission"""
    sample_title: str | None = None  # Required
    molecule: SASBDBMolecule | None = None  # Required
    buffer: SASBDBBuffer | None = None  # Required
    curve_type: str | None = None  # Required: Single concentration / ... / Other
    experimental_curve: str | None = None  # Required: *.dat file
    angular_units: str | None = None  # Required: 1/nm / 1/A / arbitrary
    intensity_units: str | None = None  # 1/cm / arbitrary
    experimental_molecular_weight: float | None = None  # Required
    guinier: SASBDBGuinier | None = None
    molecular_weight_from_i0: float | None = None
    molecular_weight_from_i0_error: float | None = None
    pddf: SASBDBPDDF | None = None
    description: str | None = None
    experiment_date: str | None = None  # Required
    beamline_instrument: str | None = None  # Required
    wavelength: float | None = None  # nm
    sample_detector_distance: float | None = None  # m
    cell_temperature: float | None = None  # °C
    storage_temperature: float | None = None  # °C
    exposure_time: float | None = None  # s
    number_of_frames: int | None = None
    concentration: float | None = None  # mg/ml
    fits: list[SASBDBFit] = field(default_factory=list)  # Several fit-model pairs


@dataclass
class SASBDBExportData:
    """
    Container for all SASBDB export data.
    
    This is the top-level container class that holds all information for a
    SASBDB submission. It contains:
    
    - project: Project-level information (publication status, title, etc.)
    - samples: List of sample data objects (each sample can have multiple fits)
    - instruments: List of instrument/facility information
    
    :param project: Project information (optional)
    :param samples: List of sample data objects (default: empty list)
    :param instruments: List of instrument objects (default: empty list)
    """
    project: SASBDBProject | None = None
    samples: list[SASBDBSample] = field(default_factory=list)
    instruments: list[SASBDBInstrument] = field(default_factory=list)

