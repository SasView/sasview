#!/usr/bin/env python


def preparePackage( package, sourceRoot = "." ):

    import os
    isNT = os.name=='nt'
    
    package.changeRoot( sourceRoot )

    #------------------------------------------------------------
    #dependencies
    #
    #------------------------------------------------------------
    from distutils_adpt.paths.Paths import Paths

    #--------------------------------------------------------
    # now add subdirs
    #
    #iqPy
    package.addPurePython(
        sourceDir = 'iqPy/iqPy',
        destModuleName = 'sansModeling.iqPy' )

    clibLibs = []

    package.addCLib(
        headerExportDir = '.',
        libName = 'sansModeling_libiqPy',
        libDir = 'iqPy/libiqPy',
        libs = clibLibs,
        libdirs = [],
        include_dirs = ['libiqPy/tnt'],
        macros = [('BLD_PROCEDURE',None)],
        linkArgs = [] )

    #module
    modMacroList = [('BLD_PROCEDURE',None)]
        
    modLibs = clibLibs + ["sansModeling_libiqPy"]

    package.addModule(
        moduleDir = 'iqPy/iqPymodule',
        libs = modLibs,
        libdirs = [],
        include_dirs = [],
##         macros = [('BLD_PROCEDURE',None)],
        macros = modMacroList,
        dest = 'sansModeling.iqPy.iqPy' )

    #--------------------------------------------------------
    # now add subdirs
    #
    #geoshapepy
    package.addPurePython(
        sourceDir = 'geoshapespy/geoshapespy',
        destModuleName = 'sansModeling.geoshapespy' )

    clibLibs = ["sansModeling_libiqPy"]

    package.addCLib(
        headerExportDir = '.',
        libName = 'libgeoshapespy',
        libDir = 'geoshapespy/libgeoshapespy',
        libs = clibLibs,
        libdirs = [],
        include_dirs = [''],
        macros = [('BLD_PROCEDURE',None)],
        linkArgs = [] )

    #module
    modMacroList = [('BLD_PROCEDURE',None)]
        
    modLibs = clibLibs + ["libgeoshapespy"]

    package.addModule(
        moduleDir = 'geoshapespy/geoshapespymodule',
        libs = modLibs,
        libdirs = [],
##         macros = [('BLD_PROCEDURE',None)],
        macros = modMacroList,
        dest = 'sansModeling.geoshapespy.geoshapespy' )

    #--------------------------------------------------------
    # now add subdirs
    #
    #analmodel
    package.addPurePython(
        sourceDir = 'analmodelpy/analmodelpy',
        destModuleName = 'sansModeling.analmodelpy' )

    clibLibs = ["sansModeling_libiqPy", "libgeoshapespy"]

    package.addCLib(
        headerExportDir = '.',
        libName = 'libanalmodelpy',
        libDir = 'analmodelpy/libanalmodelpy',
        libs = clibLibs,
        libdirs = [],
        include_dirs = [''],
        macros = [('BLD_PROCEDURE',None)],
        linkArgs = [] )

    #module
    modMacroList = [('BLD_PROCEDURE',None)]
        
    modLibs = clibLibs + ["libanalmodelpy"]

    package.addModule(
        moduleDir = 'analmodelpy/analmodelpymodule',
        libs = modLibs,
        libdirs = [],
##         macros = [('BLD_PROCEDURE',None)],
        macros = modMacroList,
        dest = 'sansModeling.analmodelpy.analmodelpy' )


    #--------------------------------------------------------
    # now add subdirs
    #
    #pointsmodel
    package.addPurePython(
        sourceDir = 'pointsmodelpy/pointsmodelpy',
        destModuleName = 'sansModeling.pointsmodelpy' )

    clibLibs = ["sansModeling_libiqPy", "libgeoshapespy"]

    package.addCLib(
        headerExportDir = '.',
        libName = 'libpointsmodelpy',
        libDir = 'pointsmodelpy/libpointsmodelpy',
        libs = clibLibs,
        libdirs = [],
        include_dirs = [''],
        macros = [('BLD_PROCEDURE',None)],
        linkArgs = [] )

    #module
    modMacroList = [('BLD_PROCEDURE',None)]
        
    modLibs = clibLibs + ["libpointsmodelpy"]

    package.addModule(
        moduleDir = 'pointsmodelpy/pointsmodelpymodule',
        libs = modLibs,
        libdirs = [],
##         macros = [('BLD_PROCEDURE',None)],
        macros = modMacroList,
        dest = 'sansModeling.pointsmodelpy.pointsmodelpy' )


    package.addPurePython('.', destModuleName='sansModeling', recursive=0 )



if __name__ == "__main__":
    #------------------------------------------------------------
    #init the package
    from distutils_adpt.Package import Package
    package = Package('sansModeling_RealSpace', '0.1')

    preparePackage( package )

    package.setup()

