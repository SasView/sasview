cmake_minimum_required(VERSION 2.6)

# This will install a pyinstaller-generated sasview
project(sasview C)

# Define the version of sasview being packaged
option(SAS_VERSION "Define SASView version to package" off)

if (NOT ${SAS_VERSION})
  message(FATAL_ERROR "SASView version unspecified!\n"
    "Please use e.g. -DSAS_VERSION=4.1 ")
endif()

# main install work is done in this function
macro(installDir path)
  # Main install location is defined via CMAKE_INSTALL_PREFIX
  # - what is chosen here is a subdirectory
  install (
    DIRECTORY "${path}/"
    DESTINATION "sasview/${SAS_VERSION}"
    PATTERN "Makefile*" EXCLUDE  # skip makefiles
    PATTERN "#*"        EXCLUDE  # skip backup files
    PATTERN ".*"        EXCLUDE  # skip hidden files
    PATTERN "*.out"     EXCLUDE  # skip binary files
    PATTERN "*.*.in"    EXCLUDE  # skip configure processed template files
    PATTERN "*"
    PERMISSIONS OWNER_EXECUTE OWNER_WRITE OWNER_READ
    GROUP_EXECUTE GROUP_READ
    WORLD_EXECUTE WORLD_READ
  )
endmacro()

# CPack configuration
set(CPACK_PACKAGE_NAME          "sasview-${SAS_VERSION}")
set(CPACK_RESOURCE_FilE_LICENSE "${CMAKE_CURRENT_SOURCE_DIR}../../LICENSE.TXT")
set(CPACK_PACKAGE_CONTACT       "pkwi@fysik.dtu.dk")

set(CPACK_PACKAGE_VERSION       "1.0")
set(CPACK_PACKAGE_VERSION_MAJOR "1")
set(CPACK_PACKAGE_VERSION_MINOR "0")

# Have CPack respect install prefix
set(CPACK_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")
set(CPACK_PACKAGING_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Avoid e.g. /usr/local being "part" of the RPMs
set(CPACK_RPM_EXCLUDE_FROM_AUTO_FILELIST
  ${CMAKE_INSTALL_PREFIX}
  ${CMAKE_INSTALL_PREFIX}/bin
  ${CMAKE_INSTALL_PREFIX}/sasview
  )

installDir("${PROJECT_SOURCE_DIR}/sasview")

execute_process(COMMAND ln -s ${CMAKE_INSTALL_PREFIX}/sasview/${SAS_VERSION}/sasview sasview)
install(FILES ${CMAKE_BINARY_DIR}/sasview DESTINATION ${CMAKE_INSTALL_PREFIX}/bin/)

include(CPack)
