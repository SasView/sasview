# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path
import warnings
import platform
import sysconfig

block_cipher = None
PYTHON_PACKAGES = sysconfig.get_path('platlib')

datas = []

#TODO: Hopefully we can get away from version specific packages
datas.append((os.path.join(PYTHON_PACKAGES, 'debugpy'), 'debugpy'))
datas.append((os.path.join(PYTHON_PACKAGES, 'jedi'), 'jedi'))
datas.append((os.path.join(PYTHON_PACKAGES, 'zmq'), 'zmq'))
datas.append(('../src/sas/example_data', './example_data'))

def add_data(data):
    for component in data:
        target = component[0]
        for filename in component[1]:
           datas.append((filename, target))

try:
    import tccbox
    datas.append((os.path.join(PYTHON_PACKAGES, 'tccbox'), 'tccbox'))
except ImportError:
    warnings.warn("TCCbox package is not available and will not be included")

import periodictable
add_data(periodictable.data_files())

hiddenimports = [
    'setuptools._distutils',
    'reportlab',
    'reportlab.graphics',
    'reportlab.graphics.barcode.common',
    'reportlab.graphics.barcode.code128',
    'reportlab.graphics.barcode.code93',
    'reportlab.graphics.barcode.code39',
    'reportlab.graphics.barcode.lto',
    'reportlab.graphics.barcode.qr',
    'reportlab.graphics.barcode.usps',
    'reportlab.graphics.barcode.usps4s',
    'reportlab.graphics.barcode.eanbc',
    'reportlab.graphics.barcode.ecc200datamatrix',
    'reportlab.graphics.barcode.fourstate',
    'xmlrpc',
    'xmlrpc.server',
    'debugpy',
    'debugpy._vendored',
    'tccbox',
]

if platform.system() == 'Windows':
    # Need win32 to run sasview from the command line.
    hiddenimports.extend([
        'win32',
        'win32.win32console',
    ])

a = Analysis(
    ['sasview.py'],
    pathex=[],
    binaries=[('../src/sas/sascalc/calculator/ausaxs/lib', 'sas/sascalc/calculator/ausaxs/lib')],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

if platform.system() == 'Darwin':
    exe = EXE(
          pyz,
          a.scripts,
          exclude_binaries=True,
          name='sasview',
          contents_directory='.',
          debug=False,
          upx=True,
          icon=os.path.join("../src/sas/qtgui/images","ball.icns"),
          version="version.txt",
          console=False)
else:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='sasview',
        contents_directory='.',
        debug=False,
        bootloader_ignore_signals=False,
        icon=os.path.join("../src/sas/qtgui/images","ball.ico"),
        strip=False,
        upx=True,
        console=True,
        hide_console='hide-early')

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='sasview'
)

if platform.system() == 'Darwin':
    app = BUNDLE(coll,
        name='SasView6.app',
        icon='../src/sas/qtgui/images/ball.icns',
        bundle_identifier='org.sasview.SasView6',
        info_plist={'NSHighResolutionCapable': 'True'})
