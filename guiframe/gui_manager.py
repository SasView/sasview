"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2008, University of Tennessee
"""
import wx
import wx.aui
import os, sys
try:
    # Try to find a local config
    import imp
    path = os.getcwd()
    if(os.path.isfile("%s/%s.py" % (path, 'config'))) or \
      (os.path.isfile("%s/%s.pyc" % (path, 'config'))):
            fObj, path, descr = imp.find_module('config', [path])
            config = imp.load_module('config', fObj, path, descr)  
    else:
        raise RuntimeError, "Look for default config"   
except:
    # Didn't find local config, load the default 
    import config
from sans.guicomm.events import EVT_STATUS

import warnings
warnings.simplefilter("ignore")


class ViewerFrame(wx.Frame):
    """
        Main application frame
    """
    def __init__(self, parent, id, title):
        """
            Initialize the Frame object
        """
        from local_perspectives.plotting import plotting
        wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition, size=(1000, 1000))
        
        path = os.path.dirname(__file__)
        ico_file = os.path.join(path,'images/ball.ico')
        if os.path.isfile(ico_file):
            self.SetIcon(wx.Icon(ico_file, wx.BITMAP_TYPE_ICO))
        
        ## Application manager
        self.app_manager = None
        
        ## Find plug-ins
        # Modify this so that we can specify the directory to look into
        self.plugins = self._find_plugins()
        self.plugins.append(plotting.Plugin())

        ## List of panels
        self.panels = {}

        ## Next available ID for wx gui events 
        self.next_id = 20000

        ## Default welcome panel
        self.defaultPanel    = DefaultPanel(self, -1, style=wx.RAISED_BORDER)

        # self.build_gui()
       
        # Register the close event so it calls our own method
        wx.EVT_CLOSE(self, self._onClose)
        # Register to status events
        self.Bind(EVT_STATUS, self._on_status_event)
             
    def build_gui(self):
        # Set up the layout
        self._setup_layout()
        
        # Set up the menu
        self._setup_menus()
        
        self.Fit()
             
    def _setup_layout(self):
        """
            Set up the layout
        """
        # Status bar
        self.sb = self.CreateStatusBar()
        self.SetStatusText("")
        
        # Add panel
        self._mgr = wx.aui.AuiManager(self)
        
        # Load panels
        self._load_panels()
        
        self._mgr.Update()

    def add_perspective(self, plugin):
        """
            Add a perspective if it doesn't already
            exist.
        """
        is_loaded = False
        for item in self.plugins:
             if plugin.__class__==item.PLUGIN_ID.__class__:
                 print "Plugin %s already loaded" % plugin.__class__.__name__
                 is_loaded = True
                 
        if not is_loaded:
            self.plugins.append(plugin)
      
    def _find_plugins(self, dir="perspectives"):
        """
            Find available perspective plug-ins
            @param dir: directory in which to look for plug-ins
            @return: list of plug-ins
        """
        import imp
        print "Looking for plug-ins in %s" % dir
        # List of plug-in objects
        
        #path_exe = os.getcwd()
        #path_plugs = os.path.join(path_exe, dir)
        f = open("load.log",'w') 
        f.write(os.getcwd()+'\n\n')
        #f.write(str(os.listdir(dir))+'\n')
        
        
        plugins = []
        # Go through files in panels directory
        try:
            list = os.listdir(dir)
            for item in list:
                print item
                toks = os.path.splitext(os.path.basename(item))
                name = None
                if not toks[0] == '__init__':
                    
                    if toks[1]=='.py' or toks[1]=='':
                        name = toks[0]
                
                    path = [os.path.abspath(dir)]
                    file = None
                    try:
                        if toks[1]=='':
                            f.write("trying to import \n")
                            mod_path = '.'.join([dir, name])
                            f.write("mod_path= %s\n" % mod_path)
                            module = __import__(mod_path, globals(), locals(), [name])
                            f.write(str(module)+'\n')
                        else:
                            (file, path, info) = imp.find_module(name, path)
                            print path
                            module = imp.load_module( name, file, item, info )
                        if hasattr(module, "PLUGIN_ID"):
                            try:
                                plugins.append(module.Plugin())
                                print "Found plug-in: %s" % module.PLUGIN_ID
                            except:
                                config.printEVT("Error accessing PluginPanel in %s\n  %s" % (name, sys.exc_value))
                        
                    except:
                        print sys.exc_value
                        f.write(str(sys.exc_value)+'\n')
                    finally:
                        if not file==None:
                            file.close()
        except:
            # Should raise and catch at a higher level and display error on status bar
            pass   
        f.write(str(plugins)+'\n')
        f.close()
        return plugins
    
        
      
    def _load_panels(self):
        """
            Load all panels in the panels directory
        """
        
        # Look for plug-in panels
        panels = []        
        for item in self.plugins:
            if hasattr(item, "get_panels"):
                ps = item.get_panels(self)
                panels.extend(ps)

        # Show a default panel with some help information
        # It also sets the size of the application windows
        self.panels["default"] = self.defaultPanel
        self._mgr.AddPane(self.defaultPanel, wx.aui.AuiPaneInfo().
                              Name("default").
                              CenterPane().
                              BestSize(wx.Size(900,800)).
                              MinSize(wx.Size(900,800)).
                              Show())

        # Add the panels to the AUI manager
        for panel_class in panels:
            p = panel_class
            id = wx.NewId()
            
            # Check whether we need to put this panel
            # in the center pane
            if hasattr(p, "CENTER_PANE"):
                if p.CENTER_PANE:
                    self.panels[str(id)] = p
                    self._mgr.AddPane(p, wx.aui.AuiPaneInfo().
                                          Name(p.window_name).Caption(p.window_caption).
                                          CenterPane().
                                          BestSize(wx.Size(600,600)).
                                          MinSize(wx.Size(600,600)).
                                          Hide())
                
            else:
                self.panels[str(id)] = p
                self._mgr.AddPane(p, wx.aui.AuiPaneInfo().
                                  Name(p.window_name).Caption(p.window_caption).
                                  #Floatable().
                                  #Float().
                                  Right().
                                  Dock().
                                  TopDockable().
                                  BottomDockable().
                                  LeftDockable().
                                  RightDockable().
                                  MinimizeButton().
                                  Hide().
                                  #Show().
                                  BestSize(wx.Size(400,400)).
                                  MinSize(wx.Size(100,100)))
                
        
    def get_context_menu(self):
        """
            Get the context menu items made available 
            by the different plug-ins. 
            This function is used by the plotting module
        """
        menu_list = []
        for item in self.plugins:
            if hasattr(item, "get_context_menu"):
                menu_list.extend(item.get_context_menu())
            
        return menu_list
        
    def popup_panel(self, p):
        """
            Add a panel object to the AUI manager
            @param p: panel object to add to the AUI manager
            @return: ID of the event associated with the new panel [int]
        """
        
        ID = wx.NewId()
        self.panels[str(ID)] = p
        
        count = 0
        for item in self.panels:
            if self.panels[item].window_name.startswith(p.window_name): 
                count += 1
                
        windowname = p.window_name
        caption = p.window_caption
        if count>0:
            windowname += str(count+1)
            caption += (' '+str(count))
            
        p.window_name = windowname
        p.window_caption = caption
            
        self._mgr.AddPane(p, wx.aui.AuiPaneInfo().
                          Name(windowname).Caption(caption).
                          Floatable().
                          #Float().
                          Right().
                          Dock().
                          TopDockable().
                          BottomDockable().
                          LeftDockable().
                          RightDockable().
                          MinimizeButton().
                          #Hide().
                          #Show().
                          BestSize(wx.Size(400,400)).
                          MinSize(wx.Size(200,200)))
        
        # Register for showing/hiding the panel
        wx.EVT_MENU(self, ID, self._on_view)
        
        self._mgr.Update()
        return ID
        
    def _setup_menus(self):
        """
            Set up the application menus
        """
        # Menu
        menubar = wx.MenuBar()
        
        # File menu
        filemenu = wx.Menu()
        filemenu.Append(101,'&Quit', 'Exit') 
        
        # Add sub menus
        menubar.Append(filemenu,  '&File')
        
        # Plot menu
        # Attach a menu item for each panel in our
        # panel list that also appears in a plug-in.
        # TODO: clean this up. We should just identify
        # plug-in panels and add them all.
        
        # Only add the panel menu if there is more than one panel
        n_panels = 0
        for plug in self.plugins:
            pers = plug.get_perspective()
            if len(pers)>0:
                n_panels += 1
        
        if n_panels>1:
            viewmenu = wx.Menu()
            for plug in self.plugins:
                plugmenu = wx.Menu()
                pers = plug.get_perspective()
                if len(pers)>0:
                    for item in self.panels:
                        if item == 'default':
                            continue
                        panel = self.panels[item]
                        if panel.window_name in pers:
                            plugmenu.Append(int(item), panel.window_caption, "Show %s window" % panel.window_caption)
                            wx.EVT_MENU(self, int(item), self._on_view)
                    
                    viewmenu.AppendMenu(wx.NewId(), plug.sub_menu, plugmenu, plug.sub_menu)
                
            menubar.Append(viewmenu, '&Panel')

        # Perspective
        # Attach a menu item for each defined perspective.
        # Only add the perspective menu if there are more than one perspectves
        n_perspectives = 0
        for plug in self.plugins:
            if len(plug.get_perspective()) > 0:
                n_perspectives += 1
        
        if n_perspectives>1:
            p_menu = wx.Menu()
            for plug in self.plugins:
                if len(plug.get_perspective()) > 0:
                    id = wx.NewId()
                    p_menu.Append(id, plug.sub_menu, "Switch to %s perspective" % plug.sub_menu)
                    wx.EVT_MENU(self, id, plug.on_perspective)
            menubar.Append(p_menu,   '&Perspective')
 
        # Help menu
        helpmenu = wx.Menu()

        # Look for help item in plug-ins 
        for item in self.plugins:
            if hasattr(item, "help"):
                id = wx.NewId()
                helpmenu.Append(id,'&%s help' % item.sub_menu, '')
                wx.EVT_MENU(self, id, item.help)
        
        if config._do_aboutbox:
            id = wx.NewId()
            helpmenu.Append(id,'&About', 'Software information')
            wx.EVT_MENU(self, id, self._onAbout)
        id = wx.NewId()
        helpmenu.Append(id,'&Check for update', 'Check for the latest version of %s' % config.__appname__)
        wx.EVT_MENU(self, id, self._check_update)
        
        
        
        
        # Look for plug-in menus
        # Add available plug-in sub-menus. 
        for item in self.plugins:
            if hasattr(item, "populate_menu"):
                for (self.next_id, menu, name) in item.populate_menu(self.next_id, self):
                    menubar.Append(menu, name)
        

        menubar.Append(helpmenu, '&Help')
         
        self.SetMenuBar(menubar)
        
        # Bind handlers       
        wx.EVT_MENU(self, 101, self.Close)
        
    def _on_status_event(self, evt):
        """
            Display status message
        """
        self.SetStatusText(str(evt.status))

        
    def _on_view(self, evt):
        """
            A panel was selected to be shown. If it's not already
            shown, display it.
            @param evt: menu event
        """
        self.show_panel(evt.GetId())

    def show_panel(self, uid):
        """
            Shows the panel with the given id
            @param uid: unique ID number of the panel to show
        """
        ID = str(uid)
        config.printEVT("show_panel: %s" % ID)
        if ID in self.panels.keys():
            if not self._mgr.GetPane(self.panels[ID].window_name).IsShown():
                self._mgr.GetPane(self.panels[ID].window_name).Show()
                # Hide default panel
                self._mgr.GetPane(self.panels["default"].window_name).Hide()
                
                
            self._mgr.Update()
        

    def _onClose(self, event):
        import sys
        wx.Exit()
        sys.exit()
                   
    def Close(self, event=None):
        """
            Quit the application
        """
        import sys
        wx.Frame.Close(self)
        wx.Exit()
        sys.exit()

  
    def _check_update(self, event=None): 
        """
            Check with the deployment server whether a new version
            of the application is available
        """
        import urllib
        try: 
            h = urllib.urlopen(config.__update_URL__)
            lines = h.readlines()
            line = ''
            if len(lines)>0:
                line = lines[0]
                
                toks = line.lstrip().rstrip().split('.')
                toks_current = config.__version__.split('.')
                update_available = False
                for i in range(len(toks)):
                    if int(toks[i])>int(toks_current[i]):
                        update_available = True
                if update_available:
                    #print "Version %s is available" % line.rstrip().lstrip()
                    self.SetStatusText("Version %s is available! See the Help menu to download it." % line.rstrip().lstrip())
                    if event != None:
                        import webbrowser
                        webbrowser.open(config.__download_page__)
                else:
                    self.SetStatusText("You have the latest version of %s" % config.__appname__)
                    #print "Server version = %s"  % line.rstrip().lstrip()
        except:
            self.SetStatusText("You have the latest version of %s" % config.__appname__)
            
            
    def _onAbout(self, evt):
        """
            Pop up the about dialog
            @param evt: menu event
        """
        if config._do_aboutbox:
            import aboutbox 
            dialog = aboutbox.DialogAbout(None, -1, "")
            dialog.ShowModal()
            
    def set_manager(self, manager):
        """
            Sets the application manager for this frame
            @param manager: frame manager
        """
        self.app_manager = manager
        
    def post_init(self):
        """
            This initialization method is called after the GUI 
            has been created and all plug-ins loaded. It calls
            the post_init() method of each plug-in (if it exists)
            so that final initialization can be done.
        """
        for item in self.plugins:
            if hasattr(item, "post_init"):
                item.post_init()
        
    def set_perspective(self, panels):
        """
            Sets the perspective of the GUI.
            Opens all the panels in the list, and closes
            all the others.
            
            @param panels: list of panels
        """
        print "gui_mng.set_perspective"
        for item in self.panels:
            # Check whether this is a sticky panel
            if hasattr(self.panels[item], "ALWAYS_ON"):
                if self.panels[item].ALWAYS_ON:
                    continue 
            
            if self.panels[item].window_name in panels:
                if not self._mgr.GetPane(self.panels[item].window_name).IsShown():
                    self._mgr.GetPane(self.panels[item].window_name).Show()
            else:
                if self._mgr.GetPane(self.panels[item].window_name).IsShown():
                    self._mgr.GetPane(self.panels[item].window_name).Hide()
                 
        self._mgr.Update()
        
    def choose_file(self):
        """ 
            Functionality that belongs elsewhere
            Should add a hook to specify the preferred file type/extension.
        """
        #TODO: clean this up
        from data_loader import choose_data_file
        return choose_data_file(self)
                  
class DefaultPanel(wx.Panel):
    """
        Defines the API for a panels to work with
        the GUI manager
    """
    ## Internal nickname for the window, used by the AUI manager
    window_name = "default"
    ## Name to appear on the window title bar
    window_caption = "Welcome panel"
    ## Flag to tell the AUI manager to put this panel in the center pane
    CENTER_PANE = True

  
# Toy application to test this Frame
class ViewApp(wx.App):
    def OnInit(self):
        #from gui_manager import ViewerFrame
        self.frame = ViewerFrame(None, -1, config.__appname__)    
        self.frame.Show(True)

        if hasattr(self.frame, 'special'):
            print "Special?", self.frame.special.__class__.__name__
            self.frame.special.SetCurrent()
        self.SetTopWindow(self.frame)
        return True
    
    def set_manager(self, manager):
        """
            Sets a reference to the application manager
            of the GUI manager (Frame) 
        """
        self.frame.set_manager(manager)
        
    def build_gui(self):
        """
            Build the GUI
        """
        self.frame.build_gui()
        self.frame.post_init()
        
    def add_perspective(self, perspective):
        """
            Manually add a perspective to the application GUI
        """
        self.frame.add_perspective(perspective)
        

if __name__ == "__main__": 
    app = ViewApp(0)
    app.MainLoop()              