from enum import Enum

class _arch(Enum):
    NONE = 0
    SSE4 = 1
    AVX =  2

class _os(Enum):
    WIN = 0
    LINUX = 1
    MAC = 2
    UNKNOWN = 3

def determine_cpu_support():
    import cpufeature
    if cpufeature.CPUFeature["AVX"]:
        return _arch.AVX
    elif cpufeature.CPUFeature["SSE4"]:
        return _arch.SSE4
    else:
        return _arch.NONE
    
def determine_os():
    import platform
    if platform.system() == "Windows":
        return _os.WIN
    elif platform.system() == "Linux":
        return _os.LINUX
    elif platform.system() == "Darwin":
        return _os.MAC
    return _os.UNKNOWN