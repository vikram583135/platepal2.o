"""
Views for support app
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from .models import SupportTicket, TicketMessage, ChatBotMessage
from .serializers import SupportTicketSerializer, TicketMessageSerializer, ChatBotMessageSerializer
from apps.accounts.permissions import IsOwnerOrAdmin


class SupportTicketViewSet(viewsets.ModelViewSet):
    """Support ticket viewset"""
    serializer_class = SupportTicketSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return SupportTicket.objects.filter(is_deleted=False)
        return SupportTicket.objects.filter(user=user, is_deleted=False)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_message(self, request, pk=None):
        """Add message to ticket"""
        ticket = self.get_object()
        
        # Check permission
        if ticket.user != request.user and request.user.role != 'ADMIN':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        message_text = request.data.get('message', '').strip()
        if not message_text:
            return Response({'error': 'Message is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        message = TicketMessage.objects.create(
            ticket=ticket,
            user=request.user,
            message=message_text,
            is_internal=request.data.get('is_internal', False) and request.user.role == 'ADMIN'
        )
        
        # Update ticket status if customer replies
        if ticket.user == request.user and ticket.status == SupportTicket.Status.RESOLVED:
            ticket.status = SupportTicket.Status.OPEN
            ticket.save()
        
        serializer = TicketMessageSerializer(message, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def resolve(self, request, pk=None):
        """Resolve ticket (admin only)"""
        if request.user.role != 'ADMIN':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        ticket = self.get_object()
        ticket.status = SupportTicket.Status.RESOLVED
        ticket.resolved_at = timezone.now()
        ticket.resolved_by = request.user
        ticket.save()
        
        serializer = self.get_serializer(ticket)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def close(self, request, pk=None):
        """Close ticket"""
        ticket = self.get_object()
        
        # Customer or admin can close
        if ticket.user != request.user and request.user.role != 'ADMIN':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        ticket.status = SupportTicket.Status.CLOSED
        ticket.save()
        
        serializer = self.get_serializer(ticket)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def chatbot_message(request):
    """Handle chatbot messages"""
    message = request.data.get('message', '').strip()
    session_id = request.data.get('session_id', '')
    
    if not message:
        return Response({'error': 'Message is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Generate session ID if not provided
    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())
    
    user = request.user if request.user.is_authenticated else None
    
    # Save user message
    user_msg = ChatBotMessage.objects.create(
        user=user,
        session_id=session_id,
        message=message,
        is_from_user=True
    )
    
    # Simple rule-based chatbot (in production, use NLP/ML)
    response_text = "Thank you for contacting PlatePal support. How can I help you today?"
    intent = 'greeting'
    
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['order', 'track', 'delivery']):
        response_text = "I can help you with your order. Please provide your order number, or I can show you your recent orders."
        intent = 'order_inquiry'
    elif any(word in message_lower for word in ['refund', 'cancel', 'money']):
        response_text = "I can help you with refunds. Please provide your order number or ticket number for faster assistance."
        intent = 'refund_inquiry'
    elif any(word in message_lower for word in ['payment', 'card', 'upi', 'wallet']):
        response_text = "I can help you with payment issues. Please provide your transaction ID or order number."
        intent = 'payment_inquiry'
    elif any(word in message_lower for word in ['account', 'login', 'password', 'profile']):
        response_text = "I can help you with account issues. Please visit Settings > Profile to manage your account, or create a support ticket for assistance."
        intent = 'account_inquiry'
    elif any(word in message_lower for word in ['help', 'support', 'contact']):
        response_text = "I'm here to help! You can ask me about orders, payments, refunds, or account issues. Or create a support ticket for detailed assistance."
        intent = 'help_request'
    
    # Save bot response
    bot_msg = ChatBotMessage.objects.create(
        user=user,
        session_id=session_id,
        message=response_text,
        is_from_user=False,
        intent=intent,
        confidence=0.8
    )
    
    return Response({
        'session_id': session_id,
        'response': response_text,
        'intent': intent,
        'user_message': ChatBotMessageSerializer(user_msg).data,
        'bot_message': ChatBotMessageSerializer(bot_msg).data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chatbot_history(request):
    """Get chatbot conversation history"""
    session_id = request.query_params.get('session_id')
    
    if session_id:
        messages = ChatBotMessage.objects.filter(session_id=session_id).order_by('created_at')
    else:
        messages = ChatBotMessage.objects.filter(user=request.user).order_by('created_at')[:50]
    
    serializer = ChatBotMessageSerializer(messages, many=True)
    return Response({'messages': serializer.data})

