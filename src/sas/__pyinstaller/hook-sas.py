# hook for pyinstaller to find all the extra parts of sas

import os
from pathlib import Path

try:
    from PyInstaller.utils.hooks import collect_data_files

    datas = collect_data_files(
        'sas',
        excludes=[
            # handle the documentation trees manually
            'docs/',
            'docs-source/',
            ],
        )

    # add in additional data files
    base = Path(__file__).parent.parent.parent

    for f, t in [
        # CRUFT: Files are duplicated here because different code paths
        # are looking for the same resource in different places
        ('sas/qtgui/images', 'images'),
        ('sas/qtgui/images', "sas/qtgui/images"),
        ('sas/sasview/media', 'media'),
        ('sas/sascalc/calculator/ausaxs/lib', 'sas/sascalc/calculator/ausaxs/lib'),
        ('sas/qtgui/Utilities/Reports/report_style.css', 'sas/qtgui/Utilities/Reports'),
        ('sas/qtgui/Perspectives/Fitting/plugin_models', 'plugin_models'),
        ('sas/qtgui/Utilities/WhatsNew/messages', 'sas/qtgui/Utilities/WhatsNew/messages'),
        ('sas/qtgui/Utilities/WhatsNew/css/style.css', 'sas/qtgui/Utilities/WhatsNew/css'),
        ('sas/qtgui/Utilities/About/images', 'sas/qtgui/Utilities/About/images'),
    ]:
        datas.append((str((base / f).absolute()), t))

    # Handle documentation trees separately:
    # There's a range of files here (html, css, js, json, png, py); the .py
    # files need particular care because they should be included in the documentation
    # tree even though pyinstaller would not normally include them. At the same
    # time, the __pycache__ and .pyc files should not included
    def append_data_files(src: Path):
        # CRUFT: Path.walk() needs Python 3.12 or later
        # for root, _, files in (base / src).walk():
        for root, _, files in os.walk(base / src):
            root = Path(root)
            if root.name == "__pycache__":
                continue

            for f in files:
                if f.endswith(".pyc"):
                    continue
                src = root / f
                dst = src.relative_to(base).parent
                datas.append((str(src), str(dst)))

    append_data_files("sas/docs-source")
    append_data_files("sas/docs")

    datas.sort()
    print("SasView added datas:")
    for s, d in datas:
        print(f"  {s}")
        print(f"  > {d}")

    hiddenimports = [
        "OpenGL",
        "OpenGL.platform.egl",
        "PyOpenGL",
        "pyopencl",
        'uncertainties',
    ]

    print(f"SasView added hiddenimports: {hiddenimports}")

except ImportError:
    # Inability to import PyInstaller isn't important at runtime or test time
    pass
