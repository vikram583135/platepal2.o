"""
URLs for chat app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatRoomViewSet, ChatMessageViewSet, ChatTemplateViewSet, MaskedCallViewSet

router = DefaultRouter()
router.register(r'rooms', ChatRoomViewSet, basename='chat-room')
router.register(r'messages', ChatMessageViewSet, basename='chat-message')
router.register(r'templates', ChatTemplateViewSet, basename='chat-template')
router.register(r'masked-calls', MaskedCallViewSet, basename='masked-call')

urlpatterns = [
    path('', include(router.urls)),
]

