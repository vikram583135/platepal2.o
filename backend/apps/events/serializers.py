"""
Serializers for Event Store
"""
from rest_framework import serializers
from .models import Event


class EventSerializer(serializers.ModelSerializer):
    """Serializer for Event model"""
    
    class Meta:
        model = Event
        fields = [
            'event_id',
            'type',
            'version',
            'aggregate_type',
            'aggregate_id',
            'payload',
            'metadata',
            'timestamp',
            'sequence_number'
        ]
        read_only_fields = ['event_id', 'timestamp', 'sequence_number']


class EventReplaySerializer(serializers.Serializer):
    """Serializer for event replay requests"""
    since_event_id = serializers.UUIDField(required=False, allow_null=True)
    aggregate_type = serializers.CharField(required=False, allow_blank=True)
    aggregate_id = serializers.CharField(required=False, allow_blank=True)
    event_type = serializers.CharField(required=False, allow_blank=True)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=10000, default=1000)

