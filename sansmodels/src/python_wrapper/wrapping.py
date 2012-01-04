import sys
import os
import os.path
from WrapperGenerator import WrapperGenerator


header_dir = os.path.join('..', 'c_extensions')

nModels=0
for item in os.listdir(header_dir):
    toks = os.path.splitext(os.path.basename(item))
    if toks[1]=='.h':
        nModels += 1
        name = toks[0]
        app = WrapperGenerator(os.path.join(header_dir, name+".h"))
        app.read()
        app.write_c_wrapper()
        app.write_python_wrapper()
        print app
print "Number total of models is %s" % nModels