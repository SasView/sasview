"""
    Dummy application.
    Allows the user to set an external data manager
"""
import gui_manager

class SansView():
    
    def __init__(self):
        """
            Initialization
        """
        from gui_manager import ViewApp
        self.gui = ViewApp(0)
        
        # Set the application manager for the GUI
        self.gui.set_manager(self)
        
        # Start the main loop
        self.gui.MainLoop()  

if __name__ == "__main__": 
    sansview = SansView()