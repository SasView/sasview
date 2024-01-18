from sas.sascalc.calculator.detail.architecture import _arch, _os, determine_cpu_support, determine_os

def fetch_lib():
    arch = determine_cpu_support()
    os = determine_os()

    link = "github.com/sasview/ausaxs/releases/latest/"
    if (os is _os.WIN):
        if (arch is _arch.AVX):
            link += "win_avx"
        else:
            link += "win_generic"
    elif (os is _os.LINUX):
        if (arch is _arch.AVX):
            link += "linux_avx"
        else:
            link += "linux_generic"

    print(link)
