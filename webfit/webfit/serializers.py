from copy import deepcopy

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from rest_framework.fields import CharField, ChoiceField, DateTimeField, DecimalField, IntegerField
from rest_framework.utils import model_meta

from data.models import (
    Data,
)
from user_authentication.models import (
    User
)
from analyze.models import (
    AnalysisBase,
    AnalysisModelBase,
    AnalysisParameterBase,
)
from analyze.fitting.models import (
    Fit,
    FitModel,
    FitParameter,
)


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

class DataSerializers(ModelSerializer):
    class Meta:
	    model = Data
	    fields = "__all__"
	    
    def full_clean(self, instance, exclude=None, validate_unique=True):
	    if not instance or not instance.id:
		    exclude = []
	    super().full_clean(instance, exclude, validate_unique)
	    

    def create(self, validated_data):
		instance: User = super().create(validated_data)
		instance.get_preferences()
		return instance
