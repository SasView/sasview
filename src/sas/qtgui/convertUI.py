# Convert all .ui files in all subdirectories of the current script

# Usage: python convert.py [-f]
#  Arguments: -f -> Force the UI elements to be rebuilt, even if they exist
import os
import sys


def run(main, name, *args):
    saved_argv = sys.argv
    sys.argv = [name, *args]
    try:
        main()
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
    from PyQt5.pyrcc_main import main
    run(main, "pyrcc", in_file, "-o", out_file)


def pyuic(in_file, out_file):
    """
    Run the qt UI compiler
    """
    from PyQt5.uic.pyuic import main
    run(main, "pyuic", "-o", out_file, in_file)


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


args = sys.argv
force_recreate = '-f' in args

# Files that don't meet the default behavior of generating a python file with the same base name in the same directory
#  - /same/path/to/<filename>.ui -> /same/path/to/<filename>.py using the pyuic() method
oddity_dict = {
    # Format: {'filename': {'f_name': 'new_filename', 'root': '/new/path/to/<f_name>.py', 'method': callable}}
    'main_resources.qrc':
        {
            'f_name': 'main_resources_rc',
            'root': '.\\UI\\',
            'method': pyrrc,
        },
    'images.qrc':
        {
            'f_name': 'images_rc',
            'root': '.\\UI\\',
            'method': pyrrc,
        },
}

# look for .ui and .qrc files and generate .py files in their required location
for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".ui") or file.endswith('.qrc'):
            file_dict = oddity_dict.get(file, {'f_name': file, 'root': root, 'method': pyuic})
            file_in = os.path.join(root, file)
            file_out = os.path.join(file_dict['root'], os.path.splitext(file_dict['f_name'])[0]+'.py')
            if force_recreate or file_in_newer(file_in, file_out):
                print("Generating " + file_out + " ...")
                file_dict['method'](file_in, file_out)
