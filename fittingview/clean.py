"""
    Remove all compiled code.
"""
import os

filedirs = ['src', 'src/sans','src/sans/perspectives', 
            'src/sans/perspectives/fitting']

for d in filedirs:
    files = os.listdir(d)
    for f in files:
        if f.find('.pyc')>0:
            print "Removed", f
            os.remove(os.path.join(d,f))