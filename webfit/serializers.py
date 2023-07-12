from copy import deepcopy

#from django.contrib.auth.models import Group, Permission
#from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from rest_framework.fields import CharField, ChoiceField, DateTimeField, DecimalField, IntegerField
from rest_framework.utils import model_meta

from data.models import (
    Data,
)
from user_app.models import (
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

class DataSerializers(ModelSerializer):
    class Meta:
        model = Data
        fields = "__all__", 

    def full_clean(self, instance, exclude=None, validate_unique=True):
        if not instance or not instance.id:
            exclude = ["current_user"]
        super().full_clean(instance, exclude, validate_unique)


    def create(self, validated_data):
        instance: Data = super().create(validated_data)
        instance.current_user = serializers.PrimaryKeyRelatedField(many=True, read_only=False, queryset = AnalysisModelBase.objects.all())
        return instance
    
class AnalysisBaseSerializers(ModelSerializer):
    class Meta:
        model = AnalysisBase
        fields = "__all__"

    def full_clean(self, instance, exclude=None, validate_unique=True):
        if not instance or not instance.id:
            exclude = ["current_user", "data_id", "model_id"]
        super().full_clean(instance, exclude, validate_unique)


    def create(self, validated_data):
        instance: AnalysisBase = super().create(validated_data)
        instance.current_user = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
        instance.data_id = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
        instance.model_id = serializers.PrimaryKeyRelatedField(many=True, read_only=False, queryset = AnalysisModelBase.objects.all())
        return instance
    
class AnalysisModelBaseSerializers(ModelSerializer):
    class Meta:
        model = AnalysisModelBase
        fields = "__all__"

class AnalysisParameterBaseSerializers(ModelSerializer):
    class Meta:
        model = AnalysisParameterBase
        fields = "__all__"

    def full_clean(self, instance, exclude=None, validate_unique=True):
        if not instance or not instance.id:
            exclude = ["model_id"]
        super().full_clean(instance, exclude, validate_unique)


    def create(self, validated_data):
        instance: AnalysisModelBase = super().create(validated_data)
        instance.model_id = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
        return instance

class FitSerializers(AnalysisBaseSerializers):
    class Meta:
        model = Fit
        fields = "__all__"

class FitModelSerializers(AnalysisModelBaseSerializers):
    class Meta:
        model = FitModel
        fields = "__all__"

class FitParameterSerializers(AnalysisParameterBaseSerializers):
    class Meta:
        model = FitParameter
        fields = "__all__"