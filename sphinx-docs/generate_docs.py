import os
cwd = os.getcwd()
        
module_list = ["fittingview", "invariantview", "inversionview",
               "park_integration", "calculatorview", "plottools",
               "pr_inversion", "sanscalculator", "sansdataloader",
               "sansguiframe", "sansinvariant", "sansmodels"]

for m in module_list:
    sphinx_dir = "../%s/docs/sphinx" % m
    os.system("cd %s; python genmods.py; cd %s" % (sphinx_dir, cwd))
os.system("make html")   