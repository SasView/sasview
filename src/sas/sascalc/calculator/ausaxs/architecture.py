from enum import Enum

class Arch(Enum):
    NONE = 0
    SSE4 = 1
    AVX =  2

class OS(Enum):
    WIN = 0
    LINUX = 1
    MAC = 2
    UNKNOWN = 3

def determine_cpu_support():
    """
    Get the highest level of CPU support for SIMD instructions.
    """
    import cpufeature
    if cpufeature.CPUFeature["AVX"]:
        return Arch.AVX
    elif cpufeature.CPUFeature["SSE4"]:
        return Arch.SSE4
    else:
        return Arch.NONE
    
def determine_os():
    """
    Get the operating system of the current machine.
    """
    import platform
    if platform.system() == "Windows":
        return OS.WIN
    elif platform.system() == "Linux":
        return OS.LINUX
    elif platform.system() == "Darwin":
        return OS.MAC
    return OS.UNKNOWN