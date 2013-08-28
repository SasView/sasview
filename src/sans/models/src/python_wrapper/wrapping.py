import sys
import os
import os.path
from WrapperGenerator import WrapperGenerator

def generate_wrappers(header_dir, output_dir='.', c_wrapper_dir='.'):
    nModels=0
    model_list = list()

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
            model_list.append(app.getModelName())
    write_c_models(model_list)
    print "Total number of model  wrappers created is %s" % nModels

def write_c_models(model_list):
    # simultaneously generates 'sansmodels/installed_models.txt'
    # and 'sansmodels/src/c_models/c_models.cpp'
    

    template_file = open(os.path.join("src", "sans", "models","src","c_models","c_models.cpp.template"),"r")
    write_file = open(os.path.join("src", "sans",  "models","src","c_models","c_models.cpp"),"w")
    buf = template_file.read()
    lines = buf.split('\n')
    
    tag1 = "[TAG_1]"
    tag2 = "[TAG_2]"
    
    for line in lines:
        
        if line.count(tag1) > 0:
            write_file.write("\n // adding generated code \n")
            for pyclass in model_list:
                write_file.write("void addC" + pyclass
                                 + "(PyObject *module); \n")
            write_file.write(" // end generated code \n")
                

        elif line.count(tag2) > 0:
            write_file.write("\n // adding generated code \n")

            for pyclass in model_list:
                write_file.write("addC" + pyclass + "(m); \n")

            write_file.write("addDisperser(m); \n")
            write_file.write("\n // end generated code \n")
                
                
        else:
            write_file.write(line + "\n")



if __name__ == '__main__':
    header_dir = os.path.join('..', 'include')
    generate_wrappers(header_dir, output_dir="../sans/models/", c_wrapper_dir='.')




