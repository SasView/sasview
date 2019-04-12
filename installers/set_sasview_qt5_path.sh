#!/bin/bash

PyQt5='/PyQt5/Qt/plugins'
export QT_PLUGIN_PATH=$PWD$PyQt5

# fontconfig paths
if [ -d /etc/fonts ]; then
  export FONTCONFIG_PATH=/etc/fonts/
  export FONTCONFIG_FILE=/etc/fonts/fonts.conf
fi

