import sys
import os
import os.path
from WrapperGenerator import WrapperGenerator


root= os.path.dirname(os.getcwd())

dir = os.path.join(root, "c_extensions")
#print "dir", dir
list= os.listdir(dir)
nModels=0
for item in list:
    toks = os.path.splitext(os.path.basename(item))
    if toks[1]=='.h':
        nModels += 1
        name = toks[0]
        app = WrapperGenerator(os.path.join('..','c_extensions',name+".h"))
        app.read()
        app.write_c_wrapper()
        app.write_python_wrapper()
        print app
print "Number total of models is %s"%nModels