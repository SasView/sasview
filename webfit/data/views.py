from django.shortcuts import get_object_or_404
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import api_view

from sasdata.dataloader.loader import Loader
from serializers import DataSerializers
from .models import Data

from rest_framework.permissions import IsAuthenticated



#TODO finish logger
#TODO look through whole code to make sure serializer updates to the correct object

@api_view(['GET'])
def list_data(request, version = None):
    if request.method == 'GET':
        data_list = {}
        public_data = Data.objects.filter(is_public = True)
        data_list += {"public_file_ids": public_data.id,}
        if request.user.is_authenticated:
            private_data = Data.objects.filter(current_user = request.user)
            data_list += {"user_data_ids": private_data.id,}
        return Response(data_list)
    return HttpResponseBadRequest()


@api_view(['GET'])
def data_info(request, db_id, version = None):
    if request.method == 'GET':
        public_data = get_object_or_404(Data, id = db_id)
        private_data = get_object_or_404(Data, id = db_id)
        if public_data.is_public:
            return_data = {"info" : public_data.file.__str__()}
            return return_data
        elif request.user.token == private_data.current_user.token:
            return_data = {"info" : private_data.file.__str__()}
            return return_data
        return HttpResponseBadRequest("Database is either not public or wrong auth token")
    return HttpResponseBadRequest()


#perhaps rename data.obj from file -> data_obj as it gets confused with file.file
#data = session_token, opt_in, filename
#file = data_file
#TODO IF WE'RE USING SESSION KEYS, HOW DO WE CONNECT THEM TO DBS??
@api_view(['POST', 'PUT'])
def upload(request, data_id = None, version = None):
    serializer = DataSerializers()
    
    #saves file
    if request.method == 'POST':
        serializer(file = request.file, is_public = request.data.is_public)
        if request.user.is_authenticated:
            #doesn't check user, instead sets current_user as user
            userr = request.user
            serializer(current_user = userr)
    
    #saves or updates file
    elif request.method == 'PUT':
        #require data_id
        if data_id == None:
            if request.user.is_authenticated:
                userr = request.user
                data = Data.objects.filter(current_user = userr, id = data_id).get()
                serializer(data, data=request.file, is_public = request.data.is_public)
            else:
                return HttpResponseForbidden
        else:
            return HttpResponseBadRequest()

    if serializer.is_valid():
        serializer.save()
        #TODO get warnings/errors later
        return_data = {"authenticated" : request.user.is_authenticated, "file_id" : serializer.id, "is_public" : serializer.is_public}
        return Response(return_data)
    return HttpResponseBadRequest()
    #data is actually loaded inside fit view


#TODO check if I should move to fit
@api_view(['GET'])
def download(request, data_id, version = None):
    if request.method == 'GET':
        data = get_object_or_404(Data, id = data_id)
        serializer = DataSerializers(data)
        if not serializer.is_public:
            #add session key later
            if request.user.token != serializer.current_user.token:
                return HttpResponseBadRequest("data is private, must log in")
        #TODO add issues later
        return Response(serializer.file)
    return HttpResponseBadRequest()
        
