import os

from django.core.files.storage import FileSystemStorage
from django.http import Http404, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view

#TODO go over to see if token is needed for is_authenticated
from rest_framework.response import Response
from serializers import DataSerializer

from sasdata.dataloader.loader import Loader

from .forms import DataForm
from .models import Data

#TODO finish logger
#TODO look through whole code to make sure serializer updates to the correct object

@api_view(['GET'])
def list_data(request, username = None, version = None):
    if request.method == 'GET':
        if username:
            data_list = {"user_data_ids":{}}
            if username == request.user.username and request.user.is_authenticated:
                private_data = Data.objects.filter(current_user = request.user.id)
                for x in private_data:
                    data_list["user_data_ids"][x.id] = x.file_name
            else:
                return HttpResponseBadRequest("user is not logged in, or username is not same as current user")
        else:
            public_data = Data.objects.filter(is_public = True)
            data_list = {"public_data_ids":{}}
            for x in public_data:
                data_list["public_data_ids"][x.id] = x.file_name
        return Response(data_list)
    return HttpResponseBadRequest("not get method")


@api_view(['GET'])
def data_info(request, db_id, version = None):
    if request.method == 'GET':
        loader = Loader()
        data_db = get_object_or_404(Data, id = db_id)
        if data_db.is_public:
            data_list= loader.load(data_db.file.path)
            contents = [str(data) for data in data_list]
            return_data = {data_db.file_name:contents}
        #rewrite with "user.is_authenticated"
        elif (data_db.current_user == request.user) and request.user.is_authenticated:
            data_list = loader.load(data_db.file.path)
            contents = [str(data) for data in data_list]
            return_data = {data_db.file_name:contents}
        else:
            return HttpResponseBadRequest("Database is either not public or wrong auth token")
        return Response(return_data)
    return HttpResponseBadRequest()


@api_view(['POST', 'PUT'])
def upload(request, data_id = None, version = None):
    #saves file
    if request.method == 'POST':
        form = DataForm(request.data, request.FILES)
        if form.is_valid():
            form.save()
        db = Data.objects.get(pk = form.instance.pk)

        #TODO should we allow anonymous users to upload data? Figure out tokens
        if request.user.is_authenticated:
            serializer = DataSerializer(db, data={"file_name":os.path.basename(form.instance.file.path), "current_user" : request.user.id})
        else:
            serializer = DataSerializer(db, data={"file_name":os.path.basename(form.instance.file.path)})

    #saves or updates file
    elif request.method == 'PUT':
        #require data_id
        if data_id is not None and request.user:
            if request.user.is_authenticated:
                db = get_object_or_404(Data, current_user = request.user.id, id = data_id)
                form = DataForm(request.data, request.FILES, instance=db)
                if form.is_valid():
                    form.save()
                serializer = DataSerializer(db, data={"file_name":os.path.basename(form.instance.file.path)}, partial = True)
            else:
                return HttpResponseForbidden("user is not logged in")
        else:
            return HttpResponseBadRequest()

    if serializer.is_valid():
        serializer.save()
        #TODO get warnings/errors later
        return_data = {"current_user":request.user.username, "authenticated" : request.user.is_authenticated, "file_id" : db.id, "file_alternative_name":serializer.data["file_name"],"is_public" : serializer.data["is_public"]}
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
            file = storage.open(serializer.file.name, 'rb')
        except Exception as e:
            return HttpResponseBadRequest(str(e))
        if file is None:
            raise Http404("File not found.")
        file_content = file.read()
        return Response(file_content, content_type="application/force_download")
    return HttpResponseBadRequest()
