import os
__revision__ = "0"
__version__ = "0.0.0"
    
def get_svn_revision(path=None):
    rev = None
    if path is None:
        path = os.path.dirname(__file__)
    entries_path = '%s/.svn/entries' % path

    if os.path.exists(entries_path):
        entries = open(entries_path, 'r').read()
        # Versions >= 7 of the entries file are flat text.  The first line is
        # the version number. The next set of digits after 'dir' is the revision.
        if re.match('(\d+)', entries):
            rev_match = re.search('\d+\s+dir\s+(\d+)', entries)
            if rev_match:
                rev = rev_match.groups()[0]
        # Older XML versions of the file specify revision as an attribute of
        # the first entries node.
        else:
            from xml.dom import minidom
            dom = minidom.parse(entries_path)
            rev = dom.getElementsByTagName('entry')[0].getAttribute('revision')

    if rev:
        return u'%s' % rev
    return None

# Get the version number from the sansview module
# Check to see if we are dealing with a release
try:
    import sans.sansview
    __version__ = sans.sansview.__version__
    __revision__ = sans.sansview.__build__
except:
    print "Could not load sansview module"

# Get actual revision number if possible
try:
    rev = get_svn_revision()
    if rev is not None:
        __revision__ = rev
except:
    print "Could not extract revision number"


print "SasView v ", __version__, __revision__