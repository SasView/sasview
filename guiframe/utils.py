"""
     Contains common classes
"""
import wx

def format_number(value, high=False):
    """
        Return a float in a standardized, human-readable formatted string 
    """
    try: 
        value = float(value)
    except:
        print "returning 0"
        return "0"
    
    if high:
        return "%-6.4g" % value
    else:
        return "%-5.3g" % value
    
class PanelMenu(wx.Menu):
    plots = None
    graph = None
    
    def set_plots(self, plots):
        self.plots = plots
    
    def set_graph(self, graph):
        self.graph = graph