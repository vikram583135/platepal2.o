"""
Views for Event Store
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Q
from .models import Event
from .serializers import EventSerializer, EventReplaySerializer
from .services import EventService


class EventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for event store.
    Supports event replay and querying by aggregate or type.
    """
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Get events based on query parameters.
        Supports filtering by aggregate_type, aggregate_id, event_type, and since_event_id.
        """
        queryset = Event.objects.all()
        
        aggregate_type = self.request.query_params.get('aggregate_type')
        aggregate_id = self.request.query_params.get('aggregate_id')
        event_type = self.request.query_params.get('event_type')
        since_event_id = self.request.query_params.get('since_event_id')
        
        # Filter by aggregate
        if aggregate_type and aggregate_id:
            queryset = queryset.filter(
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id
            )
        elif aggregate_type:
            queryset = queryset.filter(aggregate_type=aggregate_type)
        
        # Filter by event type
        if event_type:
            queryset = queryset.filter(type=event_type)
        
        # Filter by since_event_id (for replay)
        if since_event_id:
            try:
                since_event = Event.objects.get(event_id=since_event_id)
                queryset = queryset.filter(sequence_number__gt=since_event.sequence_number)
            except Event.DoesNotExist:
                # If event not found, return empty queryset
                queryset = queryset.none()
        
        # Order by sequence number (for replay ordering)
        queryset = queryset.order_by('sequence_number')
        
        # Limit results (default 1000, max 10000)
        limit = int(self.request.query_params.get('limit', 1000))
        limit = min(limit, 10000)
        queryset = queryset[:limit]
        
        return queryset
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def replay(self, request):
        """
        Replay events since a specific event ID.
        
        Query params:
        - since_event_id: Event ID to start from (required)
        - limit: Maximum number of events (default 1000, max 10000)
        """
        serializer = EventReplaySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        since_event_id = serializer.validated_data.get('since_event_id')
        limit = serializer.validated_data.get('limit', 1000)
        
        if not since_event_id:
            return Response(
                {'error': 'since_event_id is required for replay'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        events = EventService.get_events_since(str(since_event_id), limit=limit)
        event_serializer = EventSerializer(events, many=True)
        
        return Response({
            'events': event_serializer.data,
            'count': len(events),
            'since_event_id': str(since_event_id)
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdminUser])
    def by_aggregate(self, request):
        """
        Get events for a specific aggregate.
        
        Query params:
        - aggregate_type: Type of aggregate (required)
        - aggregate_id: ID of aggregate (required)
        - since_event_id: Optional event ID to start from
        """
        aggregate_type = request.query_params.get('aggregate_type')
        aggregate_id = request.query_params.get('aggregate_id')
        since_event_id = request.query_params.get('since_event_id')
        
        if not aggregate_type or not aggregate_id:
            return Response(
                {'error': 'aggregate_type and aggregate_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        events = EventService.get_events_by_aggregate(
            aggregate_type,
            aggregate_id,
            since_event_id=since_event_id
        )
        event_serializer = EventSerializer(events, many=True)
        
        return Response({
            'events': event_serializer.data,
            'count': len(events),
            'aggregate_type': aggregate_type,
            'aggregate_id': aggregate_id
        })

