SUBDIRS = 

.PHONY: $(SUBDIRS)

VERSION=1.2

# make executable files under Windows
all: park

park:
	python setup.py install

parkwin:
	rm -rf MANIFEST
	python setup_win.py py2exe

# clean temporary and pyc files
clean: $(SUBDIRS)
	$(RM) *~ *.pyc

# clean temporary and pyc files, and dist/, build/
cleanall: $(SUBDIRS)
	$(RM) *~ *.pyc
	$(RM) -rf dist
	$(RM) -rf build
	$(RM) MANIFEST

# make documents
html:
	$(RM) -rf build/html
	epydoc --html park --name PARK -o build/html -v --config=park.epydoc

pdf:
	$(RM) -rf build/docpdf
	epydoc --pdf  park --name PARK -o build/pdf --config=park.epydoc

# make distributions for source code and windows executable files
distall: 
	$(RM) -rf dist
	$(RM) -rf build 
	
	$(RM) -rf MANIFEST
	./setup_fit.py sdist --formats=gztar,bztar,zip
	
	$(RM) -rf MANIFEST
	./setup_gui.py sdist --formats=gztar,bztar,zip
		
	$(RM) -rf MANIFEST
	python setup.py bdist_wininst
	python setup_win.py py2exe

# make source code distributions for all platforms
distsrc:
	$(RM) -rf dist
	$(RM) -rf build
	
	$(RM) -rf MANIFEST	 	
	./setup_fit.py sdist --formats=gztar,bztar,zip
	
	$(RM) -rf MANIFEST
	./setup_gui.py sdist --formats=gztar,bztar,zip


# script-based PARK
distfit:
	$(RM) -rf MANIFEST	
	./setup_fit.py sdist --formats=gztar,bztar,zip


# GUI-based PARK
distgui:
	$(RM) -rf MANIFEST
	./setup_gui.py sdist --formats=gztar,bztar,zip


# make source code distributions for Unix
distunix:distsrc	


# make distributions for Windows, installer or executable file	
distwin:
	rm -rf dist
	python setup_win.py py2exe
	mv dist park-$(VERSION)
	zip -r park-$(VERSION).exe.zip park-$(VERSION)
	mkdir dist
	mv park-$(VERSION).exe.zip dist
	rm -rf park-$(VERSION)
	./setup.py bdist_wininst


# recursive works for individual subdirectory 
$(SUBDIRS):
	cd $@ && $(MAKE) $(MAKECMDGOALS)

