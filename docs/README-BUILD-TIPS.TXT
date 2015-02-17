Quick Intro for Building Sasview
================================


The build works in the usualy pythonic way:

$ python setup.py build      # will build the package underneath 'build/'
$ python setup.py install    # will install the package



If you want to check the build without installing:

$ python run.py              # will run the code in place (building the C code once, if required)



To check all dependencies are met:

$ python deps.py
$ python check_packages.py 

Both tell you different parts of the story, unfortunately.



Build scripts that are used on http://build.sasview.org/ are in
build_tools. Make sure the build is run first obviously.

$ build_tools/jenkins_linux_build.sh
$ build_tools/jenkins_linux_test.sh
$ build_tools/jenkins_linux_pylint.sh

The scripts can be customized using environment variables, but 
should do a reasonable job as is in a sane setup.



To build just the Sphinx docs:
build_sphinx.py


More information can be found here:

http://www.sasview.org/help.html
http://www.sasview.org/faq.html
http://www.sasview.org/trac/wiki/DevNotes
