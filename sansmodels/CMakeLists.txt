# CMakeLists for SANS models
cmake_minimum_required (VERSION 2.6)
project (SansModels)

# Version number
set (SansModels_VERSION_MAJOR 1)
set (SansModels_VERSION_MAJOR 0)

set (SRC_FILES
    src/c_models/librefl.c
    src/c_models/binaryHS.cpp
    src/c_models/onion.cpp
    src/c_models/vesicle.cpp
    src/c_models/sld_cal.cpp
    src/c_models/parallelepiped.cpp
    src/c_models/coreshellcylinder.cpp
    src/c_models/logNormal.cpp
    src/c_models/StickyHS.cpp
    src/c_models/triaxialellipsoid.cpp
    src/c_models/coreshellsphere.cpp
    src/c_models/HayterMSA.cpp
    src/c_models/csparallelepiped.cpp
    src/c_models/fractal.cpp
    src/c_models/spheresld.cpp
    src/c_models/parameters.cpp
    src/c_models/cylinder.cpp
    src/c_models/schulz.cpp
    src/c_models/gamma_win.c
    src/c_models/libfunc.c
    src/c_models/lamellar.cpp
    src/c_models/stackeddisks.cpp
    src/c_models/bcc.cpp
    src/c_models/lamellarPS_HG.cpp
    src/c_models/ellipticalcylinder.cpp
    src/c_models/refl_adv.cpp
    src/c_models/barbell.cpp
    src/c_models/spheroid.cpp
    src/c_models/lamellarPC.cpp
    src/c_models/binaryHS_PSF11.cpp
    src/c_models/sphere.cpp
    src/c_models/DiamEllip.cpp
    src/c_models/pearlnecklace.cpp
    src/c_models/SquareWell.cpp
    src/c_models/refl.cpp
    src/c_models/multishell.cpp
    src/c_models/polygausscoil.cpp
    src/c_models/corefourshell.cpp
    src/c_models/lamellarFF_HG.cpp
    src/c_models/flexcyl_ellipX.cpp
    src/c_models/capcyl.cpp
    src/c_models/fuzzysphere.cpp
    src/c_models/lamellarPS.cpp
    src/c_models/Hardsphere.cpp
    src/c_models/hollowcylinder.cpp
    src/c_models/fcc.cpp
    src/c_models/ellipsoid.cpp
    src/c_models/lorentzian.cpp
    src/c_models/rpa.cpp
    src/c_models/gaussian.cpp
    src/c_models/sc.cpp
    src/c_models/DiamCyl.cpp
    src/c_models/flexiblecylinder.cpp
    src/libigor/libStructureFactor.c
    src/libigor/libCylinder.c
    src/libigor/GaussWeights.c
    src/libigor/libTwoPhase.c
    src/libigor/libSphere.c
    )

set ( INC_FILES
    src/c_models/gamma_win.h
    src/c_models/parameters.hh
    src/c_models/dispersion_visitor.hh
    src/include/sphere.h
    src/include/hollow_cylinder.h
    src/include/binaryHS.h
    src/include/multishell.h
    src/include/sc.h
    src/include/StickyHS.h
    src/include/vesicle.h
    src/include/flexible_cylinder.h
    src/include/csparallelepiped.h
    src/include/flexcyl_ellipX.h
    src/include/gaussian.h
    src/include/lamellarPC.h
    src/include/ellipsoid.h
    src/include/stacked_disks.h
    src/include/SquareWell.h
    src/include/lamellarFF_HG.h
    src/include/lamellarPS_HG.h
    src/include/lorentzian.h
    src/include/fractal.h
    src/include/lamellarPS.h
    src/include/cylinder.h
    src/include/elliptical_cylinder.h
    src/include/schulz.h
    src/include/Hardsphere.h
    src/include/refl_adv.h
    src/include/barbell.h
    src/include/spheresld.h
    src/include/parallelepiped.h
    src/include/pearlnecklace.h
    src/include/sld_cal.h
    src/include/logNormal.h
    src/include/spheroid.h
    src/include/HayterMSA.h
    src/include/polygausscoil.h
    src/include/corefourshell.h
    src/include/fcc.h
    src/include/triaxial_ellipsoid.h
    src/include/capcyl.h
    src/include/DiamCyl.h
    src/include/onion.h
    src/include/bcc.h
    src/include/core_shell_cylinder.h
    src/include/lamellar.h
    src/include/rpa.h
    src/include/core_shell.h
    src/include/fuzzysphere.h
    src/include/refl.h
    src/include/DiamEllip.h
    src/libigor/GaussWeights.h
    src/libigor/libSANSAnalysis.h
    src/libigor/StandardHeaders.h
    src/libigor/libTwoPhase.h
    src/libigor/winFuncs.h
    src/libigor/libCylinder.h
    src/libigor/libSphere.h
    src/libigor/libStructureFactor.h

)
    
include_directories (src/libigor src/include src/c_models)

# Add the target for this directory
add_library ( Models ${SRC_FILES} ${INC_FILES})
