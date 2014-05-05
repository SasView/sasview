"""
Checking and reinstalling the external packages
"""
import os
import sys

common_required_package_list = {'setuptools':{'version':'0.6c11','import_name':'setuptools','test':'__version__'},
                'pyparsing':{'version':'1.5.5','import_name':'pyparsing','test':'__version__'},
                'html5lib':{'version':'0.95','import_name':'html5lib','test':'__version__'},
                'reportlab':{'version':'2.5','import_name':'reportlab','test':'Version'},
                'lxml':{'version':'2.3','import_name':'lxml.etree','test':'LXML_VERSION'},
                'PIL':{'version':'1.1.7','import_name':'Image','test':'VERSION'},
                'pylint':{'version':None,'import_name':'pylint','test':None},
                'periodictable':{'version':'1.3.0','import_name':'periodictable','test':'__version__'},
                'numpy':{'version':'1.6.1','import_name':'numpy','test':'__version__'},
                'scipy':{'version':'0.10.1','import_name':'scipy','test':'__version__'},
                'wx':{'version':'2.8.12.1','import_name':'wx','test':'__version__'},
                'matplotlib':{'version':'1.1.0','import_name':'matplotlib','test':'__version__'},
                'pisa':{'version':'3.0.28','import_name':'ho.pisa','test':'__version__'}

}
win_required_package_list = {'comtypes':{'version':'0.6.2','import_name':'comtypes','test':'__version__'},
                             'pywin':{'version':'217','import_name':'pywin','test':'__version__'},
                             'py2exe':{'version':'0.6.9','import_name':'py2exe','test':'__version__'}
}
mac_required_package_list = {'py2app':{'version':None,'import_name':'py2app','test':'__version__'}}

deprecated_package_list = {'pyPdf':{'version':'1.13','import_name':'pyPdf','test':'__version__'}}

print "Checking Required Package Versions...."
print
print "Common Packages"
for package_name,test_vals in common_required_package_list.iteritems():
    try:
        i = __import__(test_vals['import_name'],fromlist=[''])
        if test_vals['test'] == None:
            print "%s Installed (Unknown version)" % package_name
        elif package_name == 'lxml':
            verstring = str(getattr(i,'LXML_VERSION'))
            print "%s Version Installed: %s"% (package_name,verstring.replace(', ','.').lstrip('(').rstrip(')'))
        else:
            print "%s Version Installed: %s"% (package_name,getattr(i,test_vals['test']))
    except:
        print '%s NOT INSTALLED'% package_name

if sys.platform == 'win32':
    print
    print "Windows Specific Packages:"
    for package_name,test_vals in win_required_package_list.iteritems():
        try:
            if package_name == "pywin":
                import win32api
                fixed_file_info = win32api.GetFileVersionInfo(win32api.__file__,'\\')
                print "%s Version Installed: %s"% (package_name,fixed_file_info['FileVersionLS'] >> 16)
            else:
                i = __import__(test_vals['import_name'],fromlist=[''])
                print "%s Version Installed: %s"% (package_name,getattr(i,test_vals['test']))
        except:
            print '%s NOT INSTALLED'% package_name

if sys.platform == 'darwin':
    print
    print "MacOS Specific Packages:"
    for package_name,test_vals in mac_required_package_list.iteritems():
        try:
            i = __import__(test_vals['import_name'],fromlist=[''])
            print "%s Version Installed: %s"% (package_name,getattr(i,test_vals['test']))
        except:
            print '%s NOT INSTALLED'% package_name


print
print "Deprecated Packages"
print "You can remove these unless you need them for other reasons!"
for package_name,test_vals in deprecated_package_list.iteritems():
    try:
        i = __import__(test_vals['import_name'],fromlist=[''])
        if package_name == 'pyPdf':
            #pyPdf doesn't have the version number internally
            print 'pyPDF Installed (Version unknown)'
        else:
            print "%s Version Installed: %s"% (package_name,getattr(i,test_vals['test']))
    except:
        print '%s NOT INSTALLED'% package_name
