# Quick Intro for Building SasView

Whether you're installing SasView to use as a tool for your research or
because you're wanting to work on the code, it is recommended that you
work inside a Python virtual environment of some sort.
A `venv` or a `Pixi` are both popular choices.

## Installing SasView as a User

Installers for SasView can be found at [https://www.sasview.org/](https://www.sasview.org/),
for various operating systems. You will also find walk through tutorials on how to install and use SasView.
Note that SasView requires Python 3.12+.

You can also install SasView using standard Python installation tools, such as
- `uv tool install sasview` (or `pipx install sasview`) to install it into its own standalone
environment
- or `uv pip install sasview` (or `pip install sasview`) to install it into your current Python environment.

## Making a SasView Development Environment

### Develop using `venv`

If you're familiar with working with developing in Python, then the very quick version is:

```shell
# clone the repository
git clone https://github.com/sasview/sasdata/
git clone https://github.com/sasview/sasmodels/
git clone https://github.com/sasview/sasview/

cd sasview

# create the virtual environment
python -m venv .venv
# .venv\Scripts\activate & REM Windows: activate environment
. .venv/bin/activate  # Linux/Mac: activate environment

# install repositories in editable/developer mode in the venv
# use "python -m ..." to ensure the venv's pip is used
python -m pip install -e ../sasdata
python -m pip install -e ../sasmodels
python -m pip install -e .[dev,test]

# test if sasview launches
python -m sas
```

Step by step, that is:

1.  Obtain the SasView source using `git`. You will likely need to coordinate
    updates to `sasdata` and `sasmodels`. The
    [`bumps`](https://github.com/bumps/bumps) and
    [`periodictable`](https://github.com/python-periodictable/periodictable)
    packages are far more loosely coupled, but depending on what you are
    doing you may also want them as development packages.
1.  Create a Python virtual environment in the `.venv` directory.
1.  Activate the `.venv` so that Python and its modules from the venv are used.
    Note that the particular syntax above works for the `bash` and `zsh` shells under Linux, Windows and macOS;
    if you use `cmd` or PowerShell under windows, there are
    [different ways](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#create-and-use-virtual-environments)
    to activate the virtual environment.
 1. Install the necessary modules for building and running SasView, including the documentation and GUI.
    It will take a while to download and unpack all the dependencies.
    The `pip install -e` command says to install the package in development mode
    so that any changes you make in the source tree will be available the
    next time you run the program. We execute this using the `python -m` syntax in order to ensure that the virtual environment python is used. The `.[dev,test]` syntax says to install
    the current directory (sasview) with test and dev dependencies.
 1. Run SasView! As an alternative to typing `python -m sas`, you can simply type `sasview`.

Almost all the modules that SasView needs are available as precompiled modules
on PyPI, including numpy, scipy, h5py, pyside6. A handful of Python-only
modules will be built into wheels on your local machine. Installing the
dependencies should be a one-off task.

When you want to work on SasView again at a later date, you can type:

```shell
# .venv\Scripts\activate  & REM Windows: activate environment
. .venv/bin/activate  # Linux/Mac: activate environment
python -m sas
```

(or the [equivalent command](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#create-and-use-virtual-environments) for your shell to activate the venv)

Note that many Python-focused integrated development environment programs have the
ability to activate the venv for you as part of the process of starting and
debugging software, e.g.:

- [VS Code](https://code.visualstudio.com/docs/python/environments)
- [PyCharm](https://www.jetbrains.com/help/pycharm/creating-virtual-environment.html)

### Develop using Pixi

An alternative to `venv` is the package management tool Pixi. If Pixi is not
installed, follow the instructions [here](https://pixi.prefix.dev/latest/#installation).

The very quick version for developing using Pixi is:

```shell
# Clone the repository
git clone https://github.com/sasview/sasdata/
git clone https://github.com/sasview/sasmodels/
git clone https://github.com/sasview/sasview/

# Enter the developer environment
# (This will create (or reuse) a local Pixi environment with all required dependencies.)
cd sasview
pixi shell

# Start the GUI
python -m sas

# Run tests
pixi run test

# Exit the developer environment
exit
```

In more detail, the steps are:

1. Obtain the SasView source using `git`. You will likely need to coordinate
   updates to `sasdata` and `sasmodels`. The
   [`bumps`](https://github.com/bumps/bumps) and
   [`periodictable`](https://github.com/python-periodictable/periodictable)
   packages are far more loosely coupled, but depending on what you are
   doing you may also want them as development packages, in which case they
   need to be added as editable in the section `[tool.pixi.pypi-dependencies]`
   in `pyproject.toml`.
1. Create (or reuse) a local Pixi environment in `.pixi` and enter the shell
   into the developer environment. The first time it will take a while to
   download and unpack all dependencies.
   Note that `sasdata`, `sasmodels` and `sasview` are installed in editable mode,
   meaning that any code changes will be available the next time you run the
   program.
1. Run SasView! As an alternative to typing `python -m sas`, you can simply
   type `sasview`.

Almost all the modules that SasView needs are available as precompiled modules
on PyPI, including numpy, scipy, h5py, pyside6. A handful of Python-only
modules will be built into wheels on your local machine. Installing the
dependencies should be a one-off task.

## Pre-Commit Hooks for Linting

The SasView, SasData and SasModels repositories include [pre-commit hooks](https://pre-commit.com/), which can be set up to enable linting to be run on the code. A linter is a tool that can detect programming errors, bugs, stylistic errors, etc. SasView uses the [Ruff](https://docs.astral.sh/ruff/) package for linting. Ruff is able to warn about a wide range of possible errors, and in some cases apply automatic fixes for them.

When code is submitted to the SasView repository, we make sure to always apply all available automatic fixes for any linting
violations present. The pre-commit hooks can be used to warn of any linting errors when committing to the local branch, or pushing that branch to the repository.

To use the pre-commit hooks provided in SasView, first activate your virtual environment and install the pre-commit package with:

```shell
pip install pre-commit
```

To set up the pre-commit hook for a package, simply navigate to the appropriate directory for the package and type:

```shell
pre-commit install
```

This will configure the pre-commit hook for the relevant package.

> [!IMPORTANT]
> To set up the pre-commit hooks for SasView, SasData, and SasModels this command needs to be run in the directory for each package separately.

## Seeing and testing your changes

Having set up the venv for your work, it's important that you activate the venv and run sasview inside it.
When you're working across several different sets of changes, you might end up with multiple different venvs.

The instructions above used *editable* installs (that is `-e` for pip) which means that any changes to Python code and resources that live inside the Python module next to Python files (like icons) will take effect from when you next start SasView. This will be true for all the projects that you installed as editable installs in setting up your development environment.


### Resources that are created or moved during the build

For files that do not live in git in the same place as the module expects to find them, the magic of editable installs does not work, likewise for files that are generated as part of the build process.

**GUI — automated**: For `.ui` files that are part of the SasView GUI, new Python files are automatically regenerated by sasview if needed so there's nothing manual you need to do.
Running `uic` to make the user interface is fast enough that it can be done on the fly so we can get away with this.

**Documentation and other resources ­— manual steps required**: running sphinx is not fast, and so Python will need some help from you for the documentation and some other files that do not live in git in the same place as they do in the installed Python module.
Specifically *editable* install magic does not apply to:

- files that are listed in `pyproject.toml` in the `force-includes` blocks:

   - `example_data`
   - `src/sas/sasview/media/`

- all sphinx documentation files; the source for the documentation is assembled by `collect_sphinx_sources.py` from files scattered across multiple projects. The documentation is then built by sphinx and the output needs to be installed. In particular, the following need manual handling in the editable installation:

  - `.rst` files
  - auto-generated documentation files from apidoc
  - auto-generated model descriptions and sample output
  - images that are copied into the documentation (often from `media` directories in the case of SasView)

To have changes to any of these file propagate into the build, the module needs to be reinstalled: `python -m pip install -e .`
The process of reinstalling the module rebuilds the documentation and copies it into `site-packages`, so that it can be used. Since all the dependencies are already installed, the build just runs the sphinx tools with the correct options and copies the output.

:warning: changing the file doesn't just mean opening it in your editor; switching the git branch will also change the file behind Python's back and you need to follow the same instructions below to see the changes.

:warning: building sasview will use whatever sasdata and sasmodels packages are installed into the current venv; if you're looking at the wrong venv or haven't *installed* changes to other packages into that venv, they aren't visible.

To be explicit:

- **sasmodels:** you change model files or documentation in `sasmodels`

  - if you just want to see what that looks like to check your syntax etc, then
    1. inside your sasmodels directory: `python -m pip install --no-build-isolation -e .`
    2. look at the documentation in your browser (`build/doc/index.html`)

  - if you want to see what that looks like inside SasView,

    1. inside your sasmodels directory: `python -m pip install --no-build-isolation -e .` ( :warning: this is a new(ish) step and will generated puzzling results if forgotten)
    2. inside your sasview directory: `python -m pip install --no-build-isolation -e .`
    3. start SasView and look at the help

- **sasdata:** you change documentation in `sasdata`

  - same as for sasmodels, above

- **sasview:** you change documentation in `sasview`

   1. inside your sasview directory: `python -m pip install --no-build-isolation -e .`
   2. look at the documentation in your browser (`build/doc/index.html`)
   3. start SasView and look at the help



If you intend to repeat this many many times, you can speed it up:

- `--no-build-isolation` as shown above builds without creating a new temporary venv
- set `SASMODELS_BUILD_CACHE` in your environment so sasmodels will cache the figures from sasmodels, e.g. `export SASMODELS_BUILD_CACHE=~/.cache/sasmodels-figures`. (You need to empty the cache yourself from time to time; see [the documentation inside sasmodels](https://github.com/SasView/sasmodels/blob/master/doc/genmodel.py#L9) for details, suggestions and other caveats.)
- fundamentally, the slow part is always (and always was) running sphinx to render the documentation


### Details of editable installs (for those who want to know)

When `pip` does an *editable* install, it does 3 things
that you will be able to see in your venv's site-packages (e.g. `.venv/lib/python3.X/site-packages/`):

- adds the `sasview-X.Y.Z.dist-info` metadata directory that tells Python that the module is installed, along with details like its version, dependencies, file manifest
- places a `_sasview.pth` file that tells the import machinery where to find the module code and embedded resources; this will point to the `src` directory inside your sasview git clone.
- creates a `sas` directory that contains only the files that don't live in the "right" place in git and therefore do not sit in the filesystem in the correct location for the editable install.

(For a regular installation rather than an editable installation, the `.pth` file would not exist and all the module files would be in that `sas` directory.)

## More information

More information can be found at:

- [http://www.sasview.org/help](http://www.sasview.org/help)
- [http://www.sasview.org/faq](http://www.sasview.org/faq)
- [https://github.com/SasView/sasview/wiki/DevNotes](https://github.com/SasView/sasview/wiki/DevNotes)
