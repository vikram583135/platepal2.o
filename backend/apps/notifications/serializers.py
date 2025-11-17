"""
Serializers for notifications app
"""
from rest_framework import serializers
from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    """Notification serializer"""
    icon = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = ('id', 'type', 'title', 'message', 'data', 'is_read', 'read_at',
                  'sent_via_email', 'sent_via_sms', 'sent_via_push', 'created_at', 'icon')
        read_only_fields = ('id', 'created_at')
    
    def get_icon(self, obj):
        """Return icon name based on notification type"""
        icon_map = {
            'ORDER_PLACED': 'package',
            'ORDER_ACCEPTED': 'check-circle',
            'ORDER_READY': 'utensils',
            'ORDER_OUT_FOR_DELIVERY': 'truck',
            'ORDER_DELIVERED': 'check-circle-2',
            'ORDER_CANCELLED': 'x-circle',
            'PAYMENT_SUCCESS': 'credit-card',
            'PAYMENT_FAILED': 'alert-circle',
            'PROMOTION': 'tag',
            'REVIEW_REQUEST': 'star',
            'SYSTEM': 'bell',
        }
        return icon_map.get(obj.type, 'bell')


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Notification preference serializer"""
    
    class Meta:
        model = NotificationPreference
        fields = ('id', 'email_order_updates', 'email_promotions', 'email_payment_updates',
                  'email_review_requests', 'email_system_notifications',
                  'sms_order_updates', 'sms_promotions', 'sms_payment_updates',
                  'push_order_updates', 'push_promotions', 'push_payment_updates',
                  'push_review_requests', 'push_system_notifications',
                  'quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end')
        read_only_fields = ('id',)

