"""
Generate ReST docs with figures for each model.

usage: python genmodels.py path/to/model1.py ...

Output is placed in the directory model, with *model1.py* producing
*model/model1.rst* and *model/img/model1.png*.

Set the environment variable SASMODELS_BUILD_CACHE to the path for the
build cache. That way the figure will only be regenerated if the kernel
code has changed.  This is useful on a build server where the environment
is created from scratch each time.  Be sure to clear the cache from time
to time so it doesn't get too large.  Also, the cache will need to be
cleared if the image generation is updated, either because matplotib
is upgraded or because this file changes.  To accomodate both these
conditions set the path as the following in your build script::

    SASMODELS_BUILD_CACHE=/tmp/sasbuild_$(shasum genmodel.py | cut -f 1 -d" ")

Putting the cache in /tmp allows temp-reaper to clean it up automatically.
Putting the sha1 hash of this file in the cache directory name means that
a new cache will be created whenever the text of this file has changed,
even if it is downloaded from a different branch of the repo.

The release build should not use any caching.

This program uses multiprocessing to build the jobs in parallel.  Use
the following::

    SASMODELS_BUILD_CPUS=0  # one per processor
    SASMODELS_BUILD_CPUS=1  # don't use multiprocessing
    SASMODELS_BUILD_CPUS=n  # use n processes

Note that sasmodels with OpenCL is very good at using all the processors
when generating the model plot, so you should only use a small amount
of parallelism (maybe 2-4 processes), allowing matplotlib to run in
parallel.  More parallelism won't help, and may overwhelm the GPU if you
have one.
"""
from __future__ import print_function

import sys
import os
from os.path import basename, dirname, realpath, join as joinpath, exists
import math
import re
import shutil
import argparse
import subprocess

# CRUFT: python 2.7 backport of makedirs(path, exist_ok=False)
if sys.version_info[0] >= 3:
    from os import makedirs
else:
    def makedirs(path, exist_ok=False):
        try:
            os.makedirs(path)
        except Exception:
            if not exist_ok or not exists(path):
                raise

import numpy as np

# TODO: Remove this line when genmodel is moved to the sasmodels directory.
sys.path.insert(0, realpath(joinpath(dirname(__file__), '..')))
from sasmodels import generate, core
from sasmodels.direct_model import DirectModel, call_profile
from sasmodels.data import empty_data1D, empty_data2D

try:
    from typing import Dict, Any
    #from matplotlib.axes import Axes
    from sasmodels.kernel import KernelModel
    from sasmodels.modelinfo import ModelInfo
except ImportError:
    pass

# Destination directory for model docs
#ROOT = dirname(dirname(realpath(__file__)))
#TARGET_DIR = joinpath(ROOT, "doc", "model")
TARGET_DIR = "../source-temp/user/models" # relative to current path

def plot_1d(model, opts, ax):
    # type: (KernelModel, Dict[str, Any], Axes) -> None
    """
    Create a 1-D image.
    """
    q_min, q_max, nq = opts['q_min'], opts['q_max'], opts['nq']
    q_min = math.log10(q_min)
    q_max = math.log10(q_max)
    q = np.logspace(q_min, q_max, nq)
    data = empty_data1D(q)
    calculator = DirectModel(data, model)
    Iq1D = calculator()

    ax.plot(q, Iq1D, color='blue', lw=2, label=model.info.name)
    ax.set_xlabel(r'$Q \/(\AA^{-1})$')
    ax.set_ylabel(r'$I(Q) \/(\mathrm{cm}^{-1})$')
    ax.set_xscale(opts['xscale'])
    ax.set_yscale(opts['yscale'])
    #ax.legend(loc='best')

def plot_2d(model, opts, ax):
    # type: (KernelModel, Dict[str, Any], Axes) -> None
    """
    Create a 2-D image.
    """
    qx_max, nq2d = opts['qx_max'], opts['nq2d']
    q = np.linspace(-qx_max, qx_max, nq2d) # type: np.ndarray
    data2d = empty_data2D(q, resolution=0.0)
    calculator = DirectModel(data2d, model)
    Iq2D = calculator() #background=0)
    Iq2D = Iq2D.reshape(nq2d, nq2d)
    if opts['zscale'] == 'log':
        Iq2D = np.log(np.clip(Iq2D, opts['vmin'], np.inf))
    ax.imshow(Iq2D, interpolation='nearest', aspect=1, origin='lower',
              extent=[-qx_max, qx_max, -qx_max, qx_max], cmap=opts['colormap'])
    ax.set_xlabel(r'$Q_x \/(\AA^{-1})$')
    ax.set_ylabel(r'$Q_y \/(\AA^{-1})$')

def plot_profile_inset(model_info, ax):
    # type: (ModelInfo, Axes) -> None
    """
    Plot 1D radial profile as inset plot.
    """
    import matplotlib.pyplot as plt
    p = ax.get_position()
    width, height = 0.4*(p.x1-p.x0), 0.4*(p.y1-p.y0)
    left, bottom = p.x1-width, p.y1-height
    inset = plt.gcf().add_axes([left, bottom, width, height])
    x, y, labels = call_profile(model_info)
    inset.plot(x, y, '-')
    inset.locator_params(nbins=4)
    #inset.set_xlabel(labels[0])
    #inset.set_ylabel(labels[1])
    inset.text(0.99, 0.99, "profile",
               horizontalalignment="right",
               verticalalignment="top",
               transform=inset.transAxes)

def figfile(model_info):
    # type: (ModelInfo) -> str
    return model_info.id + '_autogenfig.png'

def make_figure(model_info, opts):
    # type: (ModelInfo, Dict[str, Any]) -> None
    """
    Generate the figure file to include in the docs.
    """
    import matplotlib.pyplot as plt

    print("Build model")
    model = core.build_model(model_info)

    print("Set up figure")
    fig_height = 3.0 # in
    fig_left = 0.6 # in
    fig_right = 0.5 # in
    fig_top = 0.6*0.25 # in
    fig_bottom = 0.6*0.75
    if model_info.parameters.has_2d:
        plot_height = fig_height - (fig_top+fig_bottom)
        plot_width = plot_height
        fig_width = 2*(plot_width + fig_left + fig_right)
        aspect = (fig_width, fig_height)
        ratio = aspect[0]/aspect[1]
        ax_left = fig_left/fig_width
        ax_bottom = fig_bottom/fig_height
        ax_height = plot_height/fig_height
        ax_width = ax_height/ratio # square axes
        fig = plt.figure(figsize=aspect)
        ax2d = fig.add_axes([0.5+ax_left, ax_bottom, ax_width, ax_height])
        print("2D plot")
        plot_2d(model, opts, ax2d)
        ax1d = fig.add_axes([ax_left, ax_bottom, ax_width, ax_height])
        print("1D plot")
        plot_1d(model, opts, ax1d)
        #ax.set_aspect('square')
    else:
        plot_height = fig_height - (fig_top+fig_bottom)
        plot_width = (1+np.sqrt(5))/2*fig_height
        fig_width = plot_width + fig_left + fig_right
        ax_left = fig_left/fig_width
        ax_bottom = fig_bottom/fig_height
        ax_width = plot_width/fig_width
        ax_height = plot_height/fig_height
        aspect = (fig_width, fig_height)
        fig = plt.figure(figsize=aspect)
        ax1d = fig.add_axes([ax_left, ax_bottom, ax_width, ax_height])
        print("1D plot")
        plot_1d(model, opts, ax1d)

    if model_info.profile:
        print("Profile inset")
        plot_profile_inset(model_info, ax1d)

    print("Save")
    # Save image in model/img
    makedirs(joinpath(TARGET_DIR, 'img'), exist_ok=True)
    path = joinpath(TARGET_DIR, 'img', figfile(model_info))
    plt.savefig(path, bbox_inches='tight')
    plt.close(fig)
    #print("figure saved in",path)

def newer(src, dst):
    return not exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst)

def copy_if_newer(src, dst):
    # type: (str) -> str
    """
    Copy from *src* to *dst* if *src* is newer or *dst* doesn't exist.
    """
    if newer(src, dst):
        makedirs(dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)

def link_sources(model_info):
    # type: (ModelInfo) -> str
    """
    Add link to model sources from the doc tree.
    """
    # List source files in order of dependency.
    sources = generate.model_sources(model_info) if model_info.source else []
    sources.append(model_info.basefile)

    # Copy files to src dir under models directory.  Need to do this
    # because sphinx can't link to an absolute path.
    dst = joinpath(TARGET_DIR, "src")
    for path in sources:
        copy_if_newer(path, joinpath(dst, basename(path)))

    # Link to local copy of the files in reverse order of dependency
    targets = [basename(path) for path in sources]
    downloads = [":download:`%s <src/%s>`"%(filename, filename)
                 for filename in reversed(targets)]

    # Could do syntax highlighting on the model files by creating a rst file
    # beside each source file named containing source file with
    #
    #    src/path.rst:
    #
    #    .. {{ path.replace('/','_') }}:
    #
    #    .. literalinclude:: {{ src/path }}
    #        :language: {{ "python" if path.endswith('.py') else "c" }}
    #        :linenos:
    #
    # and link to it using
    #
    #     colors = [":ref:`%s`"%(path.replace('/','_')) for path in sources]
    #
    # Probably need to dump all the rst files into an index.rst to build them.

    # Link to github repo (either the tagged sasmodels version or master)
    #url = "https://github.com/SasView/sasmodels/blob/v%s"%sasmodels.__version__
    #url = "https://github.com/SasView/sasmodels/blob/master"%sasmodels.__version__
    #links = ["`%s <%s/sasmodels/models/%s>`_"%(path, url, path) for path in sources]

    sep = "\n$\\ \\star\\ $ "  # bullet
    body = "\n**Source**\n"
    #body += "\n" + sep.join(links) + "\n\n"
    body += "\n" + sep.join(downloads) + "\n\n"
    return body

def gen_docs(model_info, outfile):
    # type: (ModelInfo, str) -> None
    """
    Generate the doc string with the figure inserted before the references.
    """
    # Load the doc string from the module definition file and store it in rst
    docstr = generate.make_doc(model_info)

    # Auto caption for figure
    captionstr = '\n'
    captionstr += '.. figure:: img/' + figfile(model_info) + '\n'
    captionstr += '\n'
    if model_info.parameters.has_2d:
        captionstr += '    1D and 2D plots corresponding to the default parameters of the model.\n'
    else:
        captionstr += '    1D plot corresponding to the default parameters of the model.\n'
    captionstr += '\n'

    # Add figure reference and caption to documentation (at end, before References)
    pattern = r'\*\*REFERENCE'
    match = re.search(pattern, docstr.upper())

    sources = link_sources(model_info)

    insertion = captionstr + sources

    if match:
        docstr1 = docstr[:match.start()]
        docstr2 = docstr[match.start():]
        docstr = docstr1 + insertion + docstr2
    else:
        print('------------------------------------------------------------------')
        print('References NOT FOUND for model: ', model_info.id)
        print('------------------------------------------------------------------')
        docstr += insertion

    with open(outfile, 'w', encoding='utf-8') as fid:
        fid.write(docstr)

def make_figure_cached(model_info, opts):
    """
    Cache sasmodels figures between independent builds.

    To enable caching, set *SASMODELS_BUILD_CACHE* in the environment.
    A (mostly) unique key will be created based on model source and opts.  If
    the png file matching that key exists in the cache it will be copied into
    the documentation tree, otherwise a new png file will be created and copied
    into the cache.

    Be sure to clear the cache from time to time.  Even though the model
    source
    """
    import hashlib

    # check if we are caching
    cache_dir = os.environ.get('SASMODELS_BUILD_CACHE', None)
    if cache_dir is None:
        print("Nothing cashed, creating...")
        make_figure(model_info, opts)
        print("Made a figure")
        return

    # TODO: changing default parameters won't trigger a rebuild.
    # build cache identifier
    if callable(model_info.Iq):
        with open(model_info.filename) as fid:
            source = fid.read()
    else:
        source = generate.make_source(model_info)["dll"]
    pars = str(sorted(model_info.parameters.defaults.items()))
    code = source + pars + str(sorted(opts.items()))
    hash_id = hashlib.sha1(code.encode('utf-8')).hexdigest()

    # copy from cache or generate and copy to cache
    png_name = figfile(model_info)
    target_fig = joinpath(TARGET_DIR, 'img', png_name)
    cache_fig = joinpath(cache_dir, ".".join((png_name, hash_id, "png")))
    if exists(cache_fig):
        copy_file(cache_fig, target_fig)
    else:
        #print(f"==>regenerating png {model_info.id}")
        make_figure(model_info, opts)
        copy_file(target_fig, cache_fig)

def copy_file(src, dst):
    # type: (str) -> str
    """
    Copy from *src* to *dst*, making the destination directory if needed.
    """
    if not exists(dst):
        path = dirname(dst)
        makedirs(path, exist_ok=True)
        shutil.copy2(src, dst)
    elif os.path.getmtime(src) > os.path.getmtime(dst):
        shutil.copy2(src, dst)

def process_model(py_file, force=False):
    # type: (str) -> None
    """
    Generate doc file and image file for the given model definition file.

    Does nothing if the corresponding rst file is newer than *py_file*.
    Also checks the timestamp on the *genmodel.py* program (*__file__*),
    since we want to rerun the generator on all files if we change this
    code.

    If *force* then generate the rst file regardless of time stamps.
    """
    rst_file = joinpath(TARGET_DIR, basename(py_file).replace('.py', '.rst'))
    if not (force or newer(py_file, rst_file) or newer(__file__, rst_file)):
        #print("skipping", rst_file)
        return rst_file

    # Load the model file
    model_info = core.load_model_info(py_file)
    if model_info.basefile is None:
        model_info.basefile = py_file

    # Plotting ranges and options
    PLOT_OPTS = {
        'xscale'    : 'log',
        'yscale'    : 'log' if not model_info.structure_factor else 'linear',
        'zscale'    : 'log' if not model_info.structure_factor else 'linear',
        'q_min'     : 0.001,
        'q_max'     : 1.0,
        'nq'        : 1000,
        'nq2d'      : 1000,
        'vmin'      : 1e-3,  # floor for the 2D data results
        'qx_max'    : 0.5,
        #'colormap'  : 'gist_ncar',
        'colormap'  : 'nipy_spectral',
        #'colormap'  : 'jet',
    }

    # Generate the RST file and the figure.  Order doesn't matter.
    print("generating rst", rst_file)
    print("1: docs")
    gen_docs(model_info, rst_file)
    print("2: figure", end='')
    if force:
        print()
        make_figure(model_info, PLOT_OPTS)
    else:
        print(" (cached)")
        make_figure_cached(model_info, PLOT_OPTS)
    print("Done process_model")

    return rst_file

def run_sphinx(rst_files, output):
    """
    Use sphinx to build *rst_files*, storing the html in *output*.
    """

    print("Building index...")

    conf_dir = dirname(realpath(__file__))
    with open(joinpath(TARGET_DIR, 'index.rst'), 'w') as fid:
        fid.write(".. toctree::\n\n")
        for path in rst_files:
            fid.write("    %s\n"%basename(path))

    print("Running sphinx command...")

    command = [
        sys.executable,
        "-m", "sphinx",
        "-c", conf_dir,
        TARGET_DIR,
        output,
    ]

    process = subprocess.Popen(command, shell=False, stdout=subprocess.PIPE)

    # Make sure we can see process output in real time
    while True:

        output = process.stdout.readline()

        if process.poll() is not None:
            break

        if output:
            print(output.strip())

def main():
    """
    Process files listed on the command line via :func:`process_model`.
    """
    import matplotlib
    matplotlib.use('Agg')

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cpus", type=int, default=-1, metavar="n",
        help="number of cpus to use in build")
    parser.add_argument("-f", "--force", action="store_true",
        help="force rebuild (serial only)")
    parser.add_argument("-r", "--rst", default="../source-temp/user/models", metavar="path",
        help="path for the rst files")
    parser.add_argument("-b", "--build", default="html", metavar="path",
        help="path for the html files (if sphinx build)")
    parser.add_argument("-s", "--sphinx", action="store_true",
        help="build html docs for the model files")
    parser.add_argument("files", nargs="+",
        help="model files ")
    args = parser.parse_args()

    global TARGET_DIR
    TARGET_DIR = os.path.expanduser(args.rst)
    if not os.path.exists(TARGET_DIR) and not args.sphinx:
        print("build directory %r does not exist"%TARGET_DIR)
        sys.exit(1)
    makedirs(TARGET_DIR, exist_ok=True)

    print("** 'Normal' processing **")
    rst_files = [process_model(py_file, args.force)
                     for py_file in args.files]
    print("normal .rst file processing complete")

    if args.sphinx:
        print("running sphinx")
        run_sphinx(rst_files, args.build)


if __name__ == "__main__":
    main()