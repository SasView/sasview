
import sys,re,string, wx   
from sans.guicomm.events import StatusEvent    

class SimultaneousFitPage(wx.Panel):
    """
        Simultaneous fitting panel
        All that needs to be defined are the
        two data members window_name and window_caption
    """
      ## Internal name for the AUI manager
    window_name = "simultaneous Fit page"
    ## Title to appear on top of the window
    window_caption = "Simultaneous Fit Page"
    
    
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
        """
             Simultaneous page display
        """
        self.parent = parent
        self.sizer3 = wx.GridBagSizer(5,5)
        self.sizer1 = wx.GridBagSizer(5,5)
        #self.sizer2 = wx.GridBagSizer(5,5)
        self.sizer2  = wx.BoxSizer(wx.HORIZONTAL)
        self.vbox  = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.sizer3)
        self.vbox.Add(self.sizer1)
        self.vbox.Add(self.sizer2)
        id = wx.NewId()
        self.btFit =wx.Button(self,id,'Constraint Fit')
        self.btFit.Bind(wx.EVT_BUTTON, self.onFit,id=id)
        self.btFit.SetToolTipString("Perform fit.")
        ix = 0
        iy = 1 
        self.cb1 = wx.CheckBox(self, -1,'Models', (10, 10))
        self.sizer3.Add(self.cb1,(iy, ix),(1,1),\
                        wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        wx.EVT_CHECKBOX(self, self.cb1.GetId(), self.select_all_model_name)
      
        text=wx.StaticText(self, -1, 'Constraint')
        self.sizer2.Add(text,0, wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)

        self.ctl2 = wx.TextCtrl(self, -1, style=wx.TE_MULTILINE)
       
        self.sizer2.Add(self.ctl2, 0, wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)
       
        self.sizer2.Add(self.btFit, 0, wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)
        self.params=[]
        self.model_list=[]
        self.model_toFit=[]
        self.page_finder={}
       
        self.vbox.Layout()
        self.vbox.Fit(self) 
        self.SetSizer(self.vbox)
        self.Centre()
        
        
    def onFit(self,event):
        """ signal for fitting"""
        for page in self.page_finder.iterkeys():
            page.set_model_parameter()
            
        if len(self.model_toFit) ==1 :
            self.manager._on_single_fit()
           # print "simfitpage: when here"
        elif len(self.model_toFit) > 1 :
            self._onTextEnter()
            self.set_model()
            self.manager._on_simul_fit()
        else:
            wx.PostEvent(self.parent.GrandParent, StatusEvent(status=\
                            "Select at least on model to fit "))
            
            
    def set_manager(self, manager):
        """
            set panel manager
            @param manager: instance of plugin fitting
        """
        self.manager = manager
        
        
    def select_all_model_name(self,event):
        """
            check all models names
        """
        self.model_toFit=[] 
        if self.cb1.GetValue()==True:
            for item in self.model_list:
                item[0].SetValue(True)
                #item[1].schedule_tofit(1)
                self.manager.schedule_for_fit( value=1,fitproblem =item[1]) 
                self.model_toFit.append(item)
        else:
            #print"simfit: deselected all"
            self.manager.schedule_for_fit( value=0,fitproblem =item[1]) 
            for item in self.model_list:
                item[0].SetValue(False) 
                #item[1].schedule_tofit(0)
                
            self.model_toFit=[]
       
            
    def add_model(self,page_finder):
        """
            Receive a dictionary containing information to display model name
            @param page_finder: the dictionary containing models information
        """
       
        self.model_list=[]
        self.model_toFit=[]
        self.sizer1.Clear(True)
        self.page_finder=page_finder
        self.cb1.SetValue(False)
        ix = 0
        iy = 1 
        list=[]
        for page, value in page_finder.iteritems():
            try:
                list = value.get_model()
                model = list[0]
                modelname = list[1]
                cb = wx.CheckBox(self, -1, modelname, (10, 10))
                cb.SetValue(False)
                self.sizer1.Add( cb,( iy,ix),(1,1),  wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
                ix = 0
                iy += 1 
                wx.EVT_CHECKBOX(self, cb.GetId(), self.select_model_name)
                self.model_list.append([cb,value,page,modelname])
            except:
                #wx.PostEvent(self.parent.GrandParent, StatusEvent(status="Simultaneous fit: %s doesn't have a model selected yet %s" % \
                #(value.get_data().group_id,sys.exc_value)))
                pass
        iy +=1
        self.sizer1.Add((20,20),( iy,ix),(1,1),  wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        self.sizer1.Layout()        
        self.vbox.Layout()
        
    def remove_model(self,delpage):
        """
             Remove  a checkbox and the name related to a model selected on page delpage
             @param delpage: the page removed
        """
        self.sizer1.Clear(True)
        ix = 0
        iy = 1 
        for item in self.model_list:
            try:
                # redraw the panel without the name of the model associated 
                # with the page to delete
                if not delpage in item:
                    #print "simfitpage:  redraw modelname",item[3]
                    cb = wx.CheckBox(self, -1, item[3], (10, 10))
                    cb.SetValue(False)
                    self.sizer1.Add( cb,( iy,ix),(1,1),  wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
                    ix = 0
                    iy += 1 
                    wx.EVT_CHECKBOX(self, cb.GetId(), self.select_model_name)
                else:
                    # if the page to delete in item remove it from the model list
                    self.model_list.remove(item)
            except:
                 wx.PostEvent(self.parent.GrandParent, StatusEvent(status="Page deletion Error: %s" % sys.exc_value))
                 
        self.sizer1.Layout()        
        self.vbox.Layout()
            
        
    def select_model_name(self,event):
        """
            Save interformation related to checkbox and their states
        """
        self.model_toFit=[]
        for item in self.model_list:
            if item[0].GetValue()==True:
                item[1].schedule_tofit('True')
                self.model_toFit.append(item)
                self.manager.schedule_for_fit( value=1,fitproblem =item[1]) 
            else:
                #print"simfit: deselected one"
                self.manager.schedule_for_fit( value=0,fitproblem =item[1]) 
                if item in self.model_toFit:
                    self.model_toFit.remove(item)
                    self.cb1.SetValue(False)
                    
        if len(self.model_list)==len(self.model_toFit):
            self.cb1.SetValue(True)
        else:
            self.cb1.SetValue(False)
     
        
   
    def set_model(self):
        """
            set_model take values in self.params which are the values enters by the user
            and try to assign them into the model concerned in self.manager. page.finder
        """
        if len(self.params) >0:
            for item in self.model_toFit:
                #print"simfitpage: self.model_toFit",item[1]
                list=item[1].get_model()
                #print "simfitpage: list fitpanel2",list,list[0]
                model=list[0]
                param_list=model.getParamList()
                print "simfitpage: on set_model self.params ",self.params
                if self.params !=[]:
                    for element in self.params:
                        if model.name == str(element[0]):
                            for item in param_list:
                                if item==str(element[1]):
                                    print "simfitpage: on set_model page 1",param_list
                                    print "simfitpage: model name",element[0], model.name
                                    print "simfitpage: param name ,param value",element[1],element[2]
                                    self.manager.set_page_finder(model.name,element[1],\
                                                                 str(element[2]))
                            #print "simfitpage:on set_model page 2",model.params['A'],self.params[2]
    
    def _onTextEnter(self):
        """
            get values from the constrainst textcrtl ,parses them into model name
            parameter name and parameters values.
            store them in a list self.params .when when params is not empty set_model uses it
            to reset the appropriate model and its appropriates parameters
        """
        value= self.ctl2.GetValue()
        if value:
            self.params=[]
            #print "simfitpage: value",value
            try:
                expression='[\s,;]'
                if re.search(expression,value) !=None:
                    word=re.split(expression,value)
                    #print "simfitpage: when herre",word
                    for item in word:
                        self.params.append(self.parser_helper(item))
                else:
                    self.params.append(self.parser_helper(value))  
            except:
                raise
                wx.PostEvent(self.parent.GrandParent, StatusEvent(status="Constraint Error: %s" % sys.exc_value))
        #print "simfitpage: self.params",self.params
        
        
        
    def parser_helper(self,value):
        """
             @return  param:a list containing the name of a model ,its parameters 
             value and name extracted from the constrainst controlbox
        """
        #print "simfitpage: value",value
        if string.find(value, "=") !=-1:
            model_param= re.split("=",value)
            param_name=model_param[0]
            param_value=model_param[1]
            #print"simfitpage: ", param_name
            #print "simfitpage: ",param_value
            if string.find(param_name,".")!=-1:
                param_names= re.split("\.",param_name)
                model_name=param_names[0]
                param_name=param_names[1]
                ##### just added
                print "simfitpage: param name",model_name,param_name
            
                param=[str(model_name),param_name,str(param_value)]
                #print "simfitpage: param",param
                return param
            else:
                raise ValueError,"cannot evaluate this expression"
                return
        else:
            raise ValueError,"Missing '=' in expression"
        
   
    
