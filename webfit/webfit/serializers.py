from rest_framework import serializers
from data.models import Data

class DataSerializers(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(required=False, allow_blank=True, max_length=100)
    code = serializers.CharField(style={'base_template': 'textarea.html'})
    linenos = serializers.BooleanField(required=False)
    language = serializers.ChoiceField(choices=LANGUAGE_CHOICES, default='python')
    style = serializers.ChoiceField(choices=STYLE_CHOICES, default='friendly')

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
        instance.save()
        return instance