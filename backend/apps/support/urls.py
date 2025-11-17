"""
URLs for support app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SupportTicketViewSet, chatbot_message, chatbot_history

router = DefaultRouter()
router.register(r'tickets', SupportTicketViewSet, basename='ticket')

urlpatterns = [
    path('', include(router.urls)),
    path('chatbot/message/', chatbot_message, name='chatbot_message'),
    path('chatbot/history/', chatbot_history, name='chatbot_history'),
]

