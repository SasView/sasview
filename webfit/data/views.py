import os

from django.shortcuts import get_object_or_404
from django.http import HttpResponseBadRequest, HttpResponseForbidden, Http404
from django.contrib.auth.models import User
from django.core.files import File
from django.core.files.storage import FileSystemStorage 

from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import api_view

from sasdata.dataloader.loader import Loader
from serializers import DataSerializer
from .models import Data
from .forms import DataForm

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
        loader = Loader()
        public_data = get_object_or_404(Data, id = db_id)
        private_data = get_object_or_404(Data, id = db_id)
        if public_data.is_public:
            data_list= loader.load(public_data.file.path)
            contents = [str(data) for data in data_list]
            return_data = {public_data.file.__str__():contents}
            return Response(return_data)
        #rewrite with "user.is_authenticated"
        elif request.user.is_authenticated:
            return_data = {"info" : private_data.file.__str__()}
            return Response(return_data)
        return HttpResponseBadRequest("Database is either not public or wrong auth token")
    return HttpResponseBadRequest()


@api_view(['POST', 'PUT'])
def upload(request, data_id = None, version = None):
    #saves file
    if request.method == 'POST':
        form = DataForm(request.data, request.FILES)
        if form.is_valid():
            form.save()
        db = Data.objects.get(pk = form.instance.pk)
        if request.user.is_authenticated:
            serializer = DataSerializer(db, data={"file_name":os.path.basename(form.instance.file.path), "current_user" : request.user.id})
        else:
            serializer = DataSerializer(db, data={"file_name":os.path.basename(form.instance.file.path)})

    #saves or updates file
    elif request.method == 'PUT':
        #require data_id
        if data_id != None and request.user:
            if request.user.is_authenticated:
                userr = request.user
                db = Data.objects.filter(current_user = userr, id = data_id).get()
                form = DataForm(request.data, request.FILES, instance=db)
                if form.is_valid():
                    form.save()
                serializer = DataSerializer(db, data={"file_name":os.path.basename(form.instance.file.path), "current_user" : request.user.id})
            else:
                return HttpResponseForbidden("user is not logged in")
        else:
            return HttpResponseBadRequest()

    if serializer.is_valid():
        serializer.save()
        #TODO get warnings/errors later
        return_data = {"current_user":serializer.data["current_user"], "authenticated" : request.user.is_authenticated, "file_id" : db.id, "file_alternative_name":serializer.data["file_name"],"is_public" : serializer.data["is_public"]}
        return Response(return_data)


#TODO check if I should move to fit
@api_view(['GET'])
def download(request, data_id, version = None):
    if request.method == 'GET':
        storage = FileSystemStorage()
        data = get_object_or_404(Data, id = data_id)
        serializer = DataSerializer(data)
        if not serializer.is_public:
            #add session key later
            if not request.user.is_authenticated:
                return HttpResponseBadRequest("data is private, must log in")
        #TODO add issues later
        try:
            file = storage.open(serializer.file_name, 'rb')
        except Exception as e:
            return HttpResponseBadRequest(str(e))
        if file is None:
            raise Http404("File not found.")
        file_content = file.read()
        return Response(file_content, content_type="application/force_download")
    return HttpResponseBadRequest()
