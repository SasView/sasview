from django.test import TestCase
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework.test import APIRequestFactory, APIClient, force_authenticate
from rest_framework.authtoken.models import Token

from .models import Data
from .views import (
    list_data,
    data_info,
    upload,
    download
)


# Create your tests here.
class DataTest(TestCase):
    def setUp(self):
        public_test_data = Data.objects.create(id = 1, file = "cyl_400_20.txt", is_public = True)
        self.user = User.objects.create_user(username="testUser", password="secret", id = 2)
        private_test_data = Data.objects.create(id = 3, current_user = self.user, file = "another.txt", is_public = False)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    #working
    def does_list_public(self):
        request = self.client.get('/v1/data/list/')
        self.assertEqual(request.data, {"public_file_ids":1})

    #working
    def does_list_user(self):
        request = self.client.get('/v1/data/list/testUser/', user = self.user)
        self.assertEqual(request.data, {"public_file_ids":1, "user_data_ids":3})

    #check if this is what we want
    def does_load_data_info_public(self):
        request = self.client.get('/v1/data/load/1/')
        self.assertEqual(request.data, {"info":"cyl_400_20.txt"})

    #check if this is what we want
    def does_load_data_info_private(self):
        request = self.client.get('/v1/data/load/3/')
        self.assertEqual(request.data, {"info":"another.txt"})

    def is_data_being_created(self):
        file = ...
        request = self.client.post('/v1/data/upload/', file=file)
        new_data_bd = Data.objects.get(file = file)
        self.assertEqual(new_data_bd.id, 3)

    def does_file_upload(self):
        file = ...
        request = self.client.post('/v1/data/upload/', file=file)
        new_data_bd = Data.objects.get(file = file)
        self.assertEqual(new_data_bd.file, file)

    def does_file_upload_update(self):
        file = ...
        request = self.client.put('/v1/data/upload/3/', file = file)
        new_data_bd = Data.objects.get(file = file)
        self.assertEqual(new_data_bd.file, file)

    def does_download(self):
        self.client.get()

    def download_gives_file(self):
        self.client.get()
