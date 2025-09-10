#
#Also see sasview\src\sas\qtgui\Perspectives\Fitting\media\cli.rst
#
"""
**SasView command line interface**

This functionality is under development. Interactive sessions do not yet
work in the Windows console.

**Usage:**

sasview [flags]
    *Run SasView. If no flag is given, or -q or -V are given, this will start
    the GUI.*

sasview [flags] script [args...]
    *Run a python script using the installed SasView libraries [passing
    optional arguments]*

sasview [flags] -m module [args...]
    *Run a SasView/Sasmodels/Bumps module as main [passing optional arguments]*

sasview [flags] -c "python statements" [args...]
    *Execute python statements using the installed SasView libraries*

sasview -V
    *Print sasview version and exit.*

**Flags:**

    -i, --interactive. *Enter an interactive session after command/module/script.*

    -o, --console. *Open a console to show command output. (Windows only)*

    -q, --quiet. *Suppress startup messages on interactive console.*

Note: On Windows any console output is ignored by default. You can either
open a console to show the output with the *-o* flag or redirect output to
a file using something like *sasview ... > output.txt*.
"""
# TODO: Support dropping datafiles onto .exe?
import argparse
import logging
import sys
from pathlib import Path


def parse_cli(argv: list[str]) -> argparse.Namespace:
    """
    Parse the argv arguments from the command line.

    * version: bool - print version
    * command: str - string to exec
    * module: str - module to run as main
    * interactive: bool - run interactive
    * args: list[str] - additional arguments, or script + args
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-V", "--version", action='store_true',
        help="Print sasview version and exit")
    parser.add_argument("-m", "--module", type=str,
        help="Run module with remaining arguments sent to main")
    parser.add_argument("-c", "--command", type=str,
        help="Execute command")
    parser.add_argument("-i", "--interactive", action='store_true',
        help="Start interactive interpreter after running command")
    parser.add_argument("-o", "--console", action='store_true',
        help="Open console to display output (windows only)")
    parser.add_argument("-q", "--quiet", action='store_true',
        help="Don't print banner when entering interactive mode")
    parser.add_argument("-l", "--loglevel", type=str,
        help="Logging level (production or development for now)")
    parser.add_argument("args", nargs="*",
        help="script followed by args")

    # Special case: abort argument processing after -m or -c.
    have_trigger = False
    collect_rest = False
    keep = []
    rest = []
    for arg in argv[1:]:
        # Append argument to the parser argv or collect them as extra args.
        if collect_rest:
            rest.append(arg)
        else:
            keep.append(arg)
        # For an action that needs an argument (e.g., -m module) we need
        # to keep the next argument for the parser, but the remaining arguments
        # get collected as extra args. Trigger and collect will happen in one
        # step if the trigger requires no args or if the arg was provided
        # with the trigger (e.g., -mmodule)
        if have_trigger:
            collect_rest = True
        if arg.startswith('-m') or arg.startswith('--module'):
            have_trigger = True
            collect_rest = arg not in ('-m', '--module')
        elif arg.startswith('-c') or arg.startswith('--command'):
            have_trigger = True
            collect_rest = arg not in ('-c', '--command')

    opts = parser.parse_args(keep)
    if collect_rest:
        opts.args = rest
    return opts

def main(dev_mode: bool|None=None) -> int:
    """
    Run the main program.

    If *dev_mode* is True then rebuild the UI before running. If *dev_mode*
    is not provided, then look into the filesystem to guess whether we are
    running from the source tree or from an installed version.
    """
    # Guess if we are in development mode if not provided on the command line.
    if dev_mode is None:
        # Check that we are in ".../src/sas/cli.py" and ".../pyproject.toml" exists.
        src = Path(__file__).resolve().parent.parent
        dev_mode = src.name == "src" and (src.parent / "pyproject.toml").exists()

    # I/O redirection for the windows console. Need to do this early so that
    # output will be displayed on the console. Presently not working for
    # production (it always opens the console even if it is not needed)
    # so require "sasview -o ..." to open the console. Not an infamous
    # "temporary fix" I hope...
    if "-i" in sys.argv[1:] or "-o" in sys.argv[1:]:
        from sas.system import console
        console.setup_console()

    # Eventually argument processing might affect logger or config, so do it first
    opts = parse_cli(sys.argv)

    # Move config files from .sasview to the platform specific user config directory
    from sas.system.user import copy_old_files_to_new_location
    copy_old_files_to_new_location()

    # Now we can load the config files and setup the sasview environment
    from sas.system import lib, log

    # Setup logger and sasmodels
    log_mode = opts.loglevel if opts.loglevel else "development" if dev_mode else "production"
    log_mode = log_mode.upper()
    if log_mode == "PRODUCTION":
        log.production()
    elif log_mode == "DEVELOPMENT":
        log.development()
    elif log_mode.upper() in {'DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'}:
        log.setup_logging(log_mode)
    else:
        raise ValueError(f"Unknown logging mode \"{log_mode}\"")

    lib.setup_sasmodels()
    lib.setup_qt_env() # Note: does not import any gui libraries

    if opts.version: # -V
        import sas
        print(f"SasView {sas.__version__}")
        # Exit immediately after -V.
        return 0

    context = {'exit': sys.exit}
    if opts.module: # -m module [arg...]
        import runpy
        # TODO: argv[0] should be the path to the module file not the dotted name
        sys.argv = [opts.module, *opts.args]
        context = runpy.run_module(opts.module, run_name="__main__")
    elif opts.command: # -c "command"
        sys.argv = ["-c", *opts.args]
        exec(opts.command, context)
    elif opts.args: # script [arg...]
        import runpy
        sys.argv = opts.args
        context = runpy.run_path(opts.args[0], run_name="__main__")
    elif not opts.interactive: # no arguments so start the GUI
        if dev_mode:
            logging.info("rebuilding UI")
            from sas.qtgui.convertUI import rebuild_new_ui
            rebuild_new_ui()

        from sas.qtgui.MainWindow.MainWindow import run_sasview
        # sys.argv is unchanged
        # Maybe hand cli.quiet to run_sasview?
        run_sasview()
        return 0 # don't drop into the interactive interpreter

    # TODO: Start interactive with ipython rather than normal python
    # For ipython use:
    #     from IPython import start_ipython
    #     sys.argv = ["ipython", *args]
    #     sys.exit(start_ipython())
    if opts.interactive:
        import code
        # The python banner is something like
        #     f"Python {sys.version} on {platform.system().lower()}"
        # where sys.version contains "VERSION (HGTAG, DATE)\n[COMPILER]"
        # We are replacing it with something that includes the sasview version.
        if opts.quiet:
            exitmsg = banner = ""
        else:
            import platform

            import sas
            # Form dotted python version number out of sys.version_info
            major, minor, micro = sys.version_info[:3]
            sasview_ver = f"SasView {sas.__version__}"
            python_ver = f"Python {major}.{minor}.{micro}"
            os_ver = platform.system()
            banner = f"{sasview_ver} for {python_ver} on {os_ver}"
            exitmsg = ""
        code.interact(banner=banner, exitmsg=exitmsg, local=context)

    return 0

if __name__ == "__main__":
    sys.exit(main())
