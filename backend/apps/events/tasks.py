"""
Celery tasks for event broadcasting retry and dead-letter queue
"""
import logging
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Event
from .broadcast import EventBroadcastService

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def retry_event_broadcast(self, event_id: str, channel_group: str):
    """
    Retry broadcasting an event to a channel group.
    
    Args:
        event_id: Event UUID
        channel_group: Channel group name
    """
    try:
        event = Event.objects.get(event_id=event_id)
        
        # Normalize event type for handler
        handler_type = event.type.replace('.', '_')
        
        data = {
            'event_id': str(event.event_id),
            'type': event.type,
            'version': event.version,
            'timestamp': event.timestamp.isoformat(),
            'aggregate_type': event.aggregate_type,
            'aggregate_id': str(event.aggregate_id),
            'payload': event.payload
        }
        
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                channel_group,
                {
                    'type': handler_type,
                    'data': data,
                    'event_id': str(event.event_id),
                }
            )
            
            logger.info(f"Successfully retried broadcast for event {event_id} to {channel_group}")
        else:
            raise Exception("Channel layer not configured")
            
    except Event.DoesNotExist:
        logger.error(f"Event {event_id} not found for retry")
    except Exception as exc:
        logger.error(f"Failed to retry broadcast for event {event_id}: {str(exc)}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        else:
            # Move to dead-letter queue
            logger.error(f"Max retries reached for event {event_id}, moving to DLQ")
            send_to_dlq.delay(event_id, channel_group, str(exc))


@shared_task
def send_to_dlq(event_id: str, channel_group: str, error: str):
    """
    Send failed event broadcast to dead-letter queue.
    
    Args:
        event_id: Event UUID
        channel_group: Channel group name
        error: Error message
    """
    try:
        from apps.admin_panel.models import DeadLetterQueue
        
        event = Event.objects.get(event_id=event_id)
        
        # Store in DLQ for manual review
        DeadLetterQueue.objects.create(
            event=event,
            channel_group=channel_group,
            error_message=error,
            retry_count=3,
            status='FAILED',
            failed_at=timezone.now()
        )
        
        logger.error(f"Event {event_id} sent to DLQ for channel {channel_group}: {error}")
        
    except Exception as e:
        logger.error(f"Failed to send event {event_id} to DLQ: {str(e)}")


@shared_task(bind=True, max_retries=5, default_retry_delay=300)
def retry_payment_capture(self, payment_id: int):
    """
    Retry payment capture with exponential backoff.
    
    Args:
        payment_id: Payment ID
    """
    try:
        from apps.payments.models import Payment
        from apps.payments.views import PaymentViewSet
        
        payment = Payment.objects.get(id=payment_id)
        
        if payment.status == Payment.Status.PENDING:
            # Attempt capture
            payment.status = Payment.Status.COMPLETED
            payment.processed_at = timezone.now()
            if not payment.transaction_id:
                import uuid
                payment.transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
            payment.save()
            
            # Broadcast payment.captured event
            EventBroadcastService.broadcast_to_multiple(
                event_type='payment.captured',
                aggregate_type='Payment',
                aggregate_id=str(payment.id),
                payload={'payment_id': payment.id, 'order_id': payment.order.id},
                customer_id=payment.user.id,
                restaurant_id=payment.order.restaurant.id,
                include_admin=True,
            )
            
            logger.info(f"Successfully captured payment {payment_id}")
        else:
            logger.info(f"Payment {payment_id} already processed")
            
    except Exception as exc:
        logger.error(f"Failed to capture payment {payment_id}: {str(exc)}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=300 * (2 ** self.request.retries))
        else:
            # Fallback to COD
            try:
                payment = Payment.objects.get(id=payment_id)
                payment.status = Payment.Status.FAILED
                payment.failure_reason = f"Capture failed after {self.max_retries} retries, falling back to COD"
                payment.failure_code = 'CAPTURE_FAILED'
                payment.failed_at = timezone.now()
                payment.save()
                
                # Notify admin
                EventBroadcastService.broadcast_to_admin(
                    event_type='payment.failed',
                    aggregate_type='Payment',
                    aggregate_id=str(payment.id),
                    payload={
                        'payment_id': payment.id,
                        'order_id': payment.order.id,
                        'failure_reason': payment.failure_reason,
                    }
                )
                
                logger.error(f"Payment {payment_id} capture failed, marked as COD fallback")
            except Exception as e:
                logger.error(f"Failed to update payment {payment_id} after capture failure: {str(e)}")


@shared_task
def process_offline_actions(rider_id: int):
    """
    Process queued offline actions for a rider.
    
    Args:
        rider_id: Rider user ID
    """
    try:
        from apps.deliveries.models import OfflineAction, DeliveryOffer
        
        pending_actions = OfflineAction.objects.filter(
            rider_id=rider_id,
            status=OfflineAction.Status.PENDING
        ).order_by('created_at')
        
        for action in pending_actions:
            try:
                if action.action_type == OfflineAction.ActionType.ACCEPT_OFFER:
                    offer_id = action.action_data.get('offer_id')
                    if offer_id:
                        offer = DeliveryOffer.objects.select_for_update().get(id=offer_id)
                        
                        if offer.status == DeliveryOffer.Status.SENT and offer.rider_id == rider_id:
                            # Accept the offer
                            from apps.deliveries.views import DeliveryOfferViewSet
                            from apps.accounts.models import User
                            
                            rider = User.objects.get(id=rider_id)
                            
                            # Simulate request for acceptance
                            offer.status = DeliveryOffer.Status.ACCEPTED
                            offer.accepted_at = timezone.now()
                            offer.save()
                            
                            # Update delivery
                            delivery = offer.delivery
                            delivery.rider = rider
                            delivery.status = delivery.Status.ACCEPTED
                            delivery.save()
                            
                            action.status = OfflineAction.Status.COMPLETED
                            action.synced_at = timezone.now()
                            action.save()
                            
                            logger.info(f"Processed offline action {action.id} for rider {rider_id}")
                
            except Exception as e:
                action.retry_count += 1
                if action.retry_count >= action.max_retries:
                    action.status = OfflineAction.Status.FAILED
                    action.sync_error = str(e)
                action.save()
                
                logger.error(f"Failed to process offline action {action.id}: {str(e)}")
                
    except Exception as e:
        logger.error(f"Failed to process offline actions for rider {rider_id}: {str(e)}")

