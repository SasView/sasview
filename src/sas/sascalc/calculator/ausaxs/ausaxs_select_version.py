def create_symlink_lib():
    """
    Create a symlink to the appropriate libausaxs shared library.
    This will either be libausaxs_avx or libausaxs_sse, depending on the CPU support.
    """
    from sas.sascalc.calculator.ausaxs import architecture
    _os = architecture.determine_os()
    _arch = architecture.determine_cpu_support()

    version = None
    if _os == architecture.OS.WIN:
        if _arch == architecture.Arch.AVX:
            version = "external/libausaxs_avx.dll"
        elif _arch == architecture.Arch.SSE4:
            version = "external/libausaxs_sse.dll"
    elif _os == architecture.OS.LINUX:
        if _arch == architecture.Arch.AVX:
            version = "external/libausaxs_avx.so"
        elif _arch == architecture.Arch.SSE4:
            version = "external/libausaxs_sse.so"
    elif _os == architecture.OS.MAC:
        if _arch == architecture.Arch.AVX:
            version = "external/libausaxs_avx.dylib"
        elif _arch == architecture.Arch.SSE4:
            version = "external/libausaxs_sse.dylib"
    
    if version is not None and os.path.exists(version):
        try:
            import os
            os.symlink(version, "external/libausaxs"+architecture.get_shared_lib_extension())
        except:
            return