from copy import deepcopy

from analyze.fitting.models import (
    Fit,
    FitParameter,
    #FitConstriant,
)
from analyze.models import (
    AnalysisBase,
    AnalysisParameterBase,
    #AnalysisConstraint,
)
from data.models import (
    Data,
)
from dj_rest_auth.serializers import UserDetailsSerializer
from django.contrib.auth.models import User

#from django.contrib.auth.models import Group, Permission
#from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from rest_framework.utils import model_meta

"""    read_only=False,
    queryset=Song.objects.all()
"""

class KnoxSerializer(serializers.Serializer):
    """
    Serializer for Knox authentication.
    """
    token = serializers.SerializerMethodField()
    user = UserDetailsSerializer()

    def get_token(self, obj):
      return obj["token"][1]


# Overriding validate to call model full_clean
class ModelSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        attributes_data = dict(attrs)
        ModelClass = self.Meta.model
        instance = deepcopy(self.instance) if self.instance else ModelClass()
        # Remove many-to-many relationships from attributes_data, so we can properly validate.
        info = model_meta.get_field_info(ModelClass)
        for field_name, relation_info in info.relations.items():
            if relation_info.to_many and (field_name in attributes_data):
                attributes_data.pop(field_name)
        for attr, value in attributes_data.items():
            setattr(instance, attr, value)
        self.full_clean(instance)
        return attrs

    def full_clean(self, instance, exclude=None, validate_unique=True):
        instance.full_clean(exclude, validate_unique)


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class DataSerializer(ModelSerializer):
    class Meta:
        model = Data
        fields = "__all__"


class AnalysisBaseSerializer(ModelSerializer):
    class Meta:
        model = AnalysisBase
        fields = "__all__"


class AnalysisParameterBaseSerializer(ModelSerializer):
    class Meta:
        model = AnalysisParameterBase
        fields = "__all__"


class FitSerializer(ModelSerializer):
    class Meta:
        model = Fit
        fields = "__all__"


class FitParameterSerializer(ModelSerializer):
    class Meta:
        model = FitParameter
        fields = "__all__"

"""class AnalysisConstraintSerializer(ModelSerializer):
    class Meta:
        model = AnalysisConstraint
        fields = "__all__"

class FitConstraintSerializer(ModelSerializer):
    class Meta:
        model = FitConstraint
        fields = "__all__"
"""
