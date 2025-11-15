from rest_framework import serializers
from .models import UploadedDataset

class UploadedDatasetSerializer(serializers.ModelSerializer):
    """
    Serializer for the UploadedDataset model.
    Exposes history data for the API.
    """
    # Read-only field to display the username instead of the user ID
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = UploadedDataset
        # Expose all fields to the API, making it easy to read the history
        fields = ['id', 'username', 'name', 'timestamp', 'summary_data', 'file_path']
        read_only_fields = ['id', 'timestamp', 'file_path', 'summary_data']