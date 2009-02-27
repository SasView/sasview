"""
     Contains common classes
"""
import wx,re

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
        

def split_list(separator, mylist, n=0):
    """
        @return a list of string without white space of separator
        @param separator: the string to remove
    """
    list=[]
    for item in mylist:
        if re.search( separator,item)!=None:
            if n >0:
                word =re.split(separator,item,int(n))
            else:
                word =re.split( separator,item)
            for new_item in word: 
                if new_item.lstrip().rstrip() !='':
                    list.append(new_item.lstrip().rstrip())
    return list
def split_text(separator, string1, n=0):
    """
        @return a list of string without white space of separator
        @param separator: the string to remove
    """
    list=[]
    if re.search( separator,string1)!=None:
        if n >0:
            word =re.split(separator,string1,int(n))
        else:
            word =re.split(separator,string1)
        for item in word: 
            if item.lstrip().rstrip() !='':
                list.append(item.lstrip().rstrip())
    return list
def look_for_tag( string1,begin, end=None ):
    """
        @note: this method  remove the begin and end tags given by the user
        from the string .
        @param begin: the initial tag
        @param end: the final tag
        @param string: the string to check
        @return: begin_flag==True if begin was found,
         end_flag==if end was found else return false, false
         
    """
    begin_flag= False
    end_flag= False
    if  re.search( begin,string1)!=None:
        begin_flag= True
    if end !=None:
        if  re.search(end,string1)!=None:
            end_flag= True
    return begin_flag, end_flag


