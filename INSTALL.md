# Quick Intro for Building SasView

Note - at the current time SasView will only run in gui form under Python 3.11
and later.

Whether you're installing SasView to use as a tool for your research or
because you're wanting to work on the code, it is recommended that you
work inside a Python virtual environment of some sort.
A `venv` or a `conda` are both popular choices.

## Installing SasView as a User

Installers for SasView can be found at [https://www.sasview.org/](https://www.sasview.org/), for various operating systems. You will also find
walk through tutorials on how to install and use SasView.

You can also install SasView using standard Python installation tools,
such as `pipx install sasview` to install it into its own standalone
environment (or `pip install sasview` to install it into your current Python
environment).


## Making a SasView Development Environment

If you're familiar with working with developing in Python, then the
very quick version is:

```console
$ git clone https://github.com/sasview/sasview/
$ cd sasview
$ python -m venv venv
$ . venv/bin/activate
$ pip install -r build_tools/requirements.txt -r build_tools/requirements-dev.txt
$ hatchling build --hooks-only
$ python run.py
```

Step by step, that is:

 1. Obtain the SasView source using `git`
 1. Create a Python virtual environment in the `venv` directory
 1. Activate the `venv` so that Python and its modules from the venv are used
 1. Install the necessary modules for building and running SasView. It will take a while to download and unpack all the dependencies.
 1. Build the GUI and the documentation using the `hatchling` builder.
 1. Run SasView!

Almost all the modules that SasView needs are available as precompiled modules
on PyPI, including numpy, scipy, h5py, pyside6. A handful of Python-only
modules will get built into wheels on your local machine. Installing the
dependencies should be a one-off event. If you're wanting to work on
SasView again at a later date, you can:

```
$ . venv/bin/activate
$ python run.py
```

If you've altered the user interface or want the documentation to be rebuilt,
then the `hatchling` step can be repeated.


More information can be found at:

 - http://www.sasview.org/help
 - http://www.sasview.org/faq
 - https://github.com/SasView/sasview/wiki/DevNotes
