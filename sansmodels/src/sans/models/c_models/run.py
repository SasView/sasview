import sys, os, math
from sans.models.CylinderModel import CylinderModel
from sans.models.DisperseModel import DisperseModel

os.system('gcc -c ../../../libigor/libCylinder.c -o libigor.o -I../c_extensions -I../../../libigor')
os.system('gcc -c ../c_extensions/cylinder.c -o libcyl.o -I../c_extensions -I../../../libigor')
os.system('g++ -mno-cygwin cylinder.cpp parameters.cpp  dispersion_visitor.cpp libigor.o libcyl.o -D__MODELS_STANDALONE__ -I../c_extensions -I../../../libigor')
os.system('a.exe')


cyl = CylinderModel()
cyl.setParam('cyl_phi', 0.0)
cyl.setParam('cyl_theta', 0.0)

disp = DisperseModel(cyl, ['radius'], [5])
disp.setParam('n_pts', 100)
print "" 
print "Cyl (python): ", cyl.run(0.001)
print "Disp(pyhton): ", disp.run(0.001)

