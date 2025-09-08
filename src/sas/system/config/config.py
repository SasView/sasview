r""" Configuration class - stores configuration information for SasView


..
                  _____  ________      _______ _
                 |  __ \|  ____\ \    / / ____| |
                 | |  | | |__   \ \  / / (___ | |
                 | |  | |  __|   \ \/ / \___ \| |
                 | |__| | |____   \  /  ____) |_|
                 |_____/|______|   \/  |_____/(_)


..
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
three main reasons for this:

  1) They have a tendency to accumulate junk because people dont realise that a
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

from sas.system.config.config_meta import ConfigBase, ConfigMeta


class Config(ConfigBase, metaclass=ConfigMeta):

    def __init__(self):
        super().__init__()


        # edit the list of file state your plugin can read
        self.APPLICATION_WLIST = 'SasView files (*.svs)|*.svs'
        self.APPLICATION_STATE_EXTENSION = '.svs'
        self.PLUGIN_STATE_EXTENSIONS = ['.fitv', '.inv', '.prv', '.crf']
        self.PLUGINS_WLIST = [
            'Fitting files (*.fitv)|*.fitv',
            'Invariant files (*.inv)|*.inv',
            'P(r) files (*.prv)|*.prv',
            'Corfunc files (*.crf)|*.crf']

        self.ANALYSIS_TYPES = [
            'Fitting files (*.fitv)',
            'Invariant files (*.inv)',
            'P(r) files (*.prv)',
            'Corfunc files (*.crf)']

        self.SHOW_WELCOME_PANEL = False



        # OpenCL option - should be a string, either, "none", a number, or pair of form "A:B"
        self.SAS_OPENCL = "none"

        self.DEFAULT_OPEN_FOLDER = ""
        self.TOOLBAR_SHOW = True
        self.DEFAULT_PERSPECTIVE = "Fitting"

        # Default threading model
        self.USING_TWISTED = False

        # Time out for updating sasview
        self.UPDATE_TIMEOUT = 2

        self.SHOW_EXIT_MESSAGE = True

        # Window scaling values
        self.QT_SCALE_FACTOR = 1.0
        self.QT_AUTO_SCREEN_SCALE_FACTOR = False

        # If True, use an ugly but more robust legend plotting method in Fitting that results in full-
        # width legends.
        self.FITTING_PLOT_FULL_WIDTH_LEGENDS = False

        # If True, truncates names in Fitting plot legends such that each name is maximum one line.
        self.FITTING_PLOT_LEGEND_TRUNCATE = False

        # sets the maximum number of characters per Fitting plot legend entry.
        self.FITTING_PLOT_LEGEND_MAX_LINE_LENGTH = 30

        # Residuals management
        # If true, disables residual plot display
        self.DISABLE_RESIDUAL_PLOT = False

        # Polydispersity plot management
        # If true, disables polydispersity plot display
        self.DISABLE_POLYDISPERSITY_PLOT = True

        # Using Matplotlib Toolbar in Main Plotting Function
        self.USE_MATPLOTLIB_TOOLBAR = True

        # Default fitting optimizer
        self.FITTING_DEFAULT_OPTIMIZER = 'lm'

        # What's New variables
        self.LAST_WHATS_NEW_HIDDEN_VERSION = "6.0.1"

        # Last version that the update prompt was dismissed for
        self.LAST_UPDATE_DISMISSED_VERSION = "5.0.0"

        #
        # Lock the class down, this is necessary both for
        # securing the class, and for setting up reading/writing files
        #
        self.finalise()



config = Config()
