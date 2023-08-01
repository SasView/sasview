import os
import shutil

from django.conf import settings
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.test import APIRequestFactory, APIClient, force_authenticate, APITestCase
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
    def test_does_list_public(self):
        request = self.client.get('/v1/data/list/')
        self.assertEqual(request.data, {"public_file_ids":1})

    #working
    def test_does_list_user(self):
        request = self.client.get('/v1/data/list/testUser/', user = self.user)
        self.assertEqual(request.data, {"public_file_ids":1, "user_data_ids":3})

    #add that the data_info is getting data info after loading
    """
    loader()...
    """
    def test_does_load_data_info_public(self):
        request = self.client.get('/v1/data/load/1/')
        self.assertEqual(request.data, {"info":"cyl_400_20.txt"})

    #check if this is what we want
    def test_does_load_data_info_private(self):
        request = self.client.get('/v1/data/load/3/')
        self.assertEqual(request.data, {"info":"another.txt"})


class TestingDatabase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testUser", password="secret", id = 2)
        self.data = Data.objects.create(id = 1, current_user = self.user, file_name = "another.txt", is_public = False)
        self.data.file.save("another.txt",open(r"C:\Users\tns14\Documents\another.txt"))
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.client2 = APIClient()

    def test_is_data_being_created(self):
        file = open(r"C:\Users\tns14\Documents\testing.txt")
        data = {
            "is_public":False,
            "file":file
        }
        request = self.client.post('/v1/data/upload/', data=data)
        self.assertEqual(request.status_code, status.HTTP_200_OK)
        self.assertEqual(request.data, {"current_user":2, "authenticated" : True, "file_id" : 1, "file_alternative_name":"testing.txt","is_public" : False})

    def test_is_data_being_created_no_user(self):
        file = open(r"C:\Users\tns14\Documents\testing.txt")
        data = {
            "is_public":False,
            "file":file
        }
        request = self.client2.post('/v1/data/upload/', data=data)
        self.assertEqual(request.status_code, status.HTTP_200_OK)
        self.assertEqual(request.data, {"current_user":None, "authenticated" : False, "file_id" : 1, "file_alternative_name":"testing.txt","is_public" : False})

    def test_does_file_upload(self):
        file = open(r"C:\Users\tns14\Documents\testing.txt")
        data = {
            "is_public":False,
            "file":file
        }
        request = self.client.post('/v1/data/upload/', data = data)
        new_data_bd = Data.objects.get(current_user = 2)
        self.assertEqual(os.path.basename(new_data_bd.file.path), os.path.basename(r"C:\Users\tns14\Documents\testing.txt"))

    def test_does_file_upload_update(self):
        file = open(r"C:\Users\tns14\Documents\testing.txt")
        data = {
            "file":file,
            "is_public":False
        }
        request = self.client.put('/v1/data/upload/1/', data = data)
        request2 = self.client2.put('/v1/data/upload/1/', data = data)
        self.assertEqual(request.data, {"current_user":2, "authenticated" : True, "file_id" : 1, "file_alternative_name":"testing.txt","is_public" : False})
        self.assertEqual(request2.status_code, status.HTTP_403_FORBIDDEN)

    def test_does_download(self):
        self.client.get()

    def test_download_gives_file(self):
        self.client.get()

    def tearDown(self):
        shutil.rmtree(settings.MEDIA_ROOT)
