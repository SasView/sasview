r""" Configuration class - stores configuration information for SasView


                  _____  ________      _______ _
                 |  __ \|  ____\ \    / / ____| |
                 | |  | | |__   \ \  / / (___ | |
                 | |  | |  __|   \ \/ / \___ \| |
                 | |__| | |____   \  /  ____) |_|
                 |_____/|______|   \/  |_____/(_)


 _____  ______          _____       _______ _    _ _____  _____ _
 |  __ \|  ____|   /\   |  __ \     |__   __| |  | |_   _|/ ____| |
 | |__) | |__     /  \  | |  | |       | |  | |__| | | | | (___ | |
 |  _  /|  __|   / /\ \ | |  | |       | |  |  __  | | |  \___ \| |
 | | \ \| |____ / ____ \| |__| |       | |  | |  | |_| |_ ____) |_|
 |_|  \_\______/_/    \_\_____/        |_|  |_|  |_|_____|_____/(_)



If you're looking to change a field in the config file, you should read this



Configs
=======

Configs are a nightmare from the perspective of code maintainability. There are
three main reasons for this
  1) They have a tendency to accumulate junk because people don't realise that a
     config item is no longer needed
  2) It's hard to trace the usages and types because values are loaded at runtime
  3) Maintaining synchrony between config files and config usages is difficult, as
     it is the users that have control over the config files.

The Config class here attempts to resolve some of these issues in a way that
preserves as many of the current uses as possible. It is a compromise between
SasView's current methods, and more standard ways of handling configurations.

Brief Outline
=============

The main Config class provides a definition of the variables allowed in a config
file, along with their default values. This class is used to generate a schema
that determines how config files are read. Only a few types of variable are allowed

* bool
* int
* float
* str
* Homogeneous lists of the above, to 10 levels of depth
* None and empty list (please try to avoid)

Other types will throw an error at runtime when the schema is created.

None types and
empty lists have no type information at runtime, so the schema cannot check/coerce
the type of config variables when they are loaded. It is best to avoid having these
as default values if possible.

The presence of a config file is not necessary for the functioning of the config
system, only for making changes that differ from the default values.


What Belongs in a Config
========================

Things that do belong:
  1) Program settings that are configurable by users through the GUI
  2) Program settings that have no GUI editor, but that some advanced users
     might want to set manually with a text editor
  3) Settings that control developer tools, e.g. debug modes
  4) Very little else

Things that don't belong, but were previously in the config:
  1) dynamic content, i.e. values that are modified programmatically,
    this includes variables that are defined in terms of other variables,
    but otherwise don't change
  2) Paths to resources within sasview (use importlib.resources instead)
  3) Blocks of data that won't be modified by the user and used primarily
     by single class - e.g. the text for a message
  4) Large blocks of text in general

Making Changes to the Config Class
==================================

As users have their own copy of the sasview configuration, deletions,
name changes, default value changes, and variable type changes
often constitute a breaking change from the perspective of version
control. The users locally stored config will, in general, not be
backwards compatible with the new config. Extreme caution should be
exercised - when changing the config, don't just think about the
problem at hand, but about the future maintainability of SasView in
general.

Adding to the Config class:
Before adding a variable, think about whether it might more properly
belong somewhere else, perhaps in the web or legal classes in the
system package.
Remember that config variables are accessed across the whole of sasview
and that names need to be suitably descriptive.

Deleting from the Config class:
Currently (02/09/2022) the consequences of providing an entry in a
config file that is not properly reflected in the Config class is a
error. To ease backward compatibility, it is possible to disable
the errors for a deleted class member by adding their name to
the `_deleted_attributes` list. The suggested deletion process would
be

```
[-]   self.my_variable = 10
[+]   self._deleted_attributes.append("my_variable")
```

At major releases, additions to _deleted_attributes should be removed.


Other Design Decisions made for the Config Class
================================================

The Config class cannot be dynamically modified, this prevents the config
from having fields that are unspecified in the base class,
and makes it so that all usages of fields can be automatically tracked.

Subclassing of Config is also disabled for similar reasons.

I have opted not to use frozen dataclasses at this time
because, as they currently work, the behaviour would make creating
different configs difficult.
"""

from sas.config_system.config_meta import ConfigBase, ConfigMeta

import sas.sasview
import os
import time
import logging


class Config(ConfigBase, metaclass=ConfigMeta):

    def __init__(self):
        super().__init__()

        # Version of the application
        self.__appname__ = "SasView"
        self.__version__ = sas.sasview.__version__
        self.__build__ = sas.sasview.__build__

        # Debug message flag
        self.__EVT_DEBUG__ = False

        # Flag for automated testing
        self.__TEST__ = False

        # Debug message should be written to a file?
        self.__EVT_DEBUG_2_FILE__ = False
        self.__EVT_DEBUG_FILENAME__ = "debug.log"

        # About box info
        self._do_aboutbox = True
        self._do_acknowledge = True
        self._do_tutorial = True

        self.icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "images"))
        # logging.info("icon path: %s" % icon_path)
        self.media_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "media"))
        self.test_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "test"))


        self._corner_image = os.path.join(self.icon_path, "angles_flat.png")
        self._welcome_image = os.path.join(self.icon_path, "SVwelcome.png")

        # edit the list of file state your plugin can read
        self.APPLICATION_WLIST = 'SasView files (*.svs)|*.svs'
        self.APPLICATION_STATE_EXTENSION = '.svs'
        self.GUIFRAME_WIDTH = 1150
        self.GUIFRAME_HEIGHT = 840
        self.PLUGIN_STATE_EXTENSIONS = ['.fitv', '.inv', '.prv', '.crf']
        self.PLUGINS_WLIST = ['Fitting files (*.fitv)|*.fitv',
                         'Invariant files (*.inv)|*.inv',
                         'P(r) files (*.prv)|*.prv',
                         'Corfunc files (*.crf)|*.crf']
        self.PLOPANEL_WIDTH = 415
        self.PLOPANEL_HEIGTH = 370
        self.DATAPANEL_WIDTH = 235
        self.DATAPANEL_HEIGHT = 700
        self.SPLASH_SCREEN_PATH = os.path.join(self.icon_path, "SVwelcome_mini.png")
        self.TUTORIAL_PATH = os.path.join(self.media_path, "Tutorial.pdf")

        self.DEFAULT_STYLE = 64

        self.SPLASH_SCREEN_WIDTH = 512
        self.SPLASH_SCREEN_HEIGHT = 366
        self.SS_MAX_DISPLAY_TIME = 2000
        self.WELCOME_PANEL_ON = True
        self.WELCOME_PANEL_SHOW = False
        self.CLEANUP_PLOT = False
        # OPEN and SAVE project menu
        self.OPEN_SAVE_PROJECT_MENU = True
        # VIEW MENU
        self.VIEW_MENU = True
        # EDIT MENU
        self.EDIT_MENU = True

        self.SetupIconFile_win = os.path.join(self.icon_path, "ball.ico")
        self.SetupIconFile_mac = os.path.join(self.icon_path, "ball.icns")
        self.DefaultGroupName = "."
        self.OutputBaseFilename = "setupSasView"

        self.FIXED_PANEL = True
        self.DATALOADER_SHOW = True
        self.CLEANUP_PLOT = False
        self.WELCOME_PANEL_SHOW = False
        # Show or hide toolbar at the start up
        self.TOOLBAR_SHOW = True
        # set a default perspective
        self.DEFAULT_PERSPECTIVE = 'None'

        # Time out for updating sasview
        self.UPDATE_TIMEOUT = 2

        # OpenCL option
        self.SAS_OPENCL = None

        self.DATAPANEL_WIDTH = -1
        self.CLEANUP_PLOT = False
        self.FIXED_PANEL = True
        self.PLOPANEL_WIDTH = -1
        self.DATALOADER_SHOW = True
        self.GUIFRAME_HEIGHT = -1
        self.GUIFRAME_WIDTH = -1
        self.CONTROL_WIDTH = -1
        self.CONTROL_HEIGHT = -1
        self.DEFAULT_OPEN_FOLDER = None
        self.WELCOME_PANEL_SHOW = False
        self.TOOLBAR_SHOW = True
        self.DEFAULT_PERSPECTIVE = "Fitting"
        self.SAS_OPENCL = "None"

        # Logging options
        self.FILTER_DEBUG_LOGS = True

        # Default threading model
        self.USING_TWISTED = False

        # Time out for updating sasview
        self.UPDATE_TIMEOUT = 2


        #
        # Lock the class down, this is necessary both for
        # securing the class, and for setting up reading/writing files
        #
        self.finalise()

    def printEVT(self, message):
        if self.__EVT_DEBUG__:
            """
            :TODO - Need method doc string
            """
            print("%g:  %s" % (time.clock(), message))

            if self.__EVT_DEBUG_2_FILE__:
                out = open(self.__EVT_DEBUG_FILENAME__, 'a')
                out.write("%10g:  %s\n" % (time.clock(), message))
                out.close()






