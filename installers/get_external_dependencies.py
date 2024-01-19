import requests
import os

def get_ausaxs():
    from sas.sascalc.calculator.ausaxs import architecture
    _os = architecture.determine_os()
    arch = architecture.determine_cpu_support()

    url = "https://github.com/SasView/ausaxs/releases/latest/download/"
    lib = None
    if _os == architecture.OS.WIN:
        if arch == architecture.Arch.AVX:
            lib = "libausaxs_avx.dll"
        else:
            lib = "libausaxs.dll"
    elif _os == architecture.OS.LINUX:
        if arch == architecture.Arch.AVX:
            lib = "libausaxs_avx.so"
        else:
            lib = "libausaxs.so"
    # elif os == architecture.OS.MAC:
    #     if arch == architecture.Arch.AVX:
    #         url += "libausaxs_avx.dylib"
    #     else:
    #         url += "libausaxs.dylib"
    if lib is not None:
        os.makedirs("external", exist_ok=True)
        response = requests.get(url+lib)
        with open("external/libausaxs"+architecture.get_shared_lib_extension(), "wb") as f:
            f.write(response.content)

def get_external_dependencies(): 
    # surround with try/except to avoid breaking the build if the download fails
    try:
        get_ausaxs()
    except:
        return