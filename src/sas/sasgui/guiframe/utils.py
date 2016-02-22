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

class IdList:
    """
    Create a list of wx ids that can be reused.

    Ids for items need to be unique within their context.  In a dynamic
    application where the number of ids needed different each time the
    form is created, depending for example, on the number of items that
    need to be shown in the context menu, you cannot preallocate the
    ids that you are going to use for the form.  Instead, you can use
    an IdList, which will reuse ids from context to context, adding new
    ones if the new context requires more than a previous context.

    IdList is set up as an iterator, which returns new ids forever
    or until it runs out.  This makes it pretty useful for defining
    menus::

        class Form(wx.Dialog):
            _form_id_pool = IdList()
            def __init__(self):
                ...
                menu = wx.Menu()
                for item, wx_id in zip(menu_items, self._form_id_pool):
                    name, description, callback = item
                    menu.Append(wx_id, name, description)
                    wx.EVT_MENU(self, wx_id, callback)
                ...

    It is a little unusual to use an iterator outside of a loop, but it is
    supported. For example, when defining a form, your class definition
    might look something like::

        class Form(wx.Dialog):
            _form_id_pool = IdList()
            def __init__(self, pairs, ...):
                ids = iter(_form_id_pool)
                ...
                wx.StaticText(self, ids.next(), "Some key-value pairs")
                for name, value in pairs:
                    label = wx.StaticText(self, ids.next(), name)
                    input = wx.TextCtrl(self, ids.next(), value=str(value))
                    ...
                ...

    If the dialog is really dynamic, and not defined all in one place, then
    save the id list iterator as *self._ids = iter(_form_id_pool)* in the
    constructor.

    The wx documentation is not clear on whether ids need to be unique.
    Clearly different dialogs can use the same ids, as this is done for the
    standard button ids such as wx.ID_HELP.  Presumably each widget on the
    form needs its own id, but whether these ids can match the ids of menu
    items is not indicated, or whether different submenus need their own
    ids.  Using different id lists for menu items and widgets is safest,
    but probably not necessary.  And what about notebook tabs.  Do the
    ids need to be unique across all tabs?
    """
    def __init__(self):
        self._ids = []
    def __iter__(self):
        return _IdListIterator(self)
    def __getitem__(self, index):
        while index >= len(self._ids):
            self._ids.append(wx.NewId())
        return self._ids[index]

class _IdListIterator:
    def __init__(self, id_list):
        self.id_list = id_list
        self.index = -1
    def next(self):
        self.index += 1
        return self.id_list[self.index]

