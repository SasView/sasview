"""
Data structures for SASBDB export

This module defines dataclasses that match the SASBDB submission structure.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class SASBDBProject:
    """Project information for SASBDB submission"""
    published: bool = False  # Required
    pubmed_pmid: Optional[str] = None  # Required if published
    doi: Optional[str] = None  # Required if published
    project_title: Optional[str] = None  # Required if not published


@dataclass
class SASBDBMolecule:
    """Molecule information for SASBDB submission"""
    type: Optional[str] = None  # Protein / DNA / RNA / Lipid / Other bound molecules
    uniprot_accession: Optional[str] = None
    uniprot_range_from: Optional[int] = None
    uniprot_range_to: Optional[int] = None
    molecule_source: Optional[str] = None  # Biological / synthetic
    long_name: Optional[str] = None  # Required
    short_name: Optional[str] = None
    source_organism: Optional[str] = None
    fasta_sequence: Optional[str] = None  # Required (AA sequence)
    monomer_mw_kda: Optional[float] = None  # Required
    oligomeric_state: Optional[str] = None  # monomer / dimer / ... / other
    number_of_molecules: Optional[int] = None  # Required
    total_mw_kda: Optional[float] = None
    molecule_description: Optional[str] = None


@dataclass
class SASBDBBuffer:
    """Buffer information for SASBDB submission"""
    description: Optional[str] = None  # Required
    ph: Optional[float] = None  # Required
    comment: Optional[str] = None


@dataclass
class SASBDBGuinier:
    """Guinier analysis results"""
    rg: Optional[float] = None  # Required (nm)
    rg_error: Optional[float] = None
    i0: Optional[float] = None
    range_start: Optional[float] = None
    range_end: Optional[float] = None


@dataclass
class SASBDBPDDF:
    """Pair Distance Distribution Function information"""
    software: Optional[str] = None  # ATSAS / BayesApp / ... / Other
    software_version: Optional[str] = None
    pddf_file: Optional[str] = None
    dmax: Optional[float] = None  # nm
    dmax_error: Optional[float] = None
    rg: Optional[float] = None  # nm
    rg_error: Optional[float] = None
    i0: Optional[float] = None
    porod_volume: Optional[float] = None  # nm^3
    mw_from_porod_volume: Optional[float] = None


@dataclass
class SASBDBInstrument:
    """Instrument information for SASBDB submission"""
    source_type: Optional[str] = None  # Required: X-ray synchrotron / X-ray in house / Neutron source / Other
    beamline_name: Optional[str] = None  # Required: Beamline name or Instrument manufacturer / Model
    synchrotron_name: Optional[str] = None  # Required: Synchrotron name or Institute / Facility
    detector_manufacturer: Optional[str] = None  # Required: Detector manufacturer / Model
    detector_type: Optional[str] = None
    detector_resolution: Optional[str] = None  # Required: pixel size
    city: Optional[str] = None  # Required
    country: Optional[str] = None  # Required


@dataclass
class SASBDBModel:
    """Model information for SASBDB submission"""
    software_or_db: Optional[str] = None  # Required: ATSAS software / Multifoxs / BilboMD / ... / other / other(static image)
    software_version: Optional[str] = None
    model_data: Optional[str] = None  # Required: file in accordance with software
    symmetry: Optional[str] = None
    log: Optional[str] = None
    comment: Optional[str] = None
    # For shape visualization (not exported to JSON, only used for UI display)
    visualization_params: Optional[Dict[str, Any]] = field(default=None, repr=False)


@dataclass
class SASBDBFit:
    """Fit information for SASBDB submission"""
    software: Optional[str] = None  # ATSAS software / Pepsi / Foxis / ... / Other
    software_version: Optional[str] = None
    fit_data: Optional[str] = None  # fit file
    angular_units: Optional[str] = None  # 1/A / 1/nm / other
    chi_squared: Optional[float] = None
    cormap_pvalue: Optional[float] = None
    log_file: Optional[str] = None
    description: Optional[str] = None
    models: List[SASBDBModel] = field(default_factory=list)  # One fit can have several models


@dataclass
class SASBDBSample:
    """Sample/Data information for SASBDB submission"""
    sample_title: Optional[str] = None  # Required
    molecule: Optional[SASBDBMolecule] = None  # Required
    buffer: Optional[SASBDBBuffer] = None  # Required
    curve_type: Optional[str] = None  # Required: Single concentration / ... / Other
    experimental_curve: Optional[str] = None  # Required: *.dat file
    angular_units: Optional[str] = None  # Required: 1/nm / 1/A / arbitrary
    intensity_units: Optional[str] = None  # 1/cm / arbitrary
    experimental_molecular_weight: Optional[float] = None  # Required
    guinier: Optional[SASBDBGuinier] = None
    molecular_weight_from_i0: Optional[float] = None
    molecular_weight_from_i0_error: Optional[float] = None
    pddf: Optional[SASBDBPDDF] = None
    description: Optional[str] = None
    experiment_date: Optional[str] = None  # Required
    beamline_instrument: Optional[str] = None  # Required
    wavelength: Optional[float] = None  # nm
    sample_detector_distance: Optional[float] = None  # m
    cell_temperature: Optional[float] = None  # °C
    storage_temperature: Optional[float] = None  # °C
    exposure_time: Optional[float] = None  # s
    number_of_frames: Optional[int] = None
    concentration: Optional[float] = None  # mg/ml
    fits: List[SASBDBFit] = field(default_factory=list)  # Several fit-model pairs


@dataclass
class SASBDBExportData:
    """Container for all SASBDB export data"""
    project: Optional[SASBDBProject] = None
    samples: List[SASBDBSample] = field(default_factory=list)
    instruments: List[SASBDBInstrument] = field(default_factory=list)

