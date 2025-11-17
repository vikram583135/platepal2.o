"""
WebSocket URL routing for PlatePal
"""
from django.urls import re_path
from channels.routing import URLRouter
from channels.auth import AuthMiddlewareStack

from websockets import consumers

websocket_urlpatterns = [
    re_path(r'ws/orders/(?P<restaurant_id>\d+)/$', consumers.RestaurantOrderConsumer.as_asgi()),
    re_path(r'ws/delivery/(?P<rider_id>\d+)/$', consumers.DeliveryConsumer.as_asgi()),
    re_path(r'ws/customer/(?P<customer_id>\d+)/$', consumers.CustomerConsumer.as_asgi()),
    re_path(r'ws/admin/$', consumers.AdminConsumer.as_asgi()),
    re_path(r'ws/chat/(?P<room_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
]

