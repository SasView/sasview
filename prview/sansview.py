
#import gui_manager
from sans.guiframe import gui_manager
class SansView():
    
    def __init__(self):
        """
        
        """
        #from gui_manager import ViewApp
        self.gui = gui_manager.ViewApp(0)
        
        # Set the application manager for the GUI
        self.gui.set_manager(self)
        
        # Start the main loop
        self.gui.MainLoop()  

if __name__ == "__main__": 
    sansview = SansView()