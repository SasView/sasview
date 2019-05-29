# Convert all .ui files in all subdirectories of the current script
import os
import sys

def pyrrc(in_file, out_file):
    """ Run the pyrcc4 script"""
    execute = 'pyrcc5 %s -o %s' % (in_file, out_file)
    os.system(execute)

def pyuic(in_file, out_file):
    """ Run the pyuic5 script"""
    execute = 'pyuic5 -o %s %s' % (out_file, in_file)
    os.system(execute)

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

# look for .ui files
for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".ui"):
            file_in = os.path.join(root, file)
            file_out = os.path.splitext(file_in)[0]+'.py'
            if file_in_newer(file_in, file_out):
                print("Generating " + file_out + " ...")
                pyuic(file_in, file_out)

# RC file in UI directory
execute_root = os.path.split(sys.modules[__name__].__file__)[0]
ui_root = os.path.join(execute_root, 'UI')
rc_file = 'main_resources.qrc'
out_file = 'main_resources_rc.py'

in_file = os.path.join(ui_root, rc_file)
out_file = os.path.join(ui_root, out_file)

if file_in_newer(in_file, out_file):
    print("Generating " + out_file + " ...")
    pyrrc(in_file, out_file)

# Images
images_root = os.path.join(execute_root, 'images')
out_root = os.path.join(execute_root, 'UI')
rc_file = 'images.qrc'
out_file = 'images_rc.py'

in_file = os.path.join(images_root, rc_file)
out_file = os.path.join(ui_root, out_file)

if file_in_newer(in_file, out_file):
    print("Generating " + out_file + " ...")
    pyrrc(in_file, out_file)

