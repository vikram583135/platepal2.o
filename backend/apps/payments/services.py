"""
Payment and Settlement Services
"""
import logging
from typing import Optional, List
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Payment, Refund, SettlementCycle, Payout
from apps.orders.models import Order
from apps.events.broadcast import EventBroadcastService

logger = logging.getLogger(__name__)


class SettlementService:
    """Service for processing settlement cycles and payouts"""
    
    @staticmethod
    @transaction.atomic
    def create_settlement_cycle(restaurant_id: int, cycle_start, cycle_end) -> SettlementCycle:
        """
        Create a settlement cycle for a restaurant
        
        Args:
            restaurant_id: Restaurant ID
            cycle_start: Start datetime of cycle
            cycle_end: End datetime of cycle
        
        Returns:
            SettlementCycle object
        """
        from apps.restaurants.models import Restaurant
        
        restaurant = Restaurant.objects.get(id=restaurant_id)
        
        # Get all completed orders in cycle
        orders = Order.objects.filter(
            restaurant=restaurant,
            status=Order.Status.DELIVERED,
            delivered_at__gte=cycle_start,
            delivered_at__lt=cycle_end,
            payment__status=Payment.Status.COMPLETED
        ).select_related('payment')
        
        # Calculate totals
        total_sales = sum(order.total_amount for order in orders)
        commission_rate = Decimal('0.15')  # 15% commission (configurable)
        commission_amount = total_sales * commission_rate
        packaging_fee = Decimal('2.00') * orders.count()  # $2 per order
        delivery_fee_share = Decimal('1.00') * orders.count()  # $1 per order
        tax_rate = Decimal('0.10')  # 10% tax
        tax_amount = total_sales * tax_rate
        
        net_payout = total_sales - commission_amount - packaging_fee - delivery_fee_share - tax_amount
        
        # Create settlement cycle
        settlement = SettlementCycle.objects.create(
            restaurant=restaurant,
            cycle_start=cycle_start,
            cycle_end=cycle_end,
            total_sales=total_sales,
            commission_amount=commission_amount,
            packaging_fee=packaging_fee,
            delivery_fee_share=delivery_fee_share,
            tax_amount=tax_amount,
            net_payout=net_payout,
            status=SettlementCycle.Status.PENDING,
        )
        
        logger.info(f"Created settlement cycle {settlement.id} for restaurant {restaurant_id}")
        return settlement
    
    @staticmethod
    @transaction.atomic
    def execute_payout(settlement_id: int) -> Optional[Payout]:
        """
        Execute payout for a settlement cycle
        
        Args:
            settlement_id: SettlementCycle ID
        
        Returns:
            Payout object if successful, None otherwise
        """
        settlement = SettlementCycle.objects.get(id=settlement_id)
        
        if settlement.status != SettlementCycle.Status.PENDING:
            logger.warning(f"Settlement {settlement_id} already processed")
            return None
        
        # Get restaurant bank details
        from apps.deliveries.models import RiderBankDetail
        bank_detail = RiderBankDetail.objects.filter(
            rider=settlement.restaurant.owner,
            is_verified=True
        ).first()
        
        if not bank_detail:
            logger.error(f"No verified bank details for restaurant {settlement.restaurant.id}")
            settlement.status = SettlementCycle.Status.FAILED
            settlement.notes = "No verified bank details found"
            settlement.save()
            return None
        
        # Create payout
        payout = Payout.objects.create(
            settlement=settlement,
            restaurant=settlement.restaurant,
            amount=settlement.net_payout,
            bank_account_number=bank_detail.account_number,
            bank_ifsc_code=bank_detail.ifsc_code,
            bank_name=bank_detail.bank_name,
            account_holder_name=bank_detail.account_holder_name,
            status=Payout.Status.PENDING,
        )
        
        # Mark settlement as processing
        settlement.status = SettlementCycle.Status.PROCESSING
        settlement.save()
        
        # Initiate payout (mock - in production, integrate with payment gateway)
        try:
            payout.status = Payout.Status.INITIATED
            payout.initiated_at = timezone.now()
            payout.utr_number = f"UTR{timezone.now().strftime('%Y%m%d')}{payout.id:06d}"
            payout.save()
            
            # Mock gateway processing - in production, call actual gateway
            payout.status = Payout.Status.PROCESSING
            payout.save()
            
            # Simulate successful payout
            payout.status = Payout.Status.COMPLETED
            payout.processed_at = timezone.now()
            payout.save()
            
            settlement.status = SettlementCycle.Status.COMPLETED
            settlement.processed_at = timezone.now()
            settlement.payout_reference = payout.utr_number
            settlement.save()
            
            # Broadcast payout.completed event
            EventBroadcastService.broadcast_to_restaurant(
                restaurant_id=settlement.restaurant.id,
                event_type='payout.completed',
                aggregate_type='Payout',
                aggregate_id=str(payout.id),
                payload={
                    'payout_id': payout.id,
                    'settlement_id': settlement.id,
                    'amount': float(payout.amount),
                    'utr_number': payout.utr_number,
                }
            )
            
            EventBroadcastService.broadcast_to_admin(
                event_type='payout.completed',
                aggregate_type='Payout',
                aggregate_id=str(payout.id),
                payload={
                    'payout_id': payout.id,
                    'restaurant_id': settlement.restaurant.id,
                    'amount': float(payout.amount),
                }
            )
            
            logger.info(f"Payout {payout.id} completed successfully")
            return payout
            
        except Exception as e:
            # Handle failed payout
            payout.status = Payout.Status.FAILED
            payout.failure_reason = str(e)
            payout.save()
            
            settlement.status = SettlementCycle.Status.FAILED
            settlement.notes = f"Payout failed: {str(e)}"
            settlement.save()
            
            # Broadcast payout.failed event
            EventBroadcastService.broadcast_to_admin(
                event_type='payout.failed',
                aggregate_type='Payout',
                aggregate_id=str(payout.id),
                payload={
                    'payout_id': payout.id,
                    'settlement_id': settlement.id,
                    'restaurant_id': settlement.restaurant.id,
                    'failure_reason': str(e),
                }
            )
            
            logger.error(f"Payout {payout.id} failed: {str(e)}")
            return payout
    
    @staticmethod
    def retry_failed_payout(payout_id: int) -> bool:
        """
        Retry a failed payout
        
        Args:
            payout_id: Payout ID
        
        Returns:
            True if retry initiated, False otherwise
        """
        payout = Payout.objects.get(id=payout_id)
        
        if payout.status != Payout.Status.FAILED:
            return False
        
        # Reset payout status and retry
        payout.status = Payout.Status.PENDING
        payout.failure_reason = ''
        payout.save()
        
        # Retry payout
        return SettlementService.execute_payout(payout.settlement.id) is not None

