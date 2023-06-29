from rest_framework import serializers
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

class DataSerializers(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    user_id = serializers.ForeignKey
    file_string = serializers.CharField(required=True, allow_blank=False, max_length=200)
    data = serializers.BinaryField
    saved_file_string = serializers.CharField(required=True, allow_blank=False, max_length=200)
    opt_in = serializers.BooleanField(required=False)
    import_example_data = serializers.ChoiceField(default = 'python')
    analysis = serializers.ForeignKey

    def create(self, validated_data):
        """
        Create and return a new `Data` instance, given the validated data.
        """
        return Data.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `Data` instance, given the validated data.
        """
        instance.id = validated_data.get('id', instance.id)
        instance.user_id = validated_data.get('user id', instance.user_id)
        instance.file_string = validated_data.get('file string location', instance.file_string)
        instance.data = validated_data.get('data', instance.data)
        instance.saved_file_string = validated_data.get('style', instance.style)
        instance.opt_in = validated_data.get('opt in', instance.opt_in)
        instance.import_example_data = validated_data.get('example data', instance.import_example_data)
        instance.analysis = validated_data.get('analysis', instance.analysis)
        instance.save()
        return instance