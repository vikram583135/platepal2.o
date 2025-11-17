"""
Serializers for subscriptions app
"""
from rest_framework import serializers
from .models import MembershipPlan, Subscription


class MembershipPlanSerializer(serializers.ModelSerializer):
    """Membership plan serializer"""
    is_subscribed = serializers.SerializerMethodField()
    
    class Meta:
        model = MembershipPlan
        fields = ('id', 'name', 'plan_type', 'price', 'currency', 'benefits', 'description',
                  'is_active', 'is_featured', 'duration_days', 'is_subscribed', 'created_at')
        read_only_fields = ('id', 'created_at')
    
    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user,
                plan=obj,
                status=Subscription.Status.ACTIVE
            ).exists()
        return False


class SubscriptionSerializer(serializers.ModelSerializer):
    """Subscription serializer"""
    plan = MembershipPlanSerializer(read_only=True)
    plan_id = serializers.IntegerField(write_only=True, required=False)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = ('id', 'user', 'user_email', 'plan', 'plan_id', 'status', 'start_date',
                  'end_date', 'cancelled_at', 'payment_transaction_id', 'auto_renew',
                  'is_active', 'created_at')
        read_only_fields = ('id', 'user', 'status', 'start_date', 'end_date', 'cancelled_at',
                           'payment_transaction_id', 'created_at')
    
    def get_is_active(self, obj):
        return obj.is_active()
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

