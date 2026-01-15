.. sasbdb_download_help.rst

.. _SASBDB_Download:

Loading Datasets from SASBDB
=============================

Description
-----------

The SASBDB (Small Angle Scattering Biological Data Bank) download feature allows you to directly download and load datasets from the SASBDB database into SasView. This feature provides easy access to published small-angle scattering data and automatically populates metadata from the SASBDB entry.

Accessing the Feature
---------------------

To access the SASBDB download feature:

1. Select **File > Load from SASBDB...** from the main menu
2. A dialog will appear prompting you to enter a SASBDB dataset identifier

Dataset Identifier
------------------

Enter a valid SASBDB dataset identifier in the input field. The identifier can be:

- A 7-character SASBDB code (e.g., ``SASDN24``, ``SASDB1234``)
- The identifier is case-insensitive and will be automatically normalized

Examples of valid identifiers:
- ``SASDN24``
- ``sasdn24`` (will be converted to uppercase)

Download Process
----------------

When you click **Download and Load**:

1. **Validation**: The dataset identifier is validated
2. **Metadata Retrieval**: The system fetches metadata from the SASBDB REST API
3. **Data Download**: The experimental data file is downloaded to a temporary location
4. **Data Loading**: The downloaded data is automatically loaded into SasView
5. **Metadata Population**: Metadata from SASBDB is automatically populated into the loaded dataset

Progress Indicator
------------------

During the download process, you will see:

- A progress bar indicating the download is in progress
- Status messages showing the current operation
- A success message with a summary of the loaded dataset

Metadata Population
--------------------

When a dataset is loaded from SASBDB, the following metadata is automatically extracted and populated:

**Sample Information:**
- Sample name (from molecule name, type, and oligomeric state)
- Temperature
- Concentration
- Buffer description and pH

**Instrument Information:**
- Instrument/beamline name
- Detector information
- Location (city, country)
- Source type (X-ray synchrotron, neutron, etc.)

**Experimental Parameters:**
- Wavelength
- Temperature
- Q-range (if available)

**Structural Parameters:**
- Radius of gyration (Rg) with errors
- I(0) with errors
- Maximum dimension (Dmax)
- Molecular weight (MW) with method
- Porod volume

**Publication Information:**
- Authors
- DOI
- PMID

Viewing Metadata
----------------

After loading a SASBDB dataset, you can view the populated metadata by:

1. Right-clicking on the loaded dataset in the Data Explorer
2. Selecting **Data Info** from the context menu
3. The metadata will be displayed in a clean, formatted section labeled "SASBDB Metadata"

The metadata is displayed in a compact format with key information organized by category:
- Entry code and instrument information
- Sample details (name, temperature, concentration, buffer)
- Source wavelength
- Structural parameters (Rg, I(0), Dmax, MW, etc.)
- Publication information

Error Handling
--------------

If an error occurs during download:

- An error message will be displayed explaining the issue
- Common errors include:
  - Invalid dataset identifier format
  - Dataset not found in SASBDB
  - Network connection issues
  - API service unavailable

If you encounter errors:

1. Verify the dataset identifier is correct
2. Check your internet connection
3. Try again after a few moments if the SASBDB service is temporarily unavailable

Tips
----

- **Dataset Identifiers**: You can find SASBDB dataset identifiers in published papers or on the SASBDB website (https://www.sasbdb.org)
- **Metadata**: All metadata is automatically extracted from the SASBDB entry, so you don't need to manually enter it
- **Data Format**: The downloaded data is in a standard format compatible with SasView
- **Offline Use**: Once downloaded, the data file is stored locally and can be used offline

Related Documentation
---------------------

- :ref:`SASBDB Export <SASBDB_Export>` - Export your data to SASBDB format
- `SASBDB Website <https://www.sasbdb.org>`_ - Browse and search the SASBDB database
- `SASBDB REST API Documentation <https://www.sasbdb.org/rest-api/docs/>`_ - Technical API reference

