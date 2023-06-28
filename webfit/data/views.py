from django.shortcuts import render
from django.shortcuts import HttpResponse

from .models import Data
from sasdata.dataloader.loader import Loader

loader = Loader()

# Create your views here.
def ImportData(request, version= None):
    #takes files string and turn it into DataInfo
    if Data.file_string != False:
        Data.data = loader.load(Data.file_string)
#opt in to uploading to example data pool
    if Data.opt_in == True:
        #upload data to example data pool
        loader.save(loader, file = "PUT FILE STRING HERE LATER", data = Data.data)

def ExportData(request, version = None):
    #takes DataInfo and saves it into to specified file location
    if Data.do_save == True:
        loader.save(loader, file = Data.saved_file_string, data = Data.data)

