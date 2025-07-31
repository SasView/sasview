from allauth.account import app_settings as allauth_settings
from allauth.account.utils import complete_signup
from dj_rest_auth.registration.views import RegisterView
from dj_rest_auth.views import LoginView
from knox.models import AuthToken
from rest_framework.response import Response
from serializers import KnoxSerializer


class KnoxLoginView(LoginView):

    def get_response(self):
        serializer_class = self.get_response_serializer()

        data = {
            'user': self.user,
            'token': self.token
        }
        serializer = serializer_class(instance=data, context={'request': self.request})

        return Response(serializer.data, status=200)

#do we want to use email?
class KnoxRegisterView(RegisterView):

    def get_response_data(self, user):
        return KnoxSerializer({'user': user, 'token': self.token}).data

    def perform_create(self, serializer):
        user = serializer.save(self.request)
        self.token = AuthToken.objects.create(user=user)
        complete_signup(self.request._request, user, allauth_settings.EMAIL_VERIFICATION, None)
        return user
