import sys
import os
import os.path
from WrapperGenerator import WrapperGenerator

def generate_wrappers(header_dir, output_dir='.', c_wrapper_dir='.'):
    nModels=0
    for item in os.listdir(header_dir):
        toks = os.path.splitext(os.path.basename(item))
        if toks[1]=='.h':
            nModels += 1
            name = toks[0]
            app = WrapperGenerator(os.path.join(header_dir, name+".h"), 
                                   output_dir=output_dir,
                                   c_wrapper_dir=c_wrapper_dir)
            app.read()
            app.write_c_wrapper()
            app.write_python_wrapper()
            #print app
    print "Total number of model  wrappers created is %s" % nModels

if __name__ == '__main__':
    header_dir = os.path.join('..', 'include')
    generate_wrappers(header_dir, output_dir="../sans/models/", c_wrapper_dir='.')


