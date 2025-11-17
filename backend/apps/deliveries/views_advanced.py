"""
Advanced features views for deliveries app
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from apps.accounts.permissions import IsOwnerOrAdmin
from apps.accounts.models import User

try:
    from .models_advanced import (
        RiderAchievement, RiderLevel, MLETAPrediction,
        VoiceCommand, MultiTenantFleet, TenantRider
    )
    from .serializers_advanced import (
        RiderAchievementSerializer, RiderLevelSerializer, MLETAPredictionSerializer,
        VoiceCommandSerializer, MultiTenantFleetSerializer, TenantRiderSerializer
    )
    from .services_advanced import (
        check_and_award_achievements, add_points_to_rider,
        predict_ml_eta, process_voice_command, get_tenant_fleet_for_rider,
        get_rider_leaderboard
    )
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError:
    ADVANCED_FEATURES_AVAILABLE = False


if ADVANCED_FEATURES_AVAILABLE:
    class RiderAchievementViewSet(viewsets.ReadOnlyModelViewSet):
        """Rider achievement viewset"""
        serializer_class = RiderAchievementSerializer
        permission_classes = [IsAuthenticated]
        
        def get_queryset(self):
            user = self.request.user
            if user.role == 'ADMIN':
                return RiderAchievement.objects.all()
            return RiderAchievement.objects.filter(rider=user)
        
        @action(detail=False, methods=['get'])
        def my_achievements(self, request):
            """Get current rider's achievements"""
            achievements = RiderAchievement.objects.filter(
                rider=request.user
            ).order_by('-earned_at')
            serializer = self.get_serializer(achievements, many=True)
            return Response(serializer.data)
        
        @action(detail=False, methods=['get'])
        def leaderboard(self, request):
            """Get achievement leaderboard"""
            from django.db.models import Count
            leaderboard = User.objects.filter(
                role=User.Role.DELIVERY,
                achievements__isnull=False
            ).annotate(
                achievement_count=Count('achievements'),
                total_points=Sum('achievements__points_awarded')
            ).order_by('-total_points')[:10]
            
            data = []
            for rider in leaderboard:
                data.append({
                    'rider': rider.email,
                    'achievement_count': rider.achievement_count,
                    'total_points': rider.total_points or 0
                })
            
            return Response(data)
    
    
    class RiderLevelViewSet(viewsets.ReadOnlyModelViewSet):
        """Rider level viewset"""
        serializer_class = RiderLevelSerializer
        permission_classes = [IsAuthenticated]
        
        def get_queryset(self):
            user = self.request.user
            if user.role == 'ADMIN':
                return RiderLevel.objects.all()
            return RiderLevel.objects.filter(rider=user)
        
        @action(detail=False, methods=['get'])
        def my_level(self, request):
            """Get current rider's level"""
            level, created = RiderLevel.objects.get_or_create(
                rider=request.user,
                defaults={
                    'level': 1,
                    'total_points': 0,
                    'points_needed_for_next_level': 100
                }
            )
            serializer = self.get_serializer(level)
            return Response(serializer.data)
        
        @action(detail=False, methods=['get'])
        def leaderboard(self, request):
            """Get level leaderboard"""
            leaderboard = RiderLevel.objects.all().order_by(
                '-level', '-total_points'
            )[:10]
            serializer = self.get_serializer(leaderboard, many=True)
            return Response(serializer.data)
    
    
    class MLETAPredictionViewSet(viewsets.ReadOnlyModelViewSet):
        """ML ETA prediction viewset"""
        serializer_class = MLETAPredictionSerializer
        permission_classes = [IsAuthenticated]
        
        def get_queryset(self):
            user = self.request.user
            if user.role == 'ADMIN':
                return MLETAPrediction.objects.all()
            return MLETAPrediction.objects.filter(rider=user)
        
        @action(detail=False, methods=['post'])
        def predict(self, request):
            """Get ML-based ETA prediction for delivery"""
            from apps.deliveries.models import Delivery
            
            delivery_id = request.data.get('delivery_id')
            traffic_conditions = request.data.get('traffic_conditions', 'MEDIUM')
            weather_conditions = request.data.get('weather_conditions', 'CLEAR')
            
            if not delivery_id:
                return Response({'error': 'delivery_id is required'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            try:
                delivery = Delivery.objects.get(id=delivery_id, rider=request.user)
            except Delivery.DoesNotExist:
                return Response({'error': 'Delivery not found'}, 
                              status=status.HTTP_404_NOT_FOUND)
            
            prediction = predict_ml_eta(
                delivery=delivery,
                rider=request.user,
                traffic_conditions=traffic_conditions,
                weather_conditions=weather_conditions
            )
            
            if prediction:
                serializer = self.get_serializer(prediction)
                return Response(serializer.data)
            else:
                return Response({'error': 'Prediction not available'}, 
                              status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    
    class VoiceCommandViewSet(viewsets.ModelViewSet):
        """Voice command viewset"""
        serializer_class = VoiceCommandSerializer
        permission_classes = [IsAuthenticated]
        
        def get_queryset(self):
            user = self.request.user
            if user.role == 'ADMIN':
                return VoiceCommand.objects.all()
            return VoiceCommand.objects.filter(rider=user)
        
        @action(detail=False, methods=['post'])
        def process(self, request):
            """Process voice command"""
            spoken_text = request.data.get('spoken_text')
            recognized_text = request.data.get('recognized_text')
            command_type = request.data.get('command_type')
            delivery_id = request.data.get('delivery_id')
            
            if not spoken_text or not recognized_text or not command_type:
                return Response({'error': 'spoken_text, recognized_text, and command_type are required'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            delivery = None
            if delivery_id:
                from apps.deliveries.models import Delivery
                try:
                    delivery = Delivery.objects.get(id=delivery_id, rider=request.user)
                except Delivery.DoesNotExist:
                    return Response({'error': 'Delivery not found'}, 
                                  status=status.HTTP_404_NOT_FOUND)
            
            voice_cmd, result = process_voice_command(
                rider=request.user,
                spoken_text=spoken_text,
                recognized_text=recognized_text,
                command_type=command_type,
                delivery=delivery
            )
            
            serializer = self.get_serializer(voice_cmd)
            return Response({
                'voice_command': serializer.data,
                'result': result
            }, status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST)
    
    
    class MultiTenantFleetViewSet(viewsets.ModelViewSet):
        """Multi-tenant fleet viewset"""
        serializer_class = MultiTenantFleetSerializer
        permission_classes = [IsAuthenticated]
        
        def get_queryset(self):
            user = self.request.user
            if user.role == 'ADMIN':
                return MultiTenantFleet.objects.all()
            elif user.role == 'DELIVERY':
                # Get fleets where rider is a member
                tenant_riders = TenantRider.objects.filter(
                    rider=user,
                    is_active=True
                ).values_list('tenant_fleet_id', flat=True)
                return MultiTenantFleet.objects.filter(id__in=tenant_riders)
            return MultiTenantFleet.objects.none()
        
        @action(detail=False, methods=['get'])
        def my_fleet(self, request):
            """Get rider's tenant fleet"""
            fleet = get_tenant_fleet_for_rider(request.user)
            if fleet:
                serializer = self.get_serializer(fleet)
                return Response(serializer.data)
            return Response({'message': 'Not part of any tenant fleet'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        @action(detail=True, methods=['get'])
        def leaderboard(self, request, pk=None):
            """Get leaderboard for tenant fleet"""
            fleet = self.get_object()
            period = request.query_params.get('period', 'week')
            limit = int(request.query_params.get('limit', 10))
            
            leaderboard = get_rider_leaderboard(
                period=period,
                tenant_fleet=fleet,
                limit=limit
            )
            
            return Response({
                'fleet': fleet.name,
                'period': period,
                'leaderboard': leaderboard
            })
    
    
    class TenantRiderViewSet(viewsets.ModelViewSet):
        """Tenant rider viewset"""
        serializer_class = TenantRiderSerializer
        permission_classes = [IsAuthenticated]
        
        def get_queryset(self):
            user = self.request.user
            if user.role == 'ADMIN':
                return TenantRider.objects.all()
            elif user.role == 'DELIVERY':
                return TenantRider.objects.filter(rider=user)
            return TenantRider.objects.none()
        
        def perform_create(self, serializer):
            serializer.save(rider=self.request.user)

