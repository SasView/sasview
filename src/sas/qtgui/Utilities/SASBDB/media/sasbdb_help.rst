.. sasbdb_help.rst

SASBDB Export
=============

Introduction
------------

The SASBDB Export tool allows you to export your Small Angle Scattering (SAS) data and analysis results in a format suitable for submission to the Small Angle Scattering Biological Data Bank (SASBDB). SASBDB is a repository for experimental SAS data from biological macromolecules, providing a standardized format for data sharing and publication.

This tool collects data from your current SasView session, including:

- Loaded experimental datasets
- Fit results and model parameters
- Guinier analysis results (if available)
- Instrument and experimental metadata
- Model visualizations

The exported data can be reviewed and edited before export, ensuring all required information is complete.

Accessing the Feature
---------------------

To open the SASBDB Export dialog:

1. Ensure you have loaded data into the *Data Explorer* (see :ref:`Loading_data`).
2. Optionally, perform a fit or analysis on your data.
3. Select *Tools* from the menu bar, then choose *Export to SASBDB*.

The dialog will automatically collect available data from your current session and populate the form fields where possible.

Dialog Overview
---------------

The SASBDB Export dialog consists of multiple tabs, each containing related fields:

- **Project Tab**: Project publication status and identification
- **Sample Tab**: Sample information and experimental parameters
- **Molecule Tab**: Biological molecule details
- **Buffer Tab**: Buffer composition and conditions
- **Guinier Tab**: Guinier analysis results (if available)
- **Fit Tab**: Fit results and model information
- **Instrument Tab**: Instrument and facility details
- **Shape Visualization**: 3D model visualization (if a model is fitted)

Project Tab
-----------

The Project tab contains information about your research project.

**Published Status**
  Check the "Published" checkbox if this data is associated with a published paper. If checked, you must provide either:
  
  - **PubMed PMID**: The PubMed ID of the publication
  - **DOI**: The Digital Object Identifier of the publication
  
  If the project is not published, you must provide:
  
  - **Project Title**: A descriptive title for your project

**Field Descriptions**

- **Published**: Checkbox indicating whether the project is published
- **PubMed PMID**: PubMed identifier (required if published)
- **DOI**: Digital Object Identifier (required if published)
- **Project Title**: Title of the project (required if not published)

Sample Tab
----------

The Sample tab contains information about your experimental sample and data.

**Required Fields**

- **Sample Title**: A descriptive name for your sample
- **Experimental Molecular Weight**: The molecular weight in kDa
- **Experiment Date**: Date when the experiment was performed (format: YYYY-MM-DD)
- **Beamline/Instrument**: Name of the beamline or instrument used

**Optional Fields**

- **Curve Type**: Type of scattering curve (e.g., "Single concentration", "Concentration series", etc.)
- **Angular Units**: Units for the scattering vector (1/A, 1/nm, or arbitrary)
- **Intensity Units**: Units for the scattering intensity (1/cm or arbitrary)
- **Wavelength**: X-ray or neutron wavelength in nm
- **Sample-Detector Distance**: Distance from sample to detector in meters
- **Cell Temperature**: Sample temperature during measurement in °C
- **Concentration**: Sample concentration in mg/ml

**Data Collection**

Many fields are automatically populated from your loaded data:

- Sample title is taken from the data filename or name
- Angular and intensity units are extracted from the data axes
- Wavelength, detector distance, and temperature are read from data metadata
- Experiment date defaults to today's date if not found in metadata

Molecule Tab
------------

The Molecule tab contains detailed information about the biological molecule being studied.

**Required Fields**

- **Long Name**: Full name of the molecule (e.g., "Bovine serum albumin")
- **FASTA Sequence**: Amino acid sequence in FASTA format (single letter code)
- **Monomer MW (kDa)**: Molecular weight of a single monomer in kDa

**Optional Fields**

- **Molecule Type**: Type of molecule (Protein, DNA, RNA, Lipid, Other bound molecules)
- **Short Name**: Abbreviated name or common name
- **Source Organism**: Organism from which the molecule was derived
- **Molecule Source**: Whether the molecule is biological or synthetic
- **Oligomeric State**: The oligomeric state (monomer, dimer, trimer, tetramer, etc.)
- **Number of Molecules**: Number of molecules in the complex
- **UniProt Accession**: UniProt database accession number (if applicable)
- **UniProt Range**: Residue range from UniProt sequence (if applicable)
- **Total MW (kDa)**: Total molecular weight of the complex
- **Molecule Description**: Additional description of the molecule

Buffer Tab
----------

The Buffer tab contains information about the buffer solution used in the experiment.

**Required Fields**

- **Buffer Description**: Description of the buffer composition (e.g., "20 mM Tris-HCl, 150 mM NaCl")
- **Buffer pH**: pH value of the buffer solution

**Optional Fields**

- **Comment**: Additional notes about the buffer conditions

Guinier Tab
-----------

The Guinier tab displays results from Guinier analysis, if available.

**Fields**

- **Rg**: Radius of gyration in nm
- **Rg Error**: Uncertainty in Rg
- **I(0)**: Forward scattering intensity
- **Range Start**: Starting q-value of the Guinier range
- **Range End**: Ending q-value of the Guinier range

**Availability**

Guinier analysis results are automatically populated if:

- You have performed a Guinier fit using the Linear Fit tool
- FreeSAS auto_guinier analysis has been performed on your data

If no Guinier analysis is available, these fields will be empty and can be left blank.

Fit Tab
-------

The Fit tab contains information about your model fitting results.

**Fit Information**

- **Software**: Fitting software used (typically "SasView")
- **Software Version**: Version of the fitting software
- **Chi-squared**: Chi-squared value from the fit
- **CorMap P-value**: CorMap p-value (if calculated)

**Model Information**

- **Model Name**: Name of the fitted model (e.g., "sphere", "core_shell_sphere")
- **Model Parameters**: List of fitted parameters with values, uncertainties, and units

**Data Collection**

Fit information is automatically collected from:

- Active fitting widget in the Fitting perspective
- Fit results including chi-squared and parameter values
- Model name and parameters from the fitted model

If no fit has been performed, these fields will be empty.

Instrument Tab
--------------

The Instrument tab contains information about the instrument and facility where the experiment was performed.

**Required Fields**

- **Source Type**: Type of radiation source (X-ray synchrotron, X-ray in house, Neutron source, or Other)
- **Beamline Name**: Name of the beamline or instrument manufacturer/model
- **Synchrotron Name**: Name of the synchrotron facility or institute/facility
- **Detector Manufacturer**: Detector manufacturer and model
- **Detector Resolution**: Detector pixel size
- **City**: City where the facility is located
- **Country**: Country where the facility is located

**Data Collection**

Instrument information is automatically extracted from:

- Data metadata (beamline, facility, detector information)
- Source and detector objects in the data structure
- Metadata dictionary fields

Shape Visualization
------------------

The Shape Visualization panel displays a 3D representation of your fitted model along with cross-sectional views.

**Visualization Components**

- **3D View**: Isometric 3D view of the model shape
- **Cross-Sections**: Three orthogonal cross-sections (XY top view, XZ front view, YZ side view)

**Supported Models**

The visualization supports the following model types:

- **Sphere**: Simple spherical particles
- **Core-Shell Sphere**: Spherical particles with a core and shell
- **Cylinder**: Cylindrical particles
- **Core-Shell Cylinder**: Cylindrical particles with a core and shell
- **Ellipsoid**: Ellipsoidal particles
- **Parallelepiped**: Rectangular box-shaped particles
- **Generic Models**: Other models display a generic representation

**Availability**

The shape visualization is available when:

- A model has been fitted to your data
- The model parameters are available from the fitting widget
- The model type is recognized

The visualization uses the current fitted parameter values, so it reflects your actual fit results.

**Visualization Features**

- The 3D view shows an isometric projection of the model
- Cross-sections show clean numeric axes with minimal tick marks for clarity
- Model parameters are displayed in the visualization title
- The visualization automatically scales to fit the available space

Export Functionality
--------------------

The Export button saves three files to a location you specify:

1. **JSON File**: The main SASBDB export data in JSON format (user-selected filename)
2. **PDF File**: A PDF report containing all the export information (auto-named based on JSON filename)
3. **Project File**: A SasView project file containing your current session (auto-named based on JSON filename)

**Export Process**

1. Click the **Export** button
2. A file dialog will appear asking you to select a location and name for the JSON file
3. The PDF and project files will be automatically saved in the same directory with names derived from your JSON filename

**File Naming**

- If you save the JSON file as ``my_export.json``, the files will be:
  - ``my_export.json`` (JSON export data)
  - ``my_export.pdf`` (PDF report)
  - ``my_export_project.json`` (SasView project)

**Export Results**

After export, you will see a message indicating:

- **Success**: All three files were saved successfully
- **Partial Success**: Some files were saved, with details about which succeeded/failed
- **Failure**: All files failed to save, with error messages

The dialog will automatically close on successful export of all files.

**Export PDF**

You can also generate a PDF report without exporting by clicking the **Export PDF** button. This creates a PDF file containing:

- All project, sample, molecule, buffer, instrument, and fit information
- Model visualization (if available)
- Formatted for easy review and sharing

Data Collection
---------------

The SASBDB Export tool automatically collects data from your SasView session:

**From Loaded Data**

- Sample title from filename
- Angular and intensity units from data axes
- Wavelength, detector distance, temperature from metadata
- Experiment date (from metadata or defaults to today)
- Beamline/instrument information from metadata

**From Fit Results**

- Model name and parameters
- Chi-squared value
- Software version information
- Parameter uncertainties and units

**From Analysis Results**

- Guinier analysis results (if Linear Fit or FreeSAS was used)
- PDDF results (if Corfunc analysis was performed)

**Manual Entry**

Any missing information must be entered manually. The dialog highlights required fields and will validate your input before export.

Validation
----------

Before exporting, the dialog validates that all required fields are filled:

**Project Validation**

- If published: Either PubMed PMID or DOI must be provided
- If not published: Project Title must be provided

**Sample Validation**

- Sample Title is required
- Experimental Molecular Weight is required
- Experiment Date is required
- Beamline/Instrument is required

**Molecule Validation**

- Long Name is required
- FASTA Sequence is required
- Monomer MW (kDa) is required

**Buffer Validation**

- Buffer Description is required
- Buffer pH is required

**Validation Errors**

If validation fails, you will see an error message indicating which required fields are missing. The export will not proceed until all required fields are completed.

Tips and Best Practices
-----------------------

**When to Use This Feature**

- When preparing data for SASBDB submission
- When documenting your experimental setup and results
- When sharing data with collaborators in a standardized format
- When archiving your analysis results

**Completing Missing Information**

- Review each tab carefully to ensure all required fields are filled
- Check that automatically collected data is correct
- Add any additional information that might be useful for data submission
- Use the PDF export to review your data before final submission

**Reviewing Exported Data**

- Open the JSON file in a text editor to verify the structure
- Check the PDF report for a formatted view of all information
- The project file can be reloaded in SasView to restore your session

**Data Quality**

- Ensure molecular weight values are accurate
- Verify that units are consistent (e.g., wavelength in nm, distance in meters)
- Check that dates are in the correct format (YYYY-MM-DD)
- Review model parameters to ensure they are reasonable

**Troubleshooting**

**Shape Visualization Not Available**
  - Ensure a model has been fitted to your data
  - Check that the model type is supported
  - Verify that parameter values are available

**Export Fails**
  - Check that you have write permissions in the selected directory
  - Ensure sufficient disk space is available
  - Review error messages for specific issues

**Missing Data**
  - Some fields may not be available from your data files
  - Manually enter missing information as needed
  - Check data metadata for additional information

**Validation Errors**
  - Review the error message to identify missing required fields
  - Complete all required fields before attempting export again

See Also
--------

- :ref:`Report_Results` - Generate analysis reports
- :ref:`Save_Project` - Save your SasView session
- :ref:`Fitting` - Model fitting functionality
- :ref:`Guinier_Analysis` - Guinier analysis tools

.. note::  This help document was last updated for SasView version 6.0

