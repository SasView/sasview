"""
Contains common classes and functions
"""
import wx
import re

def parse_name(name, expression):
    """
    remove "_" in front of a name
    """
    if re.match(expression, name) is not None:
        word = re.split(expression, name, 1)
        for item in word:           
            if item.lstrip().rstrip() != '':
                return item
    else:
        return name
def format_number(value, high=False):
    """
    Return a float in a standardized, human-readable formatted string 
    """
    try: 
        value = float(value)
    except:
        output = "NaN"
        return output.lstrip().rstrip()
    if high:
        output = "%-7.5g" % value
    else:
        output = "%-5.3g" % value
    return output.lstrip().rstrip()

def check_float(item):
    """
    :param item: txtcrtl containing a value
    """
    flag = True
    try:
        mini = float(item.GetValue())
        item.SetBackgroundColour(wx.WHITE)
        item.Refresh()
    except:
        flag = False
        item.SetBackgroundColour("pink")
        item.Refresh()
    return flag

    
class PanelMenu(wx.Menu):
    """
    """
    plots = None
    graph = None
    
    def set_plots(self, plots):
        """
        """
        self.plots = plots
    
    def set_graph(self, graph):
        """
        """
        self.graph = graph
        

def split_list(separator, mylist, n=0):
    """
    returns a list of string without white space of separator
    
    :param separator: the string to remove
    
    """
    list = []
    for item in mylist:
        if re.search(separator,item)!= None:
            if n > 0:
                word = re.split(separator, item, int(n))
            else:
                word = re.split(separator, item)
            for new_item in word: 
                if new_item.lstrip().rstrip() != '':
                    list.append(new_item.lstrip().rstrip())
    return list

def split_text(separator, string1, n=0):
    """
    return a list of string without white space of separator
    
    :param separator: the string to remove
    
    """
    list = []
    if re.search(separator, string1) is not None:
        if n > 0:
            word = re.split(separator,string1,int(n))
        else:
            word = re.split(separator,string1)
        for item in word: 
            if item.lstrip().rstrip() != '':
                list.append(item.lstrip().rstrip())
    return list

def look_for_tag(string1, begin, end=None):
    """
    this method  remove the begin and end tags given by the user
    from the string .
    
    :param begin: the initial tag
    :param end: the final tag
    :param string: the string to check
    
    :return: begin_flag==True if begin was found,
     end_flag==if end was found else return false, false
     
    """
    begin_flag = False
    end_flag = False
    if  re.search(begin,string1) is not None:
        begin_flag = True
    if end  is not None:
        if  re.search(end,string1) is not None:
            end_flag = True
    return begin_flag, end_flag

