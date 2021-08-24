"""
Listing all so and dylib files and signs them separetly.
Required for notarization.
"""
import glob
import os

so_list = glob.glob("SasView5.app/Contents/MacOS/**/*.so", recursive=True)
dylib_list = glob.glob("SasView5.app/Contents/MacOS/**/*.dylib", recursive=True)
dylib_list_resources = glob.glob("SasView5.app/Contents/Resources/.dylibs/*.dylib", recursive=True)

for sfile in so_list + dylib_list + dylib_list_resources:
    os.system(
        'codesign  --timestamp --options runtime --verify --verbose=4 --force --sign "Developer ID Application: European Spallation Source Eric (W2AG9MPZ43)" '
        + sfile
    )

os.system(
    'codesign --timestamp --options runtime --verify --verbose=4 --force --sign "Developer ID Application: European Spallation Source Eric (W2AG9MPZ43)" SasView5.app'
)
