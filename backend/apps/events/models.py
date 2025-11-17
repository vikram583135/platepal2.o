"""
Event Store models for event sourcing
"""
import uuid
from django.db import models
from django.utils import timezone
from django.contrib.postgres.indexes import BTreeIndex, HashIndex


class Event(models.Model):
    """Event store for all domain events"""
    
    # Unique event identifier
    event_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    
    # Event type (e.g., 'order.created', 'payment.captured')
    type = models.CharField(max_length=100, db_index=True)
    
    # Version for schema evolution
    version = models.CharField(max_length=20, default='1.0')
    
    # Aggregate information
    aggregate_type = models.CharField(max_length=100, db_index=True)  # e.g., 'Order', 'Payment'
    aggregate_id = models.CharField(max_length=255, db_index=True)  # ID of the aggregate
    
    # Event payload (JSON)
    payload = models.JSONField(default=dict)
    
    # Metadata (user, IP, request ID, etc.)
    metadata = models.JSONField(default=dict)
    
    # Timestamp
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    # For replay ordering (monotonic sequence number)
    sequence_number = models.BigAutoField(primary_key=True)
    
    class Meta:
        db_table = 'events'
        ordering = ['sequence_number']
        indexes = [
            BTreeIndex(fields=['aggregate_type', 'aggregate_id', 'timestamp']),
            BTreeIndex(fields=['type', 'timestamp']),
            BTreeIndex(fields=['timestamp']),
            BTreeIndex(fields=['sequence_number']),
        ]
    
    def __str__(self):
        return f"{self.type} - {self.aggregate_type}:{self.aggregate_id}"

