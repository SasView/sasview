"""
SasView command line interface.

sasview -m module [args...]
    Run module as main.
sasview -c "python statements"
    Execute python statements with sasview libraries available.
sasview -i 
    Start ipython interpreter.
sasview script [args...]
    Run script with sasview libraries available
sasview
    Start sasview gui

You can also run it as "python -m sas.cli".
"""
import sys

# TODO: Support dropping datafiles onto .exe?
# TODO: Maybe use the bumps cli with project file as model?

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-m", "--module", type=str,
    help="Run module as main")
parser.add_argument("-c", "--command", type=str,
    help="Execute command")
parser.add_argument("-i", "--interactive", action='store_true', 
    help="Run interactive command line")
parser.add_argument("argv", nargs="*",
    help="script followed by argv")

def exclusive_error():
    print("Use only one of -m module args, -c command, -i, or script.py args.", sys.stderr)
    sys.exit(1)

def run_interactive():
    """Run sasview as an interactive python interpreter"""
    try:
        from IPython import start_ipython
        sys.argv = ["ipython", "--pylab"]
        sys.exit(start_ipython())
    except ImportError:
        import code
        code.interact(local={'exit': sys.exit})

def main(logging="production"):
    from sas.system import log
    from sas.system import lib

    # Eventually argument processing might affect logger or config, so do it first
    args = parser.parse_args()

    # Setup logger and sasmodels
    if logging == "production":
        log.production()
    elif logging == "development":
        log.development()
    else:
        raise ValueError(f"Unknown logging mode \"{logging}\"")
    lib.setup_sasmodels()

    # Parse mutually exclusive command line options
    # mutually exclusive (-m module args, -c command, -i, script args)
    if args.argv and not args.module: # script [arg...]
        import runpy
        if args.command or args.module or args.interactive:
            exclusive_error()
        sys.argv = args.argv
        runpy.run_path(args.argv[0], run_name="__main__")
    elif args.module: # -m module [arg...]
        import runpy
        if args.command or args.interactive:
            exclusive_error()
        sys.argv = [args.module, *args.argv]
        runpy.run_module(args.module, run_name="__main__")
    elif args.command: # -c "command"
        if args.argv or args.module or args.interactive:
            exclusive_error()
        exec(args.command)
    elif args.interactive: # -i
        if args.argv or args.module or args.command:
            exclusive_error()
        run_interactive()
    else:
        from sas.qtgui.MainWindow.MainWindow import run_sasview as run_gui
        run_gui()

if __name__ == "__main__":
    main()
