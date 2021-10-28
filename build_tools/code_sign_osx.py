"""
Listing all so and dylib files and signs them separetly.
Required for notarization.
"""
import glob
import subprocess
import itertools

so_list = glob.glob("SasView5.app/Contents/MacOS/**/*.so", recursive=True)
dylib_list = glob.glob("SasView5.app/Contents/MacOS/**/*.dylib", recursive=True)
dylib_list_resources = glob.glob(
    "SasView5.app/Contents/Resources/.dylibs/*.dylib", recursive=True
)

sign_command = ['codesign', '--timestamp', '--options=runtime', '--verify', '--verbose=4', '--force',
                '--sign \"Developer ID Application: European Spallation Source Eric (W2AG9MPZ43)\"']

for sfile in list(itertools.chain(so_list, dylib_list, dylib_list_resources)):
    exec_command = sign_command
    exec_command.append(sfile)
    subprocess.check_call(exec_command)

subprocess.check_call(sign_command.append("SasView5.app"))
sign_command.pop()
subprocess.check_call(sign_command.append("SasView5.dmg/SasView5.app/Contents/MacOS/sasview"))
