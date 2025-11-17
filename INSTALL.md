# Quick Intro for Building SasView

Note - at the current time SasView will only run in gui form under Python 3.12 and later.

Whether you're installing SasView to use as a tool for your research or
because you're wanting to work on the code, it is recommended that you
work inside a Python virtual environment of some sort.
A `venv` or a `conda` are both popular choices.

## Installing SasView as a User

Installers for SasView can be found at [https://www.sasview.org/](https://www.sasview.org/),
for various operating systems. You will also find walk through tutorials on how to install and use SasView.

You can also install SasView using standard Python installation tools,
such as `pipx install sasview` to install it into its own standalone
environment (or `pip install sasview` to install it into your current Python environment).

## Making a SasView Development Environment

If you're familiar with working with developing in Python, then the very quick version is:

```shell
# clone the repository
git clone https://github.com/sasview/sasdata/
git clone https://github.com/sasview/sasmodels/
git clone https://github.com/sasview/sasview/

cd sasview

#create the virtual environment
python -m venv .venv
# .venv\Scripts\activate & REM Windows: activate environment
. .venv/bin/activate  # Linux/Mac: activate environment

# install repositories in editable/devloper mode in the venv
python -m pip install -e ../sasdata # use "python -m ..." to ensure the correct python version is used
python -m pip install -e ../sasmodels
python -m pip install -e .[dev,test]

# test if sasview launches
python -m sas
```

Step by step, that is:

1.  Obtain the SasView source using `git`. You will likely need to coordinate
    updates to `sasdata` and `sasmodels`. The
    `bumps` (https://github.com/bumps/bumps) and
    `periodictable` (https://github.com/python-periodictable/periodictable)
    packages are far more loosely coupled, but depending on what you are
    doing you may also want them as development packages.
1.  Create a Python virtual environment in the `venv` directory.
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
# venv\Scripts\activate  & REM Windows: activate environment
. .venv/bin/activate  # Linux/Mac: activate environment
python -m sas
```

(or the [equivalent command](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#create-and-use-virtual-environments) for your shell to activate the venv)

Note that many Python-focused integrated development environment programs have the
ability to activate the venv for you as part of the process of starting and
debugging software, e.g.:

- [VS Code](https://code.visualstudio.com/docs/python/environments)
- [PyCharm](https://www.jetbrains.com/help/pycharm/creating-virtual-environment.html)

More information can be found at:

- [http://www.sasview.org/help](http://www.sasview.org/help)
- [http://www.sasview.org/faq](http://www.sasview.org/faq)
- [https://github.com/SasView/sasview/wiki/DevNotes](https://github.com/SasView/sasview/wiki/DevNotes)
