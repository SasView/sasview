# SasView Module Subdirectories Description

## Overview
The SasView module (`src/sas/`) is organized into several main subdirectories, each serving a specific purpose in the Small Angle Scattering analysis framework.

---

## Main Subdirectories

### **qtgui/**
- **Purpose**: Qt-based graphical user interface for SasView
- **Key Components**:
  - `Calculators/` - GUI components for various calculators (resolution, SLD, slit length)
  - `Perspectives/` - User interface perspectives and panels
  - `Plotting/` - Plotting and visualization functionality
  - `MainWindow/` - Main application window components
  - `UI/` - User interface definition files
  - `UnitTesting/` - GUI unit tests
  - `Utilities/` - Helper utilities for the GUI
  - `GL/` - OpenGL-related graphics functionality
  - `images/` - Image assets and icons
- **Details**: Full rewrite of the WxPython interface using PySide6 bindings with Twisted integration for asynchronous operations

---

### **sascalc/**
- **Purpose**: Core scientific calculations and data analysis engine
- **Key Submodules**:
  - `calculator/` - Various scientific calculators
    - Resolution calculator (instrument geometry calculations)
    - Slit length calculator (SAXSess instrument)
    - Scattering length density (SLD) calculator
    - Kiessig thickness calculator
    - GENI/GSC model utilities
    - ausaxs - Anomalous USAXS module
  - `fit/` - Fitting engine and model management
    - Abstract fit engine base classes
    - Bumps fitting framework integration
    - Model loader and plugin system
    - Q-space smearing calculations
    - Multiplication model capabilities
  - `pr/` - P(r) inversion module
    - Inversion calculations
    - Distance explorer for P(r) analysis
    - Number of terms optimization
  - `invariant/` - Porod invariant calculations
  - `corfunc/` - Correlation function analysis
  - `realspace/` - Real-space simulation tools
  - `shape2sas/` - Shape-to-scattering converter
  - `simulation/` - Scattering simulation utilities
  - `size_distribution/` - Size distribution analysis
  - `data_util/` - Data loading and manipulation utilities
- **Role**: Performs all numerical computations, data analysis, and scientific calculations independent of the GUI

---

### **qtgui/Perspectives/**
- **Purpose**: Modular UI perspectives for different analysis workflows
- **Details**: Pluggable interface modules that allow users to switch between different analysis tools and views

---

### **system/**
- **Purpose**: System-level configuration and utilities
- **Key Components**:
  - `config/` - Configuration management and settings
  - `version.py` - Version information
  - `log.py` - Logging configuration
  - `console.py` - Console utilities
  - `resources.py` - Resource management
  - `user.py` - User profile and settings
  - `lib.py` - System library utilities
  - `legal.py` - Legal and licensing information
  - `web.py` - Web service utilities
  - `zenodo.py` - Zenodo integration for data
  - `_help.py` - Help system integration
  - `_resources.py` - Internal resource handling
  - `_version.py` - Version tracking internals
- **Role**: Handles application configuration, resource loading, logging, version management, and system-level operations

---

### **webfit/**
- **Purpose**: Django-based web application for remote fitting and analysis
- **Key Components**:
  - `manage.py` - Django management script
  - `settings.py` - Django application settings
  - `urls.py` - URL routing configuration
  - `asgi.py` - ASGI server configuration
  - `wsgi.py` - WSGI server configuration
  - `serializers.py` - Data serialization for API endpoints
  - `analyze/` - Analysis module for web requests
  - `user_app/` - User management and authentication
  - `data/` - Data handling for web operations
  - `upload_example_data.py` - Example data upload utilities
  - `versioning.py` - API versioning
- **Role**: Provides a web-based interface and API for remote fitting and analysis operations

---

### **sasview/**
- **Purpose**: Legacy or secondary application resources
- **Components**:
  - `media/` - Media assets and resources
- **Details**: Contains application-level resources separate from GUI and calculation components

---

### **example_data/**
- **Purpose**: Sample and test data files for users
- **Details**: Contains example SAS data files for testing and learning purposes

---

### **cli.py**
- **Purpose**: Command-line interface for SasView
- **Details**: Enables non-GUI usage of SasView for scripting and batch processing

---

### **__main__.py**
- **Purpose**: Application entry point
- **Details**: Allows SasView to be run as a module with `python -m sas`

---

## Architecture Summary

| Component | Type | Purpose |
|-----------|------|---------|
| `qtgui/` | UI Layer | Desktop GUI with Qt/PyQt |
| `sascalc/` | Calculation Engine | Scientific computations and analysis |
| `system/` | Infrastructure | Configuration, logging, resources |
| `webfit/` | Web Layer | Remote fitting via web interface |
| `cli.py` | Interface | Command-line operations |

The architecture separates the calculation engine (`sascalc/`) from presentation layers (`qtgui/`, `webfit/`), allowing flexible deployment across desktop, web, and command-line environments.
