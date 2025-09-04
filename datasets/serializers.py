from rest_framework import serializers
from .models import Dataset

class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = ['id', 'name', 'csv_file', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']
