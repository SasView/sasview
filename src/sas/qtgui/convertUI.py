# Convert all .ui files in all subdirectories of the current script

# Usage: python convert.py [-f]
#  Arguments: -f -> Force the UI elements to be rebuilt, even if they exist
import os
import subprocess
import sys


def run_compiler(compiler_main, name, *args):
    """ Wrapper to run a compiler, either pyrrc or pyuic"""
    saved_argv = sys.argv
    sys.argv = [name, *args]
    try:
        compiler_main()
    except SystemExit as exc:
        if exc.code != 0:
            raise RuntimeError(f"\"{name} {' '.join(args)}\" exited with {exc.code}")
        return exc.code
    finally:
        sys.argv = saved_argv
        pass
    return 0

def pyrrc(in_file, out_file):
    """
    Run the qt resource compiler
    """
    run_line = ["pyside6-rcc", in_file, "-o" ,out_file]
    subprocess.run(run_line, check=True)


def pyuic(in_file, out_file):
    """
    Run the qt UI compiler
    """
    in_file2 = os.path.abspath(in_file)
    out_file2 = os.path.abspath(out_file)
    run_line = ["pyside6-uic", in_file2, "-o", out_file2]
    subprocess.run(run_line, check=True)

def file_in_newer(file_in, file_out):
    """
    Check whether file_in is newer than file_out, if file_out exists.

    Returns True if file_in is newer, or if file_out doesn't exist; False
    otherwise.
    """
    try:
        out_stat = os.stat(file_out)
    except OSError:
        # file_out does not exist
        return True

    in_stat = os.stat(file_in)

    # simple comparison of modification time
    return in_stat.st_mtime >= out_stat.st_mtime


def rebuild_new_ui(force=False):
    # look for .ui files
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".ui"):
                file_in = os.path.join(root, file)
                file_out = os.path.splitext(file_in)[0] + '.py'
                if force or file_in_newer(file_in, file_out):
                    print("Generating " + file_out + " ...")
                    pyuic(file_in, file_out)

    # RC file in UI directory
    execute_root = os.path.split(sys.modules[__name__].__file__)[0]
    ui_root = os.path.join(execute_root, 'UI')
    rc_file = 'main_resources.qrc'
    out_file = 'main_resources_rc.py'

    in_file = os.path.join(ui_root, rc_file)
    out_file = os.path.join(ui_root, out_file)

    if force or file_in_newer(in_file, out_file):
        print("Generating " + out_file + " ...")
        pyrrc(in_file, out_file)

    # Images
    images_root = os.path.join(execute_root, 'images')
    out_root = os.path.join(execute_root, 'UI')
    rc_file = 'images.qrc'
    out_file = 'images_rc.py'


    in_file = os.path.join(images_root, rc_file)
    out_file = os.path.join(ui_root, out_file)

    if force or file_in_newer(in_file, out_file):
        print("Generating " + out_file + " ...")
        pyrrc(in_file, out_file)


    # Icons for Particle Editor
    images_root = os.path.join(execute_root, 'Perspectives/ParticleEditor/UI/icons')
    out_root = os.path.join(execute_root, 'Perspectives/ParticleEditor/UI')
    rc_file = 'icons.qrc'
    out_file = 'icons_rc.py'

    in_file = os.path.join(images_root, rc_file)
    out_file = os.path.join(out_root, out_file)

    if force or file_in_newer(in_file, out_file):
        print("Generating " + out_file + " ...")
        pyrrc(in_file, out_file)


def main():
    """ Entry point for running as a script """

    args = sys.argv
    force_recreate = '-f' in args

    rebuild_new_ui(force_recreate)


if __name__ == "__main__":
    main()
