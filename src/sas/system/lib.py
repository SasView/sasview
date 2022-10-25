# Setup third-party libraries (e.g., sasview, periodictable, bumps)
import os

# TODO: Add api to control sasmodels rather than using environment variables
def setup_sasmodels():
    """Initialize sasmodels settings"""
    from .user import get_user_dir

    # Don't need to set SAS_MODELPATH for gui because sascalc.fit uses the
    # full paths to models, but when using the sasview package as a python
    # distribution for running sasmodels scripts we need to set SAS_MODELPATH
    # to the path used by SasView to store models.
    from sas.sascalc.fit.models import find_plugins_dir
    os.environ['SAS_MODELPATH'] = find_plugins_dir()

    # TODO: Use same mechanism as OpenCL/CUDA to manage the cache file path
    # Both scripts and gui need to know the stored DLL path.
    if "SAS_DLL_PATH" not in os.environ:
        os.environ["SAS_DLL_PATH"] = os.path.join(
            get_user_dir(), "compiled_models")

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
    from sasmodels.sasview_model import reset_environment
    from sas import config

    config.SAS_OPENCL = sas_opencl
    os.environ["SAS_OPENCL"] = sas_opencl
    # CRUFT: next version of reset_environment() will return env
    reset_environment()
