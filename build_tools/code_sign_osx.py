"""
Listing all so and dylib files and signs them separetly.
Required for notarization.
"""
import glob
import itertools
import subprocess

so_list = glob.glob("SasView*.app/Contents/MacOS/**/*.so", recursive=True)
dylib_list = glob.glob("SasView*.app/Contents/MacOS/**/*.dylib", recursive=True)
dylib_list_resources = glob.glob(
    "SasView*.app/Contents/Resources/.dylibs/*.dylib", recursive=True
)
zmq_dylib_list_resources = glob.glob(
    "SasView*.app/Contents/Resources/zmq/.dylibs/*.dylib", recursive=True
)

pyside_QtWebEngineProcessApp = glob.glob(
    "SasView*.app/Contents/Resources/PySide6/Qt/lib/QtWebEngineCore.framework/Versions/A/Helpers/QtWebEngineProcess.app", recursive=True
)

pyside_QtWebEngineCore = glob.glob(
    "SasView*.app/Contents/Resources/PySide6/Qt/lib/QtWebEngineCore.framework/Versions/A/QtWebEngineCore", recursive=True
)

pyside_QtWebEngineProcess_Helpers = glob.glob(
    "SasView*.app/Contents/Resources/PySide6/Qt/lib/QtWebEngineCore.framework/Helpers/QtWebEngineProcess.app/Contents/MacOS/QtWebEngineProcess", recursive=True
)

pyside_Qtlibs = glob.glob(
    "SasView*.app/Contents/Resources/PySide6/Qt/lib/Qt*.framework/Versions/A/Qt*", recursive=True
)

#pyside_libs = pyside_QtWebEngineCore + pyside_QtWebEngineProcess

sign_command = ['codesign', '--timestamp', '--options=runtime', '--verify', '--verbose=4', '--force',
                '--sign',  'Developer ID Application: The International Scattering Alliance (8CX8K63BQM)']

sign_deep_command = ['codesign', '--timestamp', '--deep', '--options=runtime', '--verify', '--verbose=4', '--force',
                 '--sign',  'Developer ID Application: The International Scattering Alliance (8CX8K63BQM)']

#Signing QtWebEngineProcess.app first as it is a helper app
for sfile in itertools.chain(pyside_QtWebEngineProcessApp):
    sign_deep_command.append(sfile)
    subprocess.check_call(sign_deep_command)
    sign_deep_command.pop()

for sfile in itertools.chain(so_list, dylib_list,
                             dylib_list_resources,
                             zmq_dylib_list_resources,
                             pyside_QtWebEngineCore,
                             pyside_QtWebEngineProcess_Helpers,
                             pyside_Qtlibs):
    sign_command.append(sfile)
    if sfile == pyside_QtWebEngineProcess_Helpers:
        web_engine_sign = sign_command + ['--entitlements', 'SasView6.app/Contents/Frameworks/PySide6/Qt/lib/QtWebEngineCore.framework/Helpers/QtWebEngineProcess.app/Contents/Resources/QtWebEngineProcess.entitlements']
        subprocess.check_call(web_engine_sign)
    else:
        subprocess.check_call(sign_command)
    sign_command.pop()


