"""
Setup third-party libraries (e.g., qt, sasview, periodictable, bumps)

These functions are used to setup up the GUI and the scripting environment.
"""
import os


def setup_sasmodels():
    """Initialize sasmodels settings from the sasview configuration."""
    # Don't need to set SAS_MODELPATH for gui because sascalc.fit uses the
    # full paths to models, but when using the sasview package as a python
    # distribution for running sasmodels scripts we need to set SAS_MODELPATH
    # to the path used by SasView to store models.
    from sas.system.user import find_plugins_dir, get_app_dir
    os.environ['SAS_MODELPATH'] = find_plugins_dir()

    # TODO: Use same mechanism as OpenCL/CUDA to manage the cache file path
    # Both scripts and gui need to know the stored DLL path.
    if "SAS_DLL_PATH" not in os.environ:
        os.environ["SAS_DLL_PATH"] = os.path.join(
            get_app_dir(), "compiled_models")

    # Set OpenCL config from environment variable if it is set otherwise
    # use the value from the sas config file.
    from sas import config
    # Not using sas.system.env since it just adds a layer of confusion
    SAS_OPENCL = os.environ.get("SAS_OPENCL", None)
    if SAS_OPENCL is None:
        # Let sasmodels know the value of the config variable
        os.environ["SAS_OPENCL"] = config.SAS_OPENCL
    else:
        # Let config system know the value of the the environment variable
        config.SAS_OPENCL = SAS_OPENCL

def reset_sasmodels(sas_opencl):
    """
    Trigger a reload of all sasmodels calculators using the new value of
    sas_opencl. The new value will be saved in the sasview configuration file.
    """
    from sasmodels.sasview_model import reset_environment

    from sas import config

    config.SAS_OPENCL = sas_opencl
    os.environ["SAS_OPENCL"] = sas_opencl
    # CRUFT: next version of reset_environment() will return env
    reset_environment()

def setup_qt_env():
    """
    Setup the Qt environment.

    The environment values are set by the user and managed by sasview config.

    This function does not import the Qt libraries so it is safe to use from
    a script.
    """
    from sas import config

    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_SCALE_FACTOR"] = f"{config.QT_SCALE_FACTOR}"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1" if config.QT_AUTO_SCREEN_SCALE_FACTOR else "0"
