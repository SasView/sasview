= Conda Recipes =

Here we store the recipes for building conda packages of the dependencies of SasView.  These are dependencies that unforunately do not come pre-bundled with Anaconda.

== Creating a Recipe ==

An easy way to get started with a recipe is to use the skeleton command that comes with conda, which looks for all the information it needs on PyPi (of course, this will only work if the module exists on PyPi...):

{{{
conda skeleton pypi package_name
}}}

This automatically chooses the most recent version up on PyPi.  You may specify an older version as follows:

{{{
conda skeleton pypi package_name --version 1.0.9
}}}

If you run `conda skeleton` from this directory, then the recipes will go into the right place. 

If you're lucky this is all you will need to ever do to create a new recipe, but you may need to go in and tinker with the meta.yaml file from time to time.

'''Issues'''

* Sometimes downloading the package from PyPi is problematic.  You may see something like the following:

  {{{
  Error: Could not open 'C:\\TempAnaconda\\conda-bld\\src_cache\\showfiles.php?group_id=15583.part' for writing ([Errno 22] invalid mode ('wb') or filename: 'C:\\TempAnaconda\\conda-bld\\src_cache\\showfiles.php?group_id=15583.part').
  }}}

  If so, the {{{source:}}} values in meta.yaml are pointing to external urls that are not direct links to the downloads (in the case above, a .php link).  Change  {{{fn:}}} and {{{url:}}} from {{{http://sourceforge.net/project/showfiles.php?group_id=15583}}} or similar to an actual link to a .zip of .tar.gz.  Remember to add a correct {{{mdf:}}} property so that future users have their downloads checked.

* I once tried to use recipes generated with older versions of conda and ran into problems.  Your options here are either to hack away at the recipe until it works, or just re-generate the recipe with skeleton.

== Building a Conda Package and Uploading to Binstar ==

{{{
conda build bumps\
}}}

{{{
TEST END: bumps-0.7.5.4-py27_0
# If you want to upload this package to binstar.org later, type:
#
# $ binstar upload C:\TempAnaconda\conda-bld\win-32\bumps-0.7.5.4-py27_0.tar.bz2
#
# To have conda build upload to binstar automatically, use
# $ conda config --set binstar_upload yes
}}}
