# hook for pyinstaller to find all the extra parts of sas

from pathlib import Path

try:
    from PyInstaller.utils.hooks import collect_data_files

    datas = collect_data_files('sas')

    # add in additional data files
    base = Path(__file__).parent.parent.parent

    for f, t in [
        # CRUFT: Files are duplicated here because different code paths
        # are looking for the same resource in different places
        ('sas/qtgui/images', 'images'),
        ('sas/qtgui/images', "sas/qtgui/images"),
        ('sas/sasview/media', 'media'),
        ('sas/example_data', 'example_data'),
        ('sas/sascalc/calculator/ausaxs/lib', 'sas/sascalc/calculator/ausaxs/lib'),
        ('sas/qtgui/Utilities/Reports/report_style.css', 'sas/qtgui/Utilities/Reports'),
        ('sas/qtgui/Perspectives/Fitting/plugin_models', 'plugin_models'),
        ('sas/qtgui/Utilities/WhatsNew/messages', 'sas/qtgui/Utilities/WhatsNew/messages'),
        ('sas/qtgui/Utilities/WhatsNew/css/style.css', 'sas/qtgui/Utilities/WhatsNew/css'),
        ('sas/qtgui/Utilities/About/images', 'sas/qtgui/Utilities/About/images'),
    ]:
        datas.append((str((base / f).absolute()), t))

    print(f"SasView added datas: {datas}")

    hiddenimports = [
        "pyopencl",
        'uncertainties',
    ]

    print(f"SasView added hiddenimports: {hiddenimports}")

except ImportError:
    # Inability to import PyInstaller isn't important at runtime or test time
    pass
