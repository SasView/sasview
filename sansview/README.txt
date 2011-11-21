* INSTALLATION
	For Mac and Windows, run the appropriate installer found at https://sourceforge.net/projects/sansviewproject/files/


* LINUX INSTALLATION

	Create a directory where you want to install SansView. For example:
		mkdir ~/my_username/sansview_dir
		
	Make sure that this directory is on the python path:
		export PYTHONPATH=~/my_username/sansview_dir
	
	Download the .egg file and run the following:
	
	easy_install -d=~/my_username/sansview_dir sansview[...].egg
	
	SansView can then be started by calling:
	
	~/my_username/sansview_dir/sansview


* DEPENDENCIES
	
	- wxPython >= 2.8.11
	- numpy >= 1.4.1
	- matplotlib >= 0.99.1.1
	- scipy
	
	The egg installation will attempt to install the following packages. You may want to 
	install them yourself before installing SansView:
	
	- lxml
	- pil 
	- periodictable

