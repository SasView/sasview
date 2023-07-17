from copy import deepcopy

#from django.contrib.auth.models import Group, Permission
#from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers, validators
from rest_framework.fields import CharField, ChoiceField, DateTimeField, DecimalField, IntegerField
from rest_framework.utils import model_meta
from django.contrib.auth.models import User

from data.models import (
    Data,
)
from analyze.models import (
    AnalysisBase,
    AnalysisParameterBase,
)
from analyze.fitting.models import (
    Fit,
    FitParameter,
)

"""    read_only=False,
    queryset=Song.objects.all()
"""

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
        fields = "__all__", 

    def full_clean(self, instance, exclude=None, validate_unique=True):
        if not instance or not instance.id:
            exclude = ["user"]
        super().full_clean(instance, exclude, validate_unique)


    def create(self, validated_data):
        instance: self.Meta.model = super().create(validated_data)
        return instance
    
class RegisterSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "password", "email", "first_name", "last_name") 
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {
                "required": True,
                "allow_blank": False,
                "validators": [
                    validators.UniqueValidator(
                        User.objects.all(), f"A user with that Email already exists."
                    )
                ],
            },
        }
        
    def create(self, validated_data):
        instance: self.Meta.model = super().create(validated_data)
        return instance

class DataSerializer(ModelSerializer):
    class Meta:
        model = Data
        fields = "__all__", 

    def full_clean(self, instance, exclude=None, validate_unique=True):
        if not instance or not instance.id:
            exclude = ["current_user"]
        super().full_clean(instance, exclude, validate_unique)


    def create(self, validated_data):
        instance: self.Meta.model = super().create(validated_data)
        instance.current_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True)
        return instance
    
class AnalysisBaseSerializer(ModelSerializer):
    class Meta:
        model = AnalysisBase
        fields = "__all__"

    def full_clean(self, instance, exclude=None, validate_unique=True):
        if not instance or not instance.id:
            exclude = ["current_user", "data_id"]
        super().full_clean(instance, exclude, validate_unique)


    def create(self, validated_data):
        instance: self.Meta.model = super().create(validated_data)
        instance.current_user = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.all(), many=True)
        instance.data_id = serializers.PrimaryKeyRelatedField(queryset=Data.objects.all(), many=True)
        return instance

class AnalysisParameterBaseSerializer(ModelSerializer):
    class Meta:
        model = AnalysisParameterBase
        fields = "__all__"

    def full_clean(self, instance, exclude=None, validate_unique=True):
        if not instance or not instance.id:
            exclude = ["model_id"]
        super().full_clean(instance, exclude, validate_unique)


    def create(self, validated_data):
        instance: self.Meta.model = super().create(validated_data)
        return instance

class FitSerializer(AnalysisBaseSerializer):
    analysis_base = AnalysisBaseSerializer(many = True, read_only=True)

    class Meta:
        model = Fit
        fields = "__all__", "analysis_base"

class FitParameterSerializer(AnalysisParameterBaseSerializer):
    analysis_parameter = AnalysisParameterBaseSerializer(many = True, read_only=True)

    class Meta:
        model = FitParameter
        fields = "__all__", "analysis_parameter"

    def create(self, validated_data):
        instance: FitParameter = super().create(validated_data)
        return instance