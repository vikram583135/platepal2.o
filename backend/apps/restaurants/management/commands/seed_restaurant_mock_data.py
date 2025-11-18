"""
Management command to seed mock data for all restaurants
Includes: orders, reviews, inventory items, and promotions
"""
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.restaurants.models import (
    Restaurant,
    MenuItem,
    Promotion,
    RestaurantSettings,
    RestaurantAlert,
)
from apps.orders.models import Order, OrderItem, Review
from apps.inventory.models import InventoryItem
from apps.accounts.models import Address
from apps.payments.models import Payment

User = get_user_model()

# Sample customer names for mock data
CUSTOMER_NAMES = [
    'Rajesh Kumar', 'Priya Sharma', 'Amit Patel', 'Sneha Reddy', 'Vikram Singh',
    'Anjali Mehta', 'Rahul Gupta', 'Kavita Nair', 'Suresh Iyer', 'Divya Joshi',
    'Mohammed Ali', 'Sunita Das', 'Arjun Malhotra', 'Meera Krishnan', 'Karan Kapoor',
]

# Sample review comments
REVIEW_COMMENTS = [
    'Great food and fast delivery!',
    'Amazing taste, will order again.',
    'Good quality but delivery was a bit slow.',
    'Excellent service and delicious food.',
    'Not bad, but could be better.',
    'Best restaurant in the area!',
    'Food was cold when it arrived.',
    'Perfect! Exactly as ordered.',
    'Good value for money.',
    'Highly recommended!',
]

# Sample inventory item names by category
INVENTORY_ITEMS = {
    'Vegetables': ['Tomatoes', 'Onions', 'Potatoes', 'Bell Peppers', 'Carrots', 'Cabbage', 'Cauliflower'],
    'Dairy': ['Milk', 'Cheese', 'Butter', 'Yogurt', 'Cream'],
    'Meat': ['Chicken', 'Mutton', 'Fish', 'Prawns'],
    'Spices': ['Turmeric', 'Cumin', 'Coriander', 'Garam Masala', 'Red Chili Powder'],
    'Grains': ['Rice', 'Wheat Flour', 'Basmati Rice'],
    'Beverages': ['Soft Drinks', 'Juice', 'Water'],
    'Other': ['Oil', 'Salt', 'Sugar', 'Flour', 'Bread'],
}


class Command(BaseCommand):
    help = 'Seed mock data (orders, reviews, inventory, promotions) for all restaurants'

    def add_arguments(self, parser):
        parser.add_argument(
            '--restaurant-id',
            type=int,
            help='Seed data for a specific restaurant ID only',
        )

    def handle(self, *args, **options):
        self.stdout.write('Starting mock data seeding...')
        
        restaurants = Restaurant.objects.filter(
            is_deleted=False,
            status=Restaurant.Status.ACTIVE
        )
        
        if options['restaurant_id']:
            restaurants = restaurants.filter(id=options['restaurant_id'])
        
        total_restaurants = restaurants.count()
        self.stdout.write(f'Found {total_restaurants} restaurants to seed')
        
        for idx, restaurant in enumerate(restaurants, 1):
            self.stdout.write(f'\n[{idx}/{total_restaurants}] Processing {restaurant.name}...')
            
            # Ensure settings exist
            settings, _ = RestaurantSettings.objects.get_or_create(restaurant=restaurant)
            
            # Get menu items
            menu_items = MenuItem.objects.filter(
                category__menu__restaurant=restaurant,
                category__menu__is_active=True,
                category__menu__is_deleted=False,
                is_deleted=False
            ).select_related('category', 'category__menu')
            
            if not menu_items.exists():
                self.stdout.write(self.style.WARNING(f'  No menu items found for {restaurant.name}, skipping...'))
                continue
            
            # Seed orders
            self._seed_orders(restaurant, menu_items)
            
            # Seed reviews
            self._seed_reviews(restaurant)
            
            # Seed inventory
            self._seed_inventory(restaurant, menu_items)
            
            # Seed promotions
            self._seed_promotions(restaurant)
            
            # Seed payments for completed orders
            self._seed_payments(restaurant)
            
            # Seed alerts
            self._seed_alerts(restaurant)
        
        self.stdout.write(self.style.SUCCESS('\n[SUCCESS] Mock data seeding completed!'))

    def _seed_orders(self, restaurant, menu_items):
        """Seed orders with various statuses"""
        menu_items_list = list(menu_items)
        if not menu_items_list:
            return
        
        # Get or create a test customer
        customer, _ = User.objects.get_or_create(
            email='testcustomer@platepal.com',
            defaults={
                'first_name': 'Test',
                'last_name': 'Customer',
                'role': User.Role.CUSTOMER,
                'is_email_verified': True,
            }
        )
        
        # Create delivery address if needed
        address, _ = Address.objects.get_or_create(
            user=customer,
            label='Default',
            defaults={
                'street': '123 Test Street',
                'city': restaurant.city,
                'state': restaurant.state,
                'postal_code': restaurant.postal_code,
                'country': restaurant.country or 'India',
                'latitude': restaurant.latitude,
                'longitude': restaurant.longitude,
                'is_default': True,
            }
        )
        
        orders_created = 0
        
        # Recent orders (last 7 days) - 20-30 orders
        for i in range(random.randint(20, 30)):
            days_ago = random.randint(0, 7)
            created_at = timezone.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
            
            # Random status distribution
            status_weights = {
                Order.Status.DELIVERED: 0.5,
                Order.Status.CANCELLED: 0.1,
                Order.Status.ACCEPTED: 0.1,
                Order.Status.PREPARING: 0.1,
                Order.Status.READY: 0.05,
                Order.Status.OUT_FOR_DELIVERY: 0.1,
                Order.Status.PENDING: 0.05,
            }
            status = random.choices(list(status_weights.keys()), weights=list(status_weights.values()))[0]
            
            order = self._create_order(restaurant, customer, address, menu_items_list, status, created_at)
            if order:
                orders_created += 1
        
        # Historical orders (last 30 days) - 50-100 completed orders
        for i in range(random.randint(50, 100)):
            days_ago = random.randint(8, 30)
            created_at = timezone.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
            
            order = self._create_order(restaurant, customer, address, menu_items_list, Order.Status.DELIVERED, created_at)
            if order:
                orders_created += 1
        
        # Ongoing orders - 3-5 active orders
        ongoing_statuses = [
            Order.Status.ACCEPTED,
            Order.Status.PREPARING,
            Order.Status.READY,
            Order.Status.ASSIGNED,
            Order.Status.OUT_FOR_DELIVERY,
        ]
        for i in range(random.randint(3, 5)):
            hours_ago = random.randint(0, 2)
            created_at = timezone.now() - timedelta(hours=hours_ago, minutes=random.randint(0, 59))
            status = random.choice(ongoing_statuses)
            
            order = self._create_order(restaurant, customer, address, menu_items_list, status, created_at)
            if order:
                orders_created += 1
        
        self.stdout.write(f'  [OK] Created {orders_created} orders')

    def _create_order(self, restaurant, customer, address, menu_items_list, status, created_at):
        """Create a single order with items"""
        try:
            # Generate unique order number with timestamp and random
            timestamp = int(timezone.now().timestamp() * 1000) % 100000
            random_part = random.randint(1000, 9999)
            order_number = f"ORD-{timezone.now().strftime('%Y%m%d')}-{timestamp}{random_part}"
            
            # Ensure uniqueness
            max_attempts = 10
            for attempt in range(max_attempts):
                if not Order.objects.filter(order_number=order_number).exists():
                    break
                timestamp = int(timezone.now().timestamp() * 1000) % 100000
                random_part = random.randint(1000, 9999)
                order_number = f"ORD-{timezone.now().strftime('%Y%m%d')}-{timestamp}{random_part}"
            
            # Select random menu items (1-5 items)
            selected_items = random.sample(menu_items_list, min(random.randint(1, 5), len(menu_items_list)))
            
            # Calculate subtotal
            subtotal = Decimal('0.00')
            order_items_data = []
            
            for menu_item in selected_items:
                quantity = random.randint(1, 3)
                unit_price = menu_item.price
                
                # Add some modifiers randomly
                selected_modifiers = []
                if menu_item.modifiers.filter(is_available=True).exists():
                    modifiers = list(menu_item.modifiers.filter(is_available=True)[:random.randint(0, 2)])
                    for mod in modifiers:
                        selected_modifiers.append({
                            'modifier_id': mod.id,
                            'name': mod.name,
                            'price': float(mod.price),
                        })
                
                item_total = unit_price * quantity
                if selected_modifiers:
                    modifier_total = sum(Decimal(str(m['price'])) for m in selected_modifiers)
                    item_total += modifier_total * quantity
                
                subtotal += item_total
                
                order_items_data.append({
                    'menu_item': menu_item,
                    'name': menu_item.name,
                    'description': menu_item.description,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'selected_modifiers': selected_modifiers,
                })
            
            # Calculate fees
            tax_amount = subtotal * Decimal('0.05')  # 5% tax
            delivery_fee = restaurant.delivery_fee or Decimal('45.00')
            discount_amount = Decimal('0.00')
            
            # Apply random promotion sometimes
            promotion = None
            if random.random() < 0.3:  # 30% chance
                active_promos = Promotion.objects.filter(
                    restaurant=restaurant,
                    is_active=True,
                    valid_from__lte=timezone.now(),
                    valid_until__gte=timezone.now(),
                    is_deleted=False
                )
                if active_promos.exists():
                    promotion = random.choice(list(active_promos))
                    if promotion.discount_type == Promotion.DiscountType.PERCENTAGE:
                        discount_amount = subtotal * (Decimal(str(promotion.discount_value)) / Decimal('100'))
                        if promotion.maximum_discount:
                            discount_amount = min(discount_amount, Decimal(str(promotion.maximum_discount)))
                    elif promotion.discount_type == Promotion.DiscountType.FIXED:
                        discount_amount = Decimal(str(promotion.discount_value))
                    elif promotion.discount_type == Promotion.DiscountType.FREE_DELIVERY:
                        discount_amount = delivery_fee
            
            total_amount = subtotal + tax_amount + delivery_fee - discount_amount
            
            # Create order
            order = Order.objects.create(
                customer=customer,
                restaurant=restaurant,
                delivery_address=address,
                order_number=order_number,
                status=status,
                order_type=random.choice([Order.OrderType.DELIVERY, Order.OrderType.PICKUP]),
                priority_tag=random.choice([Order.PriorityTag.NORMAL, Order.PriorityTag.NORMAL, Order.PriorityTag.RUSH]),
                subtotal=subtotal,
                tax_amount=tax_amount,
                delivery_fee=delivery_fee,
                discount_amount=discount_amount,
                total_amount=total_amount,
                promotion=promotion,
                promo_code=promotion.code if promotion else '',
                estimated_preparation_time=restaurant.delivery_time_minutes or 30,
                special_instructions=random.choice(['', '', 'Please make it spicy', 'Less spicy please', 'Extra napkins']),
                created_at=created_at,
            )
            
            # Set status timestamps
            if status in [Order.Status.ACCEPTED, Order.Status.PREPARING, Order.Status.READY, 
                         Order.Status.ASSIGNED, Order.Status.PICKED_UP, Order.Status.OUT_FOR_DELIVERY, Order.Status.DELIVERED]:
                order.accepted_at = created_at + timedelta(minutes=random.randint(1, 5))
            
            if status in [Order.Status.PREPARING, Order.Status.READY, Order.Status.ASSIGNED, 
                         Order.Status.PICKED_UP, Order.Status.OUT_FOR_DELIVERY, Order.Status.DELIVERED]:
                order.preparing_at = order.accepted_at + timedelta(minutes=random.randint(1, 3))
            
            if status in [Order.Status.READY, Order.Status.ASSIGNED, Order.Status.PICKED_UP, 
                         Order.Status.OUT_FOR_DELIVERY, Order.Status.DELIVERED]:
                order.ready_at = order.preparing_at + timedelta(minutes=random.randint(10, 25))
            
            if status == Order.Status.DELIVERED:
                order.delivered_at = order.ready_at + timedelta(minutes=random.randint(15, 45))
                order.actual_delivery_time = order.delivered_at
            
            if status == Order.Status.CANCELLED:
                order.cancelled_at = created_at + timedelta(minutes=random.randint(1, 10))
                order.cancellation_reason = random.choice([
                    'Customer cancelled',
                    'Restaurant unable to fulfill',
                    'Out of stock',
                ])
            
            order.save()
            
            # Create order items
            for item_data in order_items_data:
                OrderItem.objects.create(
                    order=order,
                    menu_item=item_data['menu_item'],
                    name=item_data['name'],
                    description=item_data['description'],
                    quantity=item_data['quantity'],
                    unit_price=item_data['unit_price'],
                    selected_modifiers=item_data['selected_modifiers'],
                )
            
            return order
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Error creating order: {str(e)}'))
            return None

    def _seed_reviews(self, restaurant):
        """Seed reviews for completed orders"""
        completed_orders = Order.objects.filter(
            restaurant=restaurant,
            status=Order.Status.DELIVERED,
            is_deleted=False
        ).exclude(review__isnull=False)  # Exclude orders that already have reviews
        
        orders_to_review = list(completed_orders[:random.randint(10, 20)])
        reviews_created = 0
        
        for order in orders_to_review:
            try:
                rating = random.choices(
                    [3, 4, 5],  # Bias towards positive ratings
                    weights=[0.1, 0.2, 0.7]
                )[0]
                
                food_rating = Decimal(str(random.uniform(3.5, 5.0)))
                delivery_rating = Decimal(str(random.uniform(3.0, 5.0)))
                
                comment = random.choice(REVIEW_COMMENTS) if random.random() < 0.8 else ''
                
                # Some reviews have restaurant replies
                restaurant_reply = ''
                restaurant_replied_at = None
                if random.random() < 0.4:  # 40% have replies
                    restaurant_reply = random.choice([
                        'Thank you for your feedback!',
                        'We appreciate your review!',
                        'Thanks for ordering with us!',
                        'Glad you enjoyed!',
                    ])
                    restaurant_replied_at = order.delivered_at + timedelta(days=random.randint(1, 3))
                
                Review.objects.create(
                    order=order,
                    customer=order.customer,
                    restaurant=restaurant,
                    restaurant_rating=rating,
                    food_rating=food_rating,
                    delivery_rating=delivery_rating,
                    comment=comment,
                    is_approved=True,
                    restaurant_reply=restaurant_reply,
                    restaurant_replied_at=restaurant_replied_at,
                    created_at=order.delivered_at + timedelta(hours=random.randint(1, 48)),
                )
                reviews_created += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error creating review: {str(e)}'))
        
        self.stdout.write(f'  [OK] Created {reviews_created} reviews')

    def _seed_inventory(self, restaurant, menu_items):
        """Seed inventory items"""
        inventory_created = 0
        
        # Create inventory items for different categories
        for category, items in INVENTORY_ITEMS.items():
            for item_name in random.sample(items, min(random.randint(2, len(items)), len(items))):
                try:
                    # Try to link to a menu item if possible
                    linked_menu_item = None
                    if menu_items.exists():
                        # Try to find a menu item with similar name
                        for menu_item in menu_items:
                            if item_name.lower() in menu_item.name.lower() or menu_item.name.lower() in item_name.lower():
                                linked_menu_item = menu_item
                                break
                        if not linked_menu_item:
                            linked_menu_item = random.choice(list(menu_items))
                    
                    # Set stock levels
                    max_stock = random.randint(50, 200)
                    current_stock = random.randint(0, max_stock)
                    low_threshold = max_stock * Decimal('0.2')  # 20% of max
                    
                    unit = random.choice([
                        InventoryItem.Unit.KILOGRAM,
                        InventoryItem.Unit.GRAM,
                        InventoryItem.Unit.PIECE,
                        InventoryItem.Unit.PACK,
                    ])
                    
                    InventoryItem.objects.get_or_create(
                        restaurant=restaurant,
                        name=item_name,
                        defaults={
                            'menu_item': linked_menu_item,
                            'category': category,
                            'unit': unit,
                            'current_stock': Decimal(str(current_stock)),
                            'reorder_level': Decimal(str(low_threshold)),
                            'max_capacity': Decimal(str(max_stock)),
                            'low_stock_threshold': Decimal(str(low_threshold)),
                            'auto_mark_unavailable': True,
                            'last_restocked_at': timezone.now() - timedelta(days=random.randint(0, 7)),
                        }
                    )
                    inventory_created += 1
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  Error creating inventory item: {str(e)}'))
        
        self.stdout.write(f'  [OK] Created {inventory_created} inventory items')

    def _seed_promotions(self, restaurant):
        """Seed promotions"""
        existing_promos = Promotion.objects.filter(restaurant=restaurant, is_deleted=False).count()
        if existing_promos >= 5:
            self.stdout.write(f'  ✓ Already has {existing_promos} promotions')
            return
        
        promotions_created = 0
        promo_types = [
            (Promotion.DiscountType.PERCENTAGE, 10, 20, 30),
            (Promotion.DiscountType.FIXED, 50, 100, 200),
            (Promotion.DiscountType.FREE_DELIVERY, 0, 0, 0),
        ]
        
        for i in range(random.randint(3, 5)):
            try:
                discount_type, *discount_values = random.choice(promo_types)
                discount_value = random.choice(discount_values) if discount_values else 0
                
                # Date ranges
                valid_from = timezone.now() - timedelta(days=random.randint(0, 7))
                valid_until = timezone.now() + timedelta(days=random.randint(7, 30))
                
                # Some promotions have codes (must be unique)
                code = ''
                if random.random() < 0.6:  # 60% have codes
                    # Generate unique code
                    max_attempts = 10
                    for attempt in range(max_attempts):
                        potential_code = f"{restaurant.name.upper().replace(' ', '')[:5]}{random.randint(1000, 9999)}"
                        if not Promotion.objects.filter(code=potential_code).exists():
                            code = potential_code
                            break
                    # If couldn't generate unique code, skip this promotion
                    if not code or code == '':
                        continue
                
                name = random.choice([
                    f'{discount_value}% Off',
                    'Special Offer',
                    'Weekend Special',
                    'Happy Hours',
                    'Flash Sale',
                ])
                
                Promotion.objects.get_or_create(
                    restaurant=restaurant,
                    name=name,
                    defaults={
                        'description': f'Special promotion for {restaurant.name}',
                        'discount_type': discount_type,
                        'discount_value': discount_value,
                        'minimum_order_amount': Decimal(str(random.choice([0, 299, 499, 799]))),
                        'maximum_discount': Decimal(str(random.choice([0, 100, 200]))) if discount_type == Promotion.DiscountType.PERCENTAGE else None,
                        'valid_from': valid_from,
                        'valid_until': valid_until,
                        'code': code,
                        'max_uses': random.choice([None, 100, 500, 1000]),
                        'max_uses_per_user': random.randint(1, 3),
                        'is_active': random.random() < 0.8,  # 80% active
                        'offer_type': Promotion.OfferType.RESTAURANT,
                    }
                )
                promotions_created += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error creating promotion: {str(e)}'))
        
        self.stdout.write(f'  [OK] Created {promotions_created} promotions')

    def _seed_payments(self, restaurant):
        """Seed payments for delivered orders"""
        delivered_orders = Order.objects.filter(
            restaurant=restaurant,
            status=Order.Status.DELIVERED,
            is_deleted=False
        ).exclude(payment__isnull=False)  # Exclude orders that already have payments
        
        orders_to_pay = list(delivered_orders[:random.randint(30, 50)])
        payments_created = 0
        
        for order in orders_to_pay:
            try:
                # Random payment method
                method_type = random.choice([
                    Payment.PaymentMethodType.CARD,
                    Payment.PaymentMethodType.UPI,
                    Payment.PaymentMethodType.WALLET,
                    Payment.PaymentMethodType.CASH,
                ])
                
                # Generate unique transaction ID
                transaction_id = f"TXN{order.id}{random.randint(100000, 999999)}"
                
                # Most payments are completed, some might be pending/processing
                status_weights = {
                    Payment.Status.COMPLETED: 0.85,
                    Payment.Status.PROCESSING: 0.1,
                    Payment.Status.PENDING: 0.05,
                }
                status = random.choices(list(status_weights.keys()), weights=list(status_weights.values()))[0]
                
                # Set processed_at for completed payments
                processed_at = None
                if status == Payment.Status.COMPLETED:
                    # Processed within 1-5 minutes of order creation
                    processed_at = order.created_at + timedelta(minutes=random.randint(1, 5))
                
                Payment.objects.create(
                    order=order,
                    user=order.customer,
                    method_type=method_type,
                    amount=order.total_amount,
                    currency='INR',
                    transaction_id=transaction_id,
                    status=status,
                    processed_at=processed_at,
                    gateway_response={
                        'gateway': 'mock_gateway',
                        'payment_id': transaction_id,
                        'status': 'success' if status == Payment.Status.COMPLETED else 'pending',
                    },
                    created_at=order.created_at,
                )
                payments_created += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error creating payment: {str(e)}'))
        
        self.stdout.write(f'  [OK] Created {payments_created} payments')

    def _seed_alerts(self, restaurant):
        """Seed restaurant alerts"""
        existing_alerts = RestaurantAlert.objects.filter(restaurant=restaurant, is_deleted=False).count()
        if existing_alerts >= 10:
            self.stdout.write(f'  ✓ Already has {existing_alerts} alerts')
            return
        
        alerts_created = 0
        
        # Get some orders for order-related alerts
        orders = list(Order.objects.filter(restaurant=restaurant, is_deleted=False)[:5])
        
        # Alert templates
        alert_templates = [
            {
                'alert_type': RestaurantAlert.AlertType.INVENTORY_LOW,
                'severity': RestaurantAlert.Severity.WARNING,
                'titles': [
                    'Low Stock Alert',
                    'Inventory Running Low',
                    'Restock Required',
                ],
                'messages': [
                    'Some items are running low on stock. Please restock soon.',
                    'Inventory levels are below threshold for multiple items.',
                    'Consider restocking to avoid running out.',
                ],
            },
            {
                'alert_type': RestaurantAlert.AlertType.NEW_REVIEW,
                'severity': RestaurantAlert.Severity.INFO,
                'titles': [
                    'New Customer Review',
                    'Review Received',
                    'Customer Feedback',
                ],
                'messages': [
                    'You have received a new review from a customer.',
                    'A customer has left feedback on their recent order.',
                    'New review available for viewing.',
                ],
            },
            {
                'alert_type': RestaurantAlert.AlertType.SLA_BREACH,
                'severity': RestaurantAlert.Severity.CRITICAL,
                'titles': [
                    'SLA Breach Warning',
                    'Order Taking Too Long',
                    'Delivery Time Exceeded',
                ],
                'messages': [
                    'An order is taking longer than expected. Please expedite.',
                    'Order preparation time has exceeded SLA threshold.',
                    'Urgent: Order delivery time is at risk.',
                ],
            },
            {
                'alert_type': RestaurantAlert.AlertType.PAYOUT,
                'severity': RestaurantAlert.Severity.INFO,
                'titles': [
                    'Payout Processed',
                    'Payment Received',
                    'Settlement Complete',
                ],
                'messages': [
                    'Your weekly payout has been processed successfully.',
                    'Payment for recent orders has been transferred.',
                    'Settlement cycle completed. Check your account.',
                ],
            },
            {
                'alert_type': RestaurantAlert.AlertType.SYSTEM,
                'severity': RestaurantAlert.Severity.INFO,
                'titles': [
                    'System Update',
                    'Maintenance Notice',
                    'Feature Available',
                ],
                'messages': [
                    'New features are now available in your dashboard.',
                    'System maintenance scheduled for tonight.',
                    'Update: New menu management tools available.',
                ],
            },
        ]
        
        # Create 5-10 alerts
        for i in range(random.randint(5, 10)):
            try:
                template = random.choice(alert_templates)
                order = random.choice(orders) if orders and random.random() < 0.3 else None
                
                # Some alerts are read, some are unread
                is_read = random.random() < 0.4  # 40% are read
                read_at = timezone.now() - timedelta(hours=random.randint(1, 24)) if is_read else None
                
                # Some alerts are resolved
                resolved_at = None
                if is_read and random.random() < 0.3:  # 30% of read alerts are resolved
                    resolved_at = read_at + timedelta(minutes=random.randint(10, 60))
                
                # Random creation time (last 7 days)
                created_at = timezone.now() - timedelta(
                    days=random.randint(0, 7),
                    hours=random.randint(0, 23)
                )
                
                RestaurantAlert.objects.create(
                    restaurant=restaurant,
                    order=order,
                    alert_type=template['alert_type'],
                    severity=template['severity'],
                    title=random.choice(template['titles']),
                    message=random.choice(template['messages']),
                    is_read=is_read,
                    read_at=read_at,
                    resolved_at=resolved_at,
                    metadata={
                        'source': 'system',
                        'auto_generated': True,
                    },
                    created_at=created_at,
                )
                alerts_created += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error creating alert: {str(e)}'))
        
        self.stdout.write(f'  [OK] Created {alerts_created} alerts')

