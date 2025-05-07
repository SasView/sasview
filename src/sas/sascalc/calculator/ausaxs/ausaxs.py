from sas.sascalc.calculator.ausaxs.detail.ausaxs_integration import AUSAXSLIB

# Note: The variable is initialized here, in a separate file from ausaxs_integration, 
# to avoid issues with multiprocessing. Usually one would query __main__ to 
# determine if the current process is the main process, but this is not possible
# as it is busy with the GUI event loop, meaning this would always return False.
ausaxslib = AUSAXSLIB()