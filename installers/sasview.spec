# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path
import warnings
import platform
import sysconfig

block_cipher = None
PYTHON_PACKAGES = sysconfig.get_path('platlib')

datas = [
    ('../src/sas/qtgui/images', 'images'),
    ('../src/sas/sasview/media', 'media'),
    ('../src/sas/example_data', 'example_data'),
    ('../src/sas/qtgui/Utilities/Reports/report_style.css', 'sas/qtgui/Utilities/Reports'),
    ('../src/sas/qtgui/Perspectives/Fitting/plugin_models', 'plugin_models'),
    ('../src/sas/system/log.ini', 'sas/system/'),
    ('../../sasmodels/sasmodels','sasmodels'),
    ('../docs/sphinx-docs/build/html','doc')
]
#TODO: Hopefully we can get away from version specific packages
datas.append((os.path.join(PYTHON_PACKAGES, 'debugpy'), 'debugpy'))
datas.append((os.path.join(PYTHON_PACKAGES, 'jedi'), 'jedi'))
datas.append((os.path.join(PYTHON_PACKAGES, 'zmq'), 'zmq'))

def add_data(data):
    for component in data:
        target = component[0]
        for filename in component[1]:
           datas.append((filename, target))

import sasmodels
add_data(sasmodels.data_files())

try:
    import tinycc
    add_data(tinycc.data_files())
except ImportError:
    warnings.warn("TinyCC package is not available and will not be included")

import periodictable
add_data(periodictable.data_files())

hiddenimports = [
    'pyopencl',
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
    'uncertainties',
]

a = Analysis(
    ['sasview.py'],
    pathex=[],
    binaries=[],
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
          debug=False,
          upx=False,
          icon=os.path.join("../src/sas/qtgui/images","ball.icns"),
          version="version.txt",
          console=False )
else:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='sasview',
        debug=False,
        bootloader_ignore_signals=False,
        icon=os.path.join("../src/sas/qtgui/images","ball.ico"),
        strip=False,
        upx=True,
        console=False)

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
        name='SasView5.app',
        icon='../src/sas/qtgui/images/ball.icns',
        bundle_identifier='org.sasview.SasView5',
        info_plist={'NSHighResolutionCapable': 'True'})
