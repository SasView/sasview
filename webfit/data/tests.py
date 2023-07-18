from django.test import TestCase
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework.test import APIRequestFactory

from .models import Data
from .views import (
    list_data,
    data_info,
    upload,
    download
)

factory = APIRequestFactory()

# Create your tests here.
class DataTest(TestCase):
    def setUp(self):
        test_user = User.objects.create(username = "testUser", email = "123@gmail.com")
        Data.objects.create(current_user = test_user.username)

    def is_data_being_created(self):
        factory.post()

    def does_list(self):
        factory.get()

    def does_get_data_info(self):
        factory.get()

    def does_file_upload(self):
        factory.post()

    def does_file_upload(self):
        factory.put()

    def does_upload_create_new_database(self):
        factory.post()

    def does_download(self):
        factory.get()

    def download_gives_file(self):
        factory.get()
