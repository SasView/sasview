"""
Listing all so and dylib files and signs them separetly
"""
import glob
import os

so_list = glob.glob("SasView5.0.app/Contents/MacOS/**/*.so", recursive=True)
dylib_list = glob.glob("SasView5.0.app/Contents/MacOS/**/*.dylib", recursive=True)


for sfile in so_list:
    os.system("codesign --verbose --force --sign \"Developer ID Application: European Spallation Source Eric (W2AG9MPZ43)\" "+sfile)

for dfile in dylib_list:
    os.system("codesign --verbose --force --sign \"Developer ID Application: European Spallation Source Eric (W2AG9MPZ43)\" "+dfile)

os.system("codesign --verbose --force --sign \"Developer ID Application: European Spallation Source Eric (W2AG9MPZ43)\" SasView5.0.app/Contents/MacOS/base_library.zip")

os.system("codesign --verbose --force --sign \"Developer ID Application: European Spallation Source Eric (W2AG9MPZ43)\" SasView5.0.app")