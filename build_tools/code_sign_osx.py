"""
Listing all so and dylib files and signs them separetly.
Required for notarization.
"""
import glob
import subprocess
import itertools

so_list = glob.glob("SasView*.app/Contents/MacOS/**/*.so", recursive=True)
dylib_list = glob.glob("SasView*.app/Contents/MacOS/**/*.dylib", recursive=True)
dylib_list_resources = glob.glob(
    "SasView*.app/Contents/Resources/.dylibs/*.dylib", recursive=True
)
zmq_dylib_list_resources = glob.glob(
    "SasView*.app/Contents/Resources/zmq/.dylibs/*.dylib", recursive=True
)

sign_command = ['codesign', '--timestamp', '--options=runtime', '--verify', '--verbose=4', '--force',
                '--sign', 'Developer ID Application: European Spallation Source Eric (W2AG9MPZ43)']


#TODO: Check if it is necesarry to do it per file (one long list maybe enough)
for sfile in itertools.chain(so_list, dylib_list, dylib_list_resources, zmq_dylib_list_resources):
    sign_command.append(sfile)
    subprocess.check_call(sign_command)
    sign_command.pop()

