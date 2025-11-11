# SasView High-Level Architecture Diagram

## UML Class Diagram - SasView Dependencies

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                            ┌──────────────────┐                        │
│                            │   SasView App    │                        │
│                            │  (Main Entry)    │                        │
│                            │                  │                        │
│                            │ - cli.py         │                        │
│                            │ - __main__.py    │                        │
│                            └────────┬─────────┘                        │
│                                     │                                  │
│                    ┌────────────────┼────────────────┐                 │
│                    │                │                │                 │
│                    ▼                ▼                ▼                 │
│          ┌──────────────────┐ ┌──────────────┐ ┌────────────────────┐ │
│          │   QtGUI Module   │ │ SasCalc      │ │  System Module     │ │
│          │                  │ │              │ │                    │ │
│          │ - MainWindow     │ │ - fit/       │ │ - config           │ │
│          │ - Perspectives   │ │ - corfunc/   │ │ - version          │ │
│          │ - Plotting       │ │ - invariant/ │ │ - resources        │ │
│          │ - Calculators    │ │ - realspace/ │ │ - logger           │ │
│          │ - Utilities      │ │ - data_util/ │ └────────────────────┘ │
│          │                  │ │              │                        │
│          └────────┬─────────┘ └──────┬───────┘                        │
│                   │                  │                                │
│                   │ uses             │ imports                        │
│                   ▼                  ▼                                │
│          ┌────────────────────────────────────────────────┐           │
│          │                                                │           │
│          │      External Dependencies                     │           │
│          │                                                │           │
│          │  ┌─────────────┐  ┌──────────────┐           │           │
│          │  │   sasdata   │  │ sasmodels    │           │           │
│          │  │             │  │              │           │           │
│          │  │ - Datasets  │  │ - Models     │           │           │
│          │  │ - Data I/O  │  │ - Fitting    │           │           │
│          │  │ - Metadata  │  │ - Simulation │           │           │
│          │  └─────────────┘  └──────────────┘           │           │
│          │                                                │           │
│          │  ┌──────────────┐  ┌─────────────────┐       │           │
│          │  │    bumps     │  │   PySide6       │       │           │
│          │  │              │  │                 │       │           │
│          │  │ - Optimizer  │  │ - Qt Framework  │       │           │
│          │  │ - Fitting    │  │ - GUI Toolkit   │       │           │
│          │  │ - Algorithms │  │ - Widget lib    │       │           │
│          │  └──────────────┘  └─────────────────┘       │           │
│          │                                                │           │
│          │  ┌────────────────────────────────────────┐  │           │
│          │  │  Also uses: NumPy, SciPy, Matplotlib  │  │           │
│          │  │           H5PY, Twisted, etc          │  │           │
│          │  └────────────────────────────────────────┘  │           │
│          │                                                │           │
│          └────────────────────────────────────────────────┘           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Detailed Dependency Matrix

### Layer 1: Application Entry Points
- **sas.cli** - Command-line interface
- **sas.__main__** - Package main entry point

### Layer 2: Core Modules
- **sas.qtgui** - Qt-based graphical user interface
  - MainWindow: Main application window
  - Perspectives: Different analysis perspectives
  - Plotting: Data visualization
  - Calculators: Various calculation tools
  - Utilities: Helper utilities

- **sas.sascalc** - Scientific calculations
  - fit: Fitting algorithms
  - corfunc: Correlation function analysis
  - invariant: Invariant calculations
  - realspace: Real space calculations
  - data_util: Data utilities

- **sas.system** - System functionality
  - config: Configuration management
  - version: Version information
  - resources: Resource management
  - logger: Logging functionality

### Layer 3: External Package Dependencies

#### Critical Dependencies:
1. **sasdata** - Data handling and I/O
   - Dataset representation
   - File I/O (HDF5, ASCII, etc.)
   - Metadata management
   - Data validation

2. **sasmodels** - Scattering model library
   - Model definitions
   - Form factors
   - Structure factors
   - Model fitting interface

3. **bumps** - Optimization framework
   - Fitting algorithms
   - Parameter optimization
   - Uncertainty analysis
   - Bayesian inference

#### Supporting Dependencies:
- NumPy: Numerical computing
- SciPy: Scientific algorithms
- Matplotlib: Data plotting
- H5PY: HDF5 file handling
- Twisted: Asynchronous networking
- QtConsole: IPython integration
- Periodictable: Element/isotope data
- Uncertainties: Uncertainty calculations

## Dependency Flow

```
End User
  ↓
SasView CLI/GUI (sas.qtgui, sas.cli)
  ↓
┌─────────────────────────────────────┐
│    Core Calculation Layer           │
│ (sas.sascalc: fit, corfunc, etc)    │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│    External Libraries               │
│ ┌───────────────┐                   │
│ │  sasmodels    │(model definitions)│
│ │  sasdata      │(data handling)    │
│ │  bumps        │(optimization)     │
│ │  PySide6      │(UI framework)     │
│ └───────────────┘                   │
└─────────────────────────────────────┘
  ↓
Scientific Data/Algorithms
```

## Key Relationships

| Component | Depends On | Purpose |
|-----------|-----------|---------|
| qtgui | sasdata, sasmodels, bumps, sascalc | Interactive data analysis GUI |
| sascalc | sasdata, sasmodels, bumps, numpy, scipy | Scientific calculations |
| qtgui.Plotting | matplotlib, numpy | Data visualization |
| qtgui.MainWindow | PySide6, sascalc, sasdata | Main application window |
| fit module | bumps, numpy, scipy | Parameter optimization |
| All modules | system.config | Configuration access |
