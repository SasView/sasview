# Convert all .ui files in all subdirectories of the current script
import os

def pyrrc(in_file, out_file):
    """ Run the pyrcc4 script"""
    execute = 'pyrcc5 %s -o %s' % (in_file, out_file)
    os.system(execute)

def pyuic(in_file, out_file):
    """ Run the pyuic5 script"""
    execute = 'pyuic5 -o %s %s' % (out_file, in_file)
    os.system(execute)

# look for .ui files
for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".ui"):
            file_in = os.path.join(root, file)
            file_out = os.path.splitext(file_in)[0]+'.py'
            pyuic(file_in, file_out)

# RC file in UI directory
ui_root = 'UI'
rc_file = 'main_resources.qrc'
out_file = 'main_resources_rc.py'
pyrrc(os.path.join(ui_root, rc_file), os.path.join(ui_root, out_file))

# Images
images_root = 'images'
rc_file = 'images.qrc'
out_file = 'images_rc.py'
pyrrc(os.path.join(images_root, rc_file), os.path.join(ui_root, out_file))
