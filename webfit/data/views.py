from django.shortcuts import get_object_or_404
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.contrib.auth.models import User
from django.core.files import File

from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import api_view

from sasdata.dataloader.loader import Loader
from serializers import DataSerializer
from .models import Data

#TODO finish logger
#TODO look through whole code to make sure serializer updates to the correct object

@api_view(['GET'])
def list_data(request, username = None, version = None):
    if request.method == 'GET':
        data_list = {}
        public_data = Data.objects.filter(is_public = True)
        for x in public_data:
            data_list["public_file_ids"] = x.id
        #figure out how to get id of querysets individual objs
        if username:
            if username == request.user.username and request.user.is_authenticated:
                private_data = Data.objects.filter(current_user = request.user.id)
                for x in private_data:
                    data_list["user_data_ids"] = x.id
            else:
                return HttpResponseBadRequest("user is not logged in, or username is not same as current user")
        return Response(data_list)
    return HttpResponseBadRequest("not get method")


@api_view(['GET'])
def data_info(request, db_id, version = None):
    if request.method == 'GET':
        public_data = get_object_or_404(Data, id = db_id)
        private_data = get_object_or_404(Data, id = db_id)
        if public_data.is_public:
            return_data = {"info" : public_data.file.__str__()}
            return Response(return_data)
        #rewrite with "user.is_authenticated"
        elif request.user.is_authenticated:
            return_data = {"info" : private_data.file.__str__()}
            return Response(return_data)
        return HttpResponseBadRequest("Database is either not public or wrong auth token")
    return HttpResponseBadRequest()


@api_view(['POST', 'PUT'])
def upload(request, data_id = None, version = None):
    serializer = DataSerializer()
    
    #saves file
    if request.method == 'POST':
        serializer(data = request.data, file = File(open(), 'rb'))
        if request.user.is_authenticated:
            serializer(current_user = request.user)
    
    #saves or updates file
    elif request.method == 'PUT':
        #require data_id
        if data_id != None:
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
        serializer = DataSerializer(data)
        if not serializer.is_public:
            #add session key later
            if request.user.token != serializer.current_user.token:
                return HttpResponseBadRequest("data is private, must log in")
        #TODO add issues later
        return Response(serializer.file)
    return HttpResponseBadRequest()
        
