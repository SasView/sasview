from sas.sascalc.calculator.ausaxs.architecture import Arch, OS, determine_cpu_support, determine_os

def fetch_lib():
    arch = determine_cpu_support()
    os = determine_os()

    link = "github.com/sasview/ausaxs/releases/latest/"
    if (os is OS.WIN):
        if (arch is Arch.AVX):
            link += "win_avx"
        else:
            link += "win_generic"
    elif (os is OS.LINUX):
        if (arch is Arch.AVX):
            link += "linux_avx"
        else:
            link += "linux_generic"

    print(link)
