"""
    State class for the invariant UI
"""

# import time
import os
import sys
import logging
import copy
import sas.sascalc.dataloader
# from xml.dom.minidom import parse
from lxml import etree
from sas.sascalc.dataloader.readers.cansas_reader import Reader as CansasReader
from sas.sascalc.dataloader.readers.cansas_reader import get_content
from sas.sasgui.guiframe.utils import format_number
from sas.sasgui.guiframe.gui_style import GUIFRAME_ID
from sas.sasgui.guiframe.dataFitting import Data1D

logger = logging.getLogger(__name__)

INVNODE_NAME = 'invariant'
CANSAS_NS = "cansas1d/1.0"

# default state
DEFAULT_STATE = {'file': 'None',
                 'compute_num':0,
                 'state_num':0,
                 'is_time_machine':False,
                 'background_tcl':0.0,
                 'scale_tcl':1.0,
                 'contrast_tcl':1.0,
                 'porod_constant_tcl':'',
                 'npts_low_tcl':10,
                 'npts_high_tcl':10,
                 'power_high_tcl':4.0,
                 'power_low_tcl': 4.0,
                 'enable_high_cbox':False,
                 'enable_low_cbox':False,
                 'guinier': True,
                 'power_law_high': False,
                 'power_law_low': False,
                 'fit_enable_high': False,
                 'fit_enable_low': False,
                 'fix_enable_high':True,
                 'fix_enable_low':True,
                 'volume_tcl':'',
                 'volume_err_tcl':'',
                 'surface_tcl':'',
                 'surface_err_tcl':''}
# list of states: This list will be filled as panel
# init and the number of states increases
state_list = {}
bookmark_list = {}
# list of input parameters (will be filled up on panel init) used by __str__
input_list = {'background_tcl':0,
              'scale_tcl':0,
              'contrast_tcl':0,
              'porod_constant_tcl':'',
              'npts_low_tcl':0,
              'npts_high_tcl':0,
              'power_high_tcl':0,
              'power_low_tcl': 0}
# list of output parameters (order sensitive) used by __str__
output_list = [["qstar_low", "Q* from low Q extrapolation [1/(cm*A)]"],
               ["qstar_low_err", "dQ* from low Q extrapolation"],
               ["qstar_low_percent", "Q* percent from low Q extrapolation"],
               ["qstar", "Q* from data [1/(cm*A)]"],
               ["qstar_err", "dQ* from data"],
               ["qstar_percent", "Q* percent from data"],
               ["qstar_high", "Q* from high Q extrapolation [1/(cm*A)]"],
               ["qstar_high_err", "dQ* from high Q extrapolation"],
               ["qstar_high_percent", "Q* percent from low Q extrapolation"],
               ["qstar_total", "total Q* [1/(cm*A)]"],
               ["qstar_total_err", "total dQ*"],
               ["volume", "volume fraction"],
               ["volume_err", "volume fraction error"],
               ["surface", "specific surface"],
               ["surface_err", "specific surface error"]]



class InvariantState(object):
    """
    Class to hold the state information of the InversionControl panel.
    """
    def __init__(self):
        """
        Default values
        """
        # Input
        self.file = None
        self.data = Data1D(x=[], y=[], dx=None, dy=None)
        self.theory_lowQ = Data1D(x=[], y=[], dy=None)
        self.theory_lowQ.symbol = GUIFRAME_ID.CURVE_SYMBOL_NUM
        self.theory_highQ = Data1D(x=[], y=[], dy=None)
        self.theory_highQ.symbol = GUIFRAME_ID.CURVE_SYMBOL_NUM
        # self.is_time_machine = False
        self.saved_state = DEFAULT_STATE
        self.state_list = state_list
        self.bookmark_list = bookmark_list
        self.input_list = input_list
        self.output_list = output_list

        self.compute_num = 0
        self.state_num = 0
        self.timestamp = ('00:00:00', '00/00/0000')
        self.container = None
        # plot image
        self.wximbmp = None
        # report_html strings
        import sas.sasgui.perspectives.invariant as invariant
        path = invariant.get_data_path(media='media')
        path_report_html = os.path.join(path, "report_template.html")
        html_template = open(path_report_html, "r")
        self.template_str = html_template.read()
        self.report_str = self.template_str
        # self.report_str_save = None
        html_template.close()

    def __str__(self):
        """
        Pretty print

        : return: string representing the state
        """
        # Input string
        compute_num = self.saved_state['compute_num']
        compute_state = self.state_list[str(compute_num)]
        my_time, date = self.timestamp
        file_name = self.file

        state_num = int(self.saved_state['state_num'])
        state = "\n[Invariant computation for %s: " % file_name
        state += "performed at %s on %s] \n" % (my_time, date)
        state += "State No.: %d \n" % state_num
        state += "\n=== Inputs ===\n"

        # text ctl general inputs ( excluding extrapolation text ctl)
        for key, value in self.input_list.items():
            if value == '':
                continue
            key_split = key.split('_')
            max_ind = len(key_split) - 1
            if key_split[max_ind] == 'tcl':
                name = ""
                if key_split[1] == 'low' or key_split[1] == 'high':
                    continue
                for ind in range(0, max_ind):
                    name += " %s" % key_split[ind]
                state += "%s:   %s\n" % (name.lstrip(" "), value)

        # other input parameters
        extra_lo = compute_state['enable_low_cbox']
        if compute_state['enable_low_cbox']:
            if compute_state['guinier']:
                extra_lo = 'Guinier'
            else:
                extra_lo = 'Power law'
        extra_hi = compute_state['enable_high_cbox']
        if compute_state['enable_high_cbox']:
            extra_hi = 'Power law'
        state += "\nExtrapolation:  High=%s; Low=%s\n" % (extra_hi, extra_lo)
        low_off = False
        high_off = False
        for key, value in self.input_list.items():
            key_split = key.split('_')
            max_ind = len(key_split) - 1
            if key_split[max_ind] == 'tcl':
                name = ""
                # check each buttons whether or not ON or OFF
                if key_split[1] == 'low' or key_split[1] == 'high':
                    if not compute_state['enable_low_cbox'] and \
                        key_split[max_ind - 1] == 'low':
                        low_off = True
                        continue
                    elif not compute_state['enable_high_cbox'] and \
                        key_split[max_ind - 1] == 'high':
                        high_off = True
                        continue
                    elif extra_lo == 'Guinier' and key_split[0] == 'power' and \
                        key_split[max_ind - 1] == 'low':
                        continue
                    for ind in range(0, max_ind):
                        name += " %s" % key_split[ind]
                    name = name.lstrip(" ")
                    if name == "power low":
                        if compute_state['fix_enable_low']:
                            name += ' (Fixed)'
                        else:
                            name += ' (Fitted)'
                    if name == "power high":
                        if compute_state['fix_enable_high']:
                            name += ' (Fixed)'
                        else:
                            name += ' (Fitted)'
                    state += "%s:   %s\n" % (name, value)
        # Outputs
        state += "\n=== Outputs ==="
        for item in output_list:
            item_split = item[0].split('_')
            # Exclude the extrapolation that turned off
            if len(item_split) > 1:
                if low_off and item_split[1] == 'low':
                    continue
                if high_off and item_split[1] == 'high':
                    continue
            max_ind = len(item_split) - 1
            value = None
            if hasattr(self.container, item[0]):
                # Q* outputs
                value = getattr(self.container, item[0])
            else:
                # other outputs than Q*
                name = item[0] + "_tcl"
                if name in list(self.saved_state.keys()):
                    value = self.saved_state[name]

            # Exclude the outputs w/''
            if value == '':
                continue
            # Error outputs
            if item_split[max_ind] == 'err':
                state += "+- %s " % format_number(value)
            # Percentage outputs
            elif item_split[max_ind] == 'percent':
                value = float(value) * 100
                state += "(%s %s)" % (format_number(value), '%')
            # Outputs
            else:
                state += "\n%s:   %s " % (item[1],
                                          format_number(value, high=True))
        # Include warning msg
        if self.container is not None:
            state += "\n\nNote:\n" + self.container.warning_msg
        return state

    def clone_state(self):
        """
        deepcopy the state
        """
        return copy.deepcopy(self.saved_state)

    def toXML(self, file="inv_state.inv", doc=None, entry_node=None):
        """
        Writes the state of the InversionControl panel to file, as XML.

        Compatible with standalone writing, or appending to an
        already existing XML document. In that case, the XML document
        is required. An optional entry node in the XML document
        may also be given.

        : param file: file to write to
        : param doc: XML document object [optional]
        : param entry_node: XML node within the document at which we will append the data [optional]
        """
        # TODO: Get this to work
        from xml.dom.minidom import getDOMImplementation
        import time
        timestamp = time.time()
        # Check whether we have to write a standalone XML file
        if doc is None:
            impl = getDOMImplementation()

            doc_type = impl.createDocumentType(INVNODE_NAME, "1.0", "1.0")

            newdoc = impl.createDocument(None, INVNODE_NAME, doc_type)
            top_element = newdoc.documentElement
        else:
            # We are appending to an existing document
            newdoc = doc
            top_element = newdoc.createElement(INVNODE_NAME)
            if entry_node is None:
                newdoc.documentElement.appendChild(top_element)
            else:
                entry_node.appendChild(top_element)

        attr = newdoc.createAttribute("version")
        attr.nodeValue = '1.0'
        top_element.setAttributeNode(attr)

        # File name
        element = newdoc.createElement("filename")
        if self.file is not None and self.file != '':
            element.appendChild(newdoc.createTextNode(str(self.file)))
        else:
            element.appendChild(newdoc.createTextNode(str(file)))
        top_element.appendChild(element)

        element = newdoc.createElement("timestamp")
        element.appendChild(newdoc.createTextNode(time.ctime(timestamp)))
        attr = newdoc.createAttribute("epoch")
        attr.nodeValue = str(timestamp)
        element.setAttributeNode(attr)
        top_element.appendChild(element)

        # Current state
        state = newdoc.createElement("state")
        top_element.appendChild(state)

        for name, value in self.saved_state.items():
            element = newdoc.createElement(str(name))
            element.appendChild(newdoc.createTextNode(str(value)))
            state.appendChild(element)

        # State history list
        history = newdoc.createElement("history")
        top_element.appendChild(history)

        for name, value in self.state_list.items():
            history_element = newdoc.createElement('state_' + str(name))
            for state_name, state_value in value.items():
                state_element = newdoc.createElement(str(state_name))
                child = newdoc.createTextNode(str(state_value))
                state_element.appendChild(child)
                history_element.appendChild(state_element)
            # history_element.appendChild(state_list_element)
            history.appendChild(history_element)

        # Bookmarks  bookmark_list[self.bookmark_num] = [\
        # my_time,date,state,comp_state]
        bookmark = newdoc.createElement("bookmark")
        top_element.appendChild(bookmark)
        item_list = ['time', 'date', 'state', 'comp_state']
        for name, value_list in self.bookmark_list.items():
            element = newdoc.createElement('mark_' + str(name))
            _, date, state, comp_state = value_list
            time_element = newdoc.createElement('time')
            time_element.appendChild(newdoc.createTextNode(str(value_list[0])))
            date_element = newdoc.createElement('date')
            date_element.appendChild(newdoc.createTextNode(str(value_list[1])))
            state_list_element = newdoc.createElement('state')
            comp_state_list_element = newdoc.createElement('comp_state')
            for state_name, state_value in value_list[2].items():
                state_element = newdoc.createElement(str(state_name))
                child = newdoc.createTextNode(str(state_value))
                state_element.appendChild(child)
                state_list_element.appendChild(state_element)
            for comp_name, comp_value in value_list[3].items():
                comp_element = newdoc.createElement(str(comp_name))
                comp_element.appendChild(newdoc.createTextNode(str(comp_value)))
                comp_state_list_element.appendChild(comp_element)
            element.appendChild(time_element)
            element.appendChild(date_element)
            element.appendChild(state_list_element)
            element.appendChild(comp_state_list_element)
            bookmark.appendChild(element)

        # Save the file
        if doc is None:
            fd = open('test000', 'w')
            fd.write(newdoc.toprettyxml())
            fd.close()
            return None
        else:
            return newdoc

    def fromXML(self, file=None, node=None):
        """
        Load invariant states from a file

        : param file: .inv file
        : param node: node of a XML document to read from
        """
        if file is not None:
            msg = "InvariantSate no longer supports non-CanSAS"
            msg += " format for invariant files"
            raise RuntimeError(msg)

        if node.get('version')\
            and node.get('version') == '1.0':

            # Get file name
            entry = get_content('ns:filename', node)
            if entry is not None:
                file_name = entry.text.strip()

            # Get time stamp
            entry = get_content('ns:timestamp', node)
            if entry is not None and entry.get('epoch'):
                try:
                    timestamp = (entry.get('epoch'))
                except:
                    msg = "InvariantSate.fromXML: Could not read"
                    msg += " timestamp\n %s" % sys.exc_info()[1]
                    logger.error(msg)

            # Parse bookmarks
            entry_bookmark = get_content('ns:bookmark', node)

            for ind in range(1, len(entry_bookmark) + 1):
                temp_state = {}
                temp_bookmark = {}
                entry = get_content('ns:mark_%s' % ind, entry_bookmark)

                if entry is not None:
                    my_time = get_content('ns:time', entry)
                    val_time = str(my_time.text.strip())
                    date = get_content('ns:date', entry)
                    val_date = str(date.text.strip())
                    state_entry = get_content('ns:state', entry)
                    for item in DEFAULT_STATE:
                        input_field = get_content('ns:%s' % item, state_entry)
                        val = str(input_field.text.strip())
                        if input_field is not None:
                            temp_state[item] = val
                    comp_entry = get_content('ns:comp_state', entry)

                    for item in DEFAULT_STATE:
                        input_field = get_content('ns:%s' % item, comp_entry)
                        val = str(input_field.text.strip())
                        if input_field is not None:
                            temp_bookmark[item] = val
                    try:
                        self.bookmark_list[ind] = [val_time, val_date, temp_state, temp_bookmark]
                    except:
                        raise "missing components of bookmarks..."
            # Parse histories
            entry_history = get_content('ns:history', node)

            for ind in range(0, len(entry_history)):
                temp_state = {}
                entry = get_content('ns:state_%s' % ind, entry_history)

                if entry is not None:
                    for item in DEFAULT_STATE:
                        input_field = get_content('ns:%s' % item, entry)
                        if input_field.text is not None:
                            val = str(input_field.text.strip())
                        else:
                            val = ''
                        if input_field is not None:
                            temp_state[item] = val
                            self.state_list[str(ind)] = temp_state

            # Parse current state (ie, saved_state)
            entry = get_content('ns:state', node)
            if entry is not None:
                for item in DEFAULT_STATE:
                    input_field = get_content('ns:%s' % item, entry)
                    if input_field.text is not None:
                        val = str(input_field.text.strip())
                    else:
                        val = ''
                    if input_field is not None:
                        self.set_saved_state(name=item, value=val)
            self.file = file_name

    def set_report_string(self):
        """
        Get the values (strings) from __str__ for report
        """
        strings = self.__str__()

        # default string values
        for num in range(1, 19):
            exec("s_%s = 'NA'" % str(num))
        lines = strings.split('\n')
        # get all string values from __str__()
        for line in range(0, len(lines)):
            if line == 1:
                s_1 = lines[1]
            elif line == 2:
                s_2 = lines[2]
            else:
                item = lines[line].split(':')
                item[0] = item[0].strip()
                if item[0] == "scale":
                    s_3 = item[1]
                elif item[0] == "porod constant":
                    s_4 = item[1]
                elif item[0] == "background":
                    s_5 = item[1]
                elif item[0] == "contrast":
                    s_6 = item[1]
                elif item[0] == "Extrapolation":
                    extra = item[1].split(";")
                    bool_0 = extra[0].split("=")
                    bool_1 = extra[1].split("=")
                    s_8 = " " + bool_0[0] + "Q region = " + bool_0[1]
                    s_7 = " " + bool_1[0] + "Q region = " + bool_1[1]
                elif item[0] == "npts low":
                    s_9 = item[1]
                elif item[0] == "npts high":
                    s_10 = item[1]
                elif item[0] == "volume fraction":
                    val = item[1].split("+-")[0].strip()
                    error = item[1].split("+-")[1].strip()
                    s_17 = val + " &plusmn; " + error
                elif item[0] == "specific surface":
                    val = item[1].split("+-")[0].strip()
                    error = item[1].split("+-")[1].strip()
                    s_18 = val + " &plusmn; " + error
                elif item[0].split("(")[0].strip() == "power low":
                    s_11 = item[0] + " =" + item[1]
                elif item[0].split("(")[0].strip() == "power high":
                    s_12 = item[0] + " =" + item[1]
                elif item[0].split("[")[0].strip() == "Q* from low Q extrapolation":
                    # looks messy but this way the symbols +_ and % work on html
                    val = item[1].split("+-")[0].strip()
                    error = item[1].split("+-")[1].strip()
                    err = error.split("%")[0].strip()
                    percent = error.split("%")[1].strip()
                    s_13 = val + " &plusmn; " + err + "&#37" + percent
                elif item[0].split("[")[0].strip() == "Q* from data":
                    val = item[1].split("+-")[0].strip()
                    error = item[1].split("+-")[1].strip()
                    err = error.split("%")[0].strip()
                    percent = error.split("%")[1].strip()
                    s_14 = val + " &plusmn; " + err + "&#37" + percent
                elif item[0].split("[")[0].strip() == "Q* from high Q extrapolation":
                    val = item[1].split("+-")[0].strip()
                    error = item[1].split("+-")[1].strip()
                    err = error.split("%")[0].strip()
                    percent = error.split("%")[1].strip()
                    s_15 = val + " &plusmn; " + err + "&#37" + percent
                elif item[0].split("[")[0].strip() == "total Q*":
                    val = item[1].split("+-")[0].strip()
                    error = item[1].split("+-")[1].strip()
                    s_16 = val + " &plusmn; " + error
                else:
                    continue

        s_1 = self._check_html_format(s_1)
        file_name = self._check_html_format(self.file)

        # make plot image
        self.set_plot_state(extra_high=bool_0[1], extra_low=bool_1[1])
        # get ready for report with setting all the html strings
        self.report_str = str(self.template_str) % (s_1, s_2,
                                                    s_3, s_4, s_5, s_6, s_7, s_8,
                                                    s_9, s_10, s_11, s_12, s_13, s_14, s_15,
                                                    s_16, s_17, s_18, file_name, "%s")

    def _check_html_format(self, name):
        """
        Check string '%' for html format
        """
        if name.count('%'):
            name = name.replace('%', '&#37')

        return name

    def set_saved_state(self, name, value):
        """
        Set the state list

        : param name: name of the state component
        : param value: value of the state component
        """
        rb_list = [['power_law_low', 'guinier'],
                   ['fit_enable_low', 'fix_enable_low'],
                   ['fit_enable_high', 'fix_enable_high']]

        self.name = value
        self.saved_state[name] = value
        # set the count part of radio button clicked
        # False for the saved_state
        for title, content in rb_list:
            if name == title:
                name = content
                value = False
            elif name == content:
                name = title
                value = False
        self.saved_state[name] = value
        self.state_num = self.saved_state['state_num']

    def set_plot_state(self, extra_high=False, extra_low=False):
        """
        Build image state that wx.html understand
        by plotting, putting it into wx.FileSystem image object

        : extrap_high,extra_low: low/high extrapolations
        are possible extra-plots
        """
        # some imports
        import wx
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_agg import FigureCanvasAgg

        # we use simple plot, not plotpanel
        # make matlab figure
        fig = plt.figure()
        fig.set_facecolor('w')
        graph = fig.add_subplot(111)

        # data plot
        graph.errorbar(self.data.x, self.data.y, yerr=self.data.dy, fmt='o')
        # low Q extrapolation fit plot
        if not extra_low == 'False':
            graph.plot(self.theory_lowQ.x, self.theory_lowQ.y)
        # high Q extrapolation fit plot
        if not extra_high == 'False':
            graph.plot(self.theory_highQ.x, self.theory_highQ.y)
        graph.set_xscale("log", nonposx='clip')
        graph.set_yscale("log", nonposy='clip')
        graph.set_xlabel('$\\rm{Q}(\\AA^{-1})$', fontsize=12)
        graph.set_ylabel('$\\rm{Intensity}(cm^{-1})$', fontsize=12)
        canvas = FigureCanvasAgg(fig)
        # actually make image
        canvas.draw()

        # make python.Image object
        # size
        w, h = canvas.get_width_height()
        # convert to wx.Image
        wximg = wx.EmptyImage(w, h)
        # wxim.SetData(img.convert('RGB').tostring() )
        wximg.SetData(canvas.tostring_rgb())
        # get the dynamic image for the htmlwindow
        wximgbmp = wx.BitmapFromImage(wximg)
        # store the image in wx.FileSystem Object
        wx.FileSystem.AddHandler(wx.MemoryFSHandler())
        # use wx.MemoryFSHandler
        self.imgRAM = wx.MemoryFSHandler()
        # AddFile, image can be retrieved with 'memory:filename'
        self.imgRAM.AddFile('img_inv.png', wximgbmp, wx.BITMAP_TYPE_PNG)

        self.wximgbmp = 'memory:img_inv.png'
        self.image = fig

class Reader(CansasReader):
    """
    Class to load a .inv invariant file
    """
    # # File type
    type_name = "Invariant"

    # # Wildcards
    type = ["Invariant file (*.inv)|*.inv",
            "SASView file (*.svs)|*.svs"]
    # # List of allowed extensions
    ext = ['.inv', '.INV', '.svs', 'SVS']

    def __init__(self, call_back, cansas=True):
        """
        Initialize the call-back method to be called
        after we load a file

        : param call_back: call-back method
        : param cansas:  True = files will be written/read in CanSAS format
                        False = write CanSAS format
        """
        # # Call back method to be executed after a file is read
        self.call_back = call_back
        # # CanSAS format flag
        self.cansas = cansas
        self.state = None

    def read(self, path):
        """
        Load a new invariant state from file

        : param path: file path
        : return: None
        """
        if self.cansas == True:
            return self._read_cansas(path)
        else:
            return self._read_standalone(path)

    def _read_standalone(self, path):
        """
        Load a new invariant state from file.
        The invariant node is assumed to be the top element.

        : param path: file path
        : return: None
        """
        # Read the new state from file
        state = InvariantState()

        state.fromXML(file=path)

        # Call back to post the new state
        self.call_back(state)
        return None

    def _parse_state(self, entry):
        """
        Read an invariant result from an XML node

        : param entry: XML node to read from
        : return: InvariantState object
        """
        state = None
        # Locate the invariant node
        try:
            nodes = entry.xpath('ns:%s' % INVNODE_NAME,
                                namespaces={'ns': CANSAS_NS})
            # Create an empty state
            if nodes != []:
                state = InvariantState()
                state.fromXML(node=nodes[0])
        except:
            msg = "XML document does not contain invariant"
            msg += " information.\n %s" % sys.exc_info()[1]
            logger.info(msg)
        return state

    def _read_cansas(self, path):
        """
        Load data and invariant information from a CanSAS XML file.

        : param path: file path
        : return: Data1D object if a single SASentry was found,
                    or a list of Data1D objects if multiple entries were found,
                    or None of nothing was found
        : raise RuntimeError: when the file can't be opened
        : raise ValueError: when the length of the data vectors are inconsistent
        """
        output = []
        if os.path.isfile(path):
            basename = os.path.basename(path)
            root, extension = os.path.splitext(basename)

            if  extension.lower() in self.ext or \
                extension.lower() == '.xml':
                tree = etree.parse(path, parser=etree.ETCompatXMLParser())

                # Check the format version number
                # Specifying the namespace will take care of
                # the file format version
                root = tree.getroot()

                entry_list = root.xpath('/ns:SASroot/ns:SASentry',
                                        namespaces={'ns': CANSAS_NS})

                for entry in entry_list:
                    invstate = self._parse_state(entry)
                    # invstate could be None when .svs file is loaded
                    # in this case, skip appending to output
                    if invstate is not None:
                        sas_entry, _ = self._parse_entry(entry)
                        sas_entry.meta_data['invstate'] = invstate
                        sas_entry.filename = invstate.file
                        output.append(sas_entry)
        else:
            raise RuntimeError("%s is not a file" % path)

        # Return output consistent with the loader's api
        if len(output) == 0:
            return None
        elif len(output) == 1:
            # Call back to post the new state
            self.state = output[0].meta_data['invstate']
            self.call_back(state=output[0].meta_data['invstate'],
                           datainfo=output[0])
            return output[0]
        else:
            return output

    def get_state(self):
        return self.state

    def write(self, filename, datainfo=None, invstate=None):
        """
        Write the content of a Data1D as a CanSAS XML file

        : param filename: name of the file to write
        : param datainfo: Data1D object
        : param invstate: InvariantState object
        """
        # Sanity check
        if self.cansas == True:
            doc = self.write_toXML(datainfo, invstate)
            # Write the XML document
            fd = open(filename, 'w')
            fd.write(doc.toprettyxml())
            fd.close()
        else:
            invstate.toXML(file=filename)

    def write_toXML(self, datainfo=None, state=None):
        """
        Write toXML, a helper for write()

        : return: xml doc
        """
        if datainfo is None:
            datainfo = sas.sascalc.dataloader.data_info.Data1D(x=[], y=[])
        elif not issubclass(datainfo.__class__, sas.sascalc.dataloader.data_info.Data1D):
            msg = "The cansas writer expects a Data1D"
            msg += " instance: %s" % str(datainfo.__class__.__name__)
            raise RuntimeError(msg)
        # make sure title and data run is filled up.
        if datainfo.title is None or datainfo.title == '':
            datainfo.title = datainfo.name
        if datainfo.run_name is None or datainfo.run_name == {}:
            datainfo.run = [str(datainfo.name)]
            datainfo.run_name[0] = datainfo.name
        # Create basic XML document
        doc, sasentry = self._to_xml_doc(datainfo)
        # Add the invariant information to the XML document
        if state is not None:
            doc = state.toXML(datainfo.name, doc=doc, entry_node=sasentry)
        return doc
