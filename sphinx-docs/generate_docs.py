import os
cwd = os.getcwd()
for d in os.listdir('.'):
    sphinx_dir = os.path.join(d, 'docs', 'sphinx')
    if os.path.isdir(sphinx_dir) and sphinx_dir.find("calculator")<0:
        print sphinx_dir
        #os.chdir(sphinx_dir)
        #os.system("cd %s; make stubs; cd %s" % (sphinx_dir, cwd))
        #print "DONE"
        
module_list = ["fittingview", "invariantview", "inversionview",
               "park_integration", "calculatorview", "plottools",
               "pr_inversion", "sanscalculator", "sansdataloader",
               "sansguiframe", "sansinvariant", "sansmodels"]

for m in module_list:
    sphinx_dir = "../%s/docs/sphinx" % m
    os.system("cd %s; python genmods.py; cd %s" % (sphinx_dir, cwd))
os.system("make html")   