"""
Seed data command for development
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from apps.restaurants.models import (
    Restaurant,
    Menu,
    MenuCategory,
    MenuItem,
    ItemModifier,
    RestaurantSettings,
    RestaurantBranch,
    ManagerProfile,
    Promotion
)
from apps.accounts.models import Address, PaymentMethod, SavedLocation
from apps.payments.models import Wallet, WalletTransaction, Payment
from apps.subscriptions.models import MembershipPlan, Subscription
from apps.rewards.models import LoyaltyTier, UserLoyalty, RewardPoint
from apps.support.models import SupportTicket
from apps.orders.models import Order
from apps.deliveries.models import (
    RiderProfile, RiderWallet, RiderShift, Delivery, DeliveryOffer, RiderEarnings,
    RiderBankDetail, RiderWalletTransaction
)
from apps.admin_panel.models import (
    Role, Permission, AdminUser, AuditLogEntry
)
from apps.admin_panel.models_operations import (
    SystemHealthMetric, Incident, MaintenanceWindow
)
from apps.admin_panel.models_advanced import (
    FeatureFlag, FraudDetectionRule, FraudFlag, Chargeback
)
from apps.admin_panel.models_automation import (
    AutomationRule, ScheduledJob, Webhook
)
from apps.inventory.models import InventoryItem, StockMovement
from apps.orders.models import Order, OrderItem, Review, ItemReview
from apps.payments.models import SettlementCycle, Payout

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database with sample data'
    
    def _ensure_restaurant_owner(self, email, first_name, last_name, password, phone=None):
        owner, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'phone': phone or '',
                'role': User.Role.RESTAURANT,
                'is_email_verified': True
            }
        )
        if created:
            owner.set_password(password)
            owner.save()
            self.stdout.write(f'Created restaurant owner: {owner.email}')
        else:
            # Update phone if not set
            if not owner.phone and phone:
                owner.phone = phone
                owner.save()
            self.stdout.write(f'Restaurant owner already exists: {owner.email}')
        return owner
    
    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')
        
        # Create or get users
        admin, admin_created = User.objects.get_or_create(
            email='admin@platepal.com',
            defaults={
                'first_name': 'Admin',
                'last_name': 'User',
                'phone': '+91 98765 00001',
                'role': User.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'is_email_verified': True
            }
        )
        if admin_created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(f'Created admin: {admin.email}')
        else:
            # Update phone if not set
            if not admin.phone:
                admin.phone = '+91 98765 00001'
                admin.save()
            self.stdout.write(f'Admin already exists: {admin.email}')
        
        customer, customer_created = User.objects.get_or_create(
            email='customer@platepal.com',
            defaults={
                'first_name': 'John',
                'last_name': 'Doe',
                'phone': '+91 98765 10000',
                'role': User.Role.CUSTOMER,
                'is_email_verified': True
            }
        )
        if customer_created:
            customer.set_password('customer123')
            customer.save()
            self.stdout.write(f'Created customer: {customer.email}')
        else:
            # Update phone if not set
            if not customer.phone:
                customer.phone = '+91 98765 10000'
                customer.save()
            self.stdout.write(f'Customer already exists: {customer.email}')
        
        restaurant_owner = self._ensure_restaurant_owner(
            email='restaurant@platepal.com',
            first_name='Riya',
            last_name='Sethi',
            password='restaurant123',
            phone='+91 98765 43210'
        )
        mumbai_owner = self._ensure_restaurant_owner(
            email='mumbai@platepal.com',
            first_name='Ananya',
            last_name='Iyer',
            password='masala123',
            phone='+91 98201 22334'
        )
        sakura_owner = self._ensure_restaurant_owner(
            email='sakura@platepal.com',
            first_name='Haruto',
            last_name='Sato',
            password='sakura123',
            phone='+91 98765 11223'
        )
        thai_owner = self._ensure_restaurant_owner(
            email='thai@platepal.com',
            first_name='Siri',
            last_name='Wong',
            password='thai123',
            phone='+91 98765 33445'
        )
        bangalore_owner = self._ensure_restaurant_owner(
            email='bangalore@platepal.com',
            first_name='Aarav',
            last_name='Iyengar',
            password='bangalore123',
            phone='+91 99000 11121'
        )
        whitefield_owner = self._ensure_restaurant_owner(
            email='whitefield@platepal.com',
            first_name='Sahana',
            last_name='Prakash',
            password='white123',
            phone='+91 99880 55667'
        )
        koramangala_owner = self._ensure_restaurant_owner(
            email='koramangala@platepal.com',
            first_name='Neha',
            last_name='Rao',
            password='bangalore123',
            phone='+91 99000 11221'
        )
        indiranagar_owner = self._ensure_restaurant_owner(
            email='indiranagar@platepal.com',
            first_name='Varun',
            last_name='Iyer',
            password='indira123',
            phone='+91 98450 99887'
        )
        
        rider, rider_created = User.objects.get_or_create(
            email='rider@platepal.com',
            defaults={
                'first_name': 'Delivery',
                'last_name': 'Rider',
                'phone': '+91 98765 20000',
                'role': User.Role.DELIVERY,
                'is_email_verified': True
            }
        )
        if rider_created:
            rider.set_password('rider123')
            rider.save()
            self.stdout.write(f'Created rider: {rider.email}')
        else:
            # Update phone if not set
            if not rider.phone:
                rider.phone = '+91 98765 20000'
                rider.save()
            self.stdout.write(f'Rider already exists: {rider.email}')
        
        # Create or get address for customer (Mumbai location to match restaurants)
        address, address_created = Address.objects.get_or_create(
            user=customer,
            label='Home',
            defaults={
                'street': '123 Marine Drive',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'postal_code': '400020',
                'country': 'India',
                'latitude': Decimal('18.9400'),
                'longitude': Decimal('72.8300'),
                'is_default': True
            }
        )
        if address_created:
            self.stdout.write(f'Created address for customer')
        else:
            self.stdout.write(f'Address already exists for customer')
        
        # Create or get saved locations for customer
        saved_location_home, home_created = SavedLocation.objects.get_or_create(
            user=customer,
            label='Home',
            defaults={
                'address': '123 Marine Drive, Mumbai, Maharashtra 400020, India',
                'latitude': Decimal('18.9400'),
                'longitude': Decimal('72.8300'),
                'is_default': True
            }
        )
        
        saved_location_work, work_created = SavedLocation.objects.get_or_create(
            user=customer,
            label='Work',
            defaults={
                'address': '45 Bandra Kurla Complex, Mumbai, Maharashtra 400051, India',
                'latitude': Decimal('19.0759'),
                'longitude': Decimal('72.8776'),
                'is_default': False
            }
        )
        
        if home_created:
            self.stdout.write(f'Created saved location: Home')
        if work_created:
            self.stdout.write(f'Created saved location: Work')
        
        # Create or get payment method
        payment_method, payment_created = PaymentMethod.objects.get_or_create(
            user=customer,
            provider='Visa',
            last_four='4242',
            defaults={
                'type': PaymentMethod.PaymentMethodType.CARD,
                'is_default': True
            }
        )
        if payment_created:
            self.stdout.write(f'Created payment method for customer')
        else:
            self.stdout.write(f'Payment method already exists for customer')
        
        # Create additional payment methods for better testing
        upi_payment, upi_created = PaymentMethod.objects.get_or_create(
            user=customer,
            provider='Google Pay',
            last_four='1234',
            defaults={
                'type': PaymentMethod.PaymentMethodType.UPI,
                'is_default': False
            }
        )
        if upi_created:
            self.stdout.write(f'Created UPI payment method for customer')
        
        # Seed restaurants with rich menus
        restaurants_seed_data = [
            {
                'owner': restaurant_owner,
                'restaurant': {
                    'name': 'Pizza Palace Mumbai',
                    'description': 'Neapolitan-style pizzas baked in stone ovens with local ingredients.',
                    'cuisine_type': Restaurant.CuisineType.ITALIAN,
                    'phone': '+91 98765 43210',
                    'email': 'hello@mumbaipizzapalace.in',
                    'latitude': Decimal('19.0880'),
                    'longitude': Decimal('72.8260'),
                    'address': '12 Colaba Causeway',
                    'city': 'Mumbai',
                    'state': 'Maharashtra',
                    'postal_code': '400001',
                    'country': 'India',
                    'status': Restaurant.Status.ACTIVE,
                    'rating': Decimal('4.6'),
                    'total_ratings': 248,
                    'delivery_time_minutes': 32,
                    'minimum_order_amount': Decimal('499.00'),
                    'delivery_fee': Decimal('45.00'),
                    'opening_hours': {
                        'monday': {'open': '11:00', 'close': '23:00'},
                        'tuesday': {'open': '11:00', 'close': '23:00'},
                        'wednesday': {'open': '11:00', 'close': '23:00'},
                        'thursday': {'open': '11:00', 'close': '23:30'},
                        'friday': {'open': '11:00', 'close': '00:00'},
                        'saturday': {'open': '12:00', 'close': '00:00'},
                        'sunday': {'open': '12:00', 'close': '23:00'},
                    },
                    'accepts_delivery': True,
                    'accepts_pickup': True,
                    'kyc_verified': True,
                    'logo_image_url': 'https://images.unsplash.com/photo-1478144592103-25e218a04891?auto=format&fit=crop&w=200&q=80',
                    'hero_image_url': 'https://images.unsplash.com/photo-1548365328-76bc3997d9ea?auto=format&fit=crop&w=900&q=80',
                },
                'menu': {
                    'name': 'Mumbai Main Menu',
                    'description': 'Stone-baked pizzas, antipasti and desserts',
                    'categories': [
                        {
                            'name': 'Wood-fired Pizzas',
                            'description': 'Hand stretched sourdough bases baked at 480°C.',
                            'display_order': 1,
                            'items': [
                                {
                                    'name': 'Truffle Burrata Pizza',
                                    'description': 'Cherry tomatoes, basil oil, fresh burrata and black truffle butter finish.',
                                    'price': Decimal('749.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1604382354932-07c5d9983bd3?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 18,
                                    'modifiers': [
                                        {'name': 'Extra Buffalo Mozzarella', 'type': ItemModifier.ModifierType.ADDON, 'price': Decimal('79.00')},
                                        {'name': 'Gluten-free Crust', 'type': ItemModifier.ModifierType.VARIANT, 'price': Decimal('59.00')}
                                    ]
                                },
                                {
                                    'name': 'Smoked Chicken Supreme',
                                    'description': 'Smoked chicken, pickled onions, mascarpone and chilli oil drizzle.',
                                    'price': Decimal('799.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1542281286-9e0a16bb7366?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 20,
                                    'is_spicy': True
                                },
                                {
                                    'name': 'Paneer Tikka Inferno',
                                    'description': 'Tandoori paneer, charred peppers, smoked paprika honey.',
                                    'price': Decimal('699.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'is_spicy': True
                                },
                                {
                                    'name': 'Classic Margherita',
                                    'description': 'San Marzano tomatoes, fresh mozzarella, basil leaves, extra virgin olive oil.',
                                    'price': Decimal('599.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1574071318508-1cdbab80d002?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 15
                                },
                                {
                                    'name': 'Pepperoni Deluxe',
                                    'description': 'Spicy pepperoni, mozzarella, oregano, red pepper flakes.',
                                    'price': Decimal('759.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1628840042765-356cda07504e?auto=format&fit=crop&w=600&q=80',
                                    'is_spicy': True,
                                    'preparation_time_minutes': 17
                                },
                                {
                                    'name': 'Quattro Formaggi',
                                    'description': 'Four cheese blend of gorgonzola, mozzarella, parmesan, and fontina.',
                                    'price': Decimal('779.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1571997478779-2adcbbe9ab2f?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 18
                                },
                                {
                                    'name': 'Veggie Supreme',
                                    'description': 'Bell peppers, mushrooms, olives, onions, jalapeños, mozzarella.',
                                    'price': Decimal('729.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1573821663912-6df460e5b2d4?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'is_spicy': True,
                                    'preparation_time_minutes': 16
                                },
                            ]
                        },
                        {
                            'name': 'Antipasti & Small Plates',
                            'description': 'Warm starters and sharing boards.',
                            'display_order': 2,
                            'items': [
                                {
                                    'name': 'Garlic Focaccia Pull-aparts',
                                    'description': 'Parmesan crust, chilli butter pot and marinara dip.',
                                    'price': Decimal('349.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1525755662778-989d0524087e?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True
                                },
                                {
                                    'name': 'Heritage Tomato Burrata',
                                    'description': 'Slow-roasted tomatoes, micro basil, pistachio pesto.',
                                    'price': Decimal('399.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True
                                },
                                {
                                    'name': 'Bruschetta Trio',
                                    'description': 'Classic tomato basil, ricotta honey, and mushroom truffle bruschetta.',
                                    'price': Decimal('379.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1572441713132-51c75654db73?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 10
                                },
                                {
                                    'name': 'Caprese Salad',
                                    'description': 'Fresh buffalo mozzarella, heirloom tomatoes, basil, balsamic reduction.',
                                    'price': Decimal('429.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 8
                                },
                                {
                                    'name': 'Arancini Balls',
                                    'description': 'Crispy risotto balls stuffed with mozzarella, served with marinara sauce.',
                                    'price': Decimal('359.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1611676279444-5577698aa13c?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 12
                                }
                            ]
                        },
                        {
                            'name': 'Dolci',
                            'description': 'Classic Italian desserts with a Mumbai twist.',
                            'display_order': 3,
                            'items': [
                                {
                                    'name': 'Cold Brew Tiramisu',
                                    'description': 'Kahlua espresso soak, mascarpone cloud, cocoa nibs.',
                                    'price': Decimal('329.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1466978913421-dad2ebd01d17?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True
                                },
                                {
                                    'name': 'Vanilla Panna Cotta',
                                    'description': 'Silky smooth vanilla panna cotta with berry compote and mint.',
                                    'price': Decimal('299.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 5
                                },
                                {
                                    'name': 'Sicilian Cannoli',
                                    'description': 'Crispy shells filled with sweet ricotta, chocolate chips, pistachios.',
                                    'price': Decimal('349.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1599599810769-bcde5a160d32?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 7
                                }
                            ]
                        }
                    ]
                }
            },
            {
                'owner': mumbai_owner,
                'restaurant': {
                    'name': 'Mumbai Masala House',
                    'description': 'Comforting curries simmered overnight in copper pots with stone ground spices.',
                    'cuisine_type': Restaurant.CuisineType.INDIAN,
                    'phone': '+91 98201 22334',
                    'email': 'table@mumbaimasala.in',
                    'latitude': Decimal('19.0760'),
                    'longitude': Decimal('72.8777'),
                    'address': '7 Residency Road, Fort',
                    'city': 'Mumbai',
                    'state': 'Maharashtra',
                    'postal_code': '400001',
                    'country': 'India',
                    'status': Restaurant.Status.ACTIVE,
                    'rating': Decimal('4.8'),
                    'total_ratings': 312,
                    'delivery_time_minutes': 28,
                    'minimum_order_amount': Decimal('399.00'),
                    'delivery_fee': Decimal('35.00'),
                    'opening_hours': {
                        'monday': {'open': '10:00', 'close': '22:30'},
                        'tuesday': {'open': '10:00', 'close': '22:30'},
                        'wednesday': {'open': '10:00', 'close': '22:30'},
                        'thursday': {'open': '10:00', 'close': '22:30'},
                        'friday': {'open': '10:00', 'close': '23:30'},
                        'saturday': {'open': '10:00', 'close': '23:30'},
                        'sunday': {'open': '10:00', 'close': '22:00'},
                    },
                    'accepts_delivery': True,
                    'accepts_pickup': True,
                    'kyc_verified': True,
                    'logo_image_url': 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=200&q=80',
                    'hero_image_url': 'https://images.unsplash.com/photo-1600628422018-8b2b0320a84c?auto=format&fit=crop&w=900&q=80',
                },
                'menu': {
                    'name': 'Masala Kitchen',
                    'description': 'Slow cooked gravies, tandoor grills and Bombay street bites.',
                    'categories': [
                        {
                            'name': 'Signature Curries',
                            'description': 'Traditional gravies finished with fresh cream and desi ghee tadka.',
                            'display_order': 1,
                            'items': [
                                {
                                    'name': 'Butter Chicken Thali',
                                    'description': 'Charcoal grilled chicken tikka simmered in creamy tomato makhani, laccha paratha and jeera rice.',
                                    'price': Decimal('489.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1608039829570-0d5cec3f9a96?auto=format&fit=crop&w=600&q=80',
                                    'is_spicy': True
                                },
                                {
                                    'name': 'Paneer Lababdar',
                                    'description': 'Malai paneer, roasted cashew paste, brown onion masala and kasuri methi smoke.',
                                    'price': Decimal('439.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1626700051175-6818013e1d4f?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True
                                },
                                {
                                    'name': 'Coastal Prawn Moilee',
                                    'description': 'Coconut milk curry perfumed with curry leaves, kokum and ginger, served with appam.',
                                    'price': Decimal('529.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1631452180519-c014fe946bc7?auto=format&fit=crop&w=600&q=80',
                                    'is_spicy': True
                                },
                                {
                                    'name': 'Dal Makhani',
                                    'description': 'Creamy black lentils slow-cooked overnight with butter, cream, and spices.',
                                    'price': Decimal('389.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 25
                                },
                                {
                                    'name': 'Chicken Curry',
                                    'description': 'Traditional North Indian curry with tender chicken pieces in spiced tomato gravy.',
                                    'price': Decimal('459.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1603360946369-dc9bb6258143?auto=format&fit=crop&w=600&q=80',
                                    'is_spicy': True,
                                    'preparation_time_minutes': 30
                                },
                                {
                                    'name': 'Palak Paneer',
                                    'description': 'Fresh spinach curry with cubes of paneer, garlic, and aromatic spices.',
                                    'price': Decimal('419.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 20
                                }
                            ]
                        },
                        {
                            'name': 'Tandoor Specials',
                            'description': 'Charcoal grilled kebabs and tikkas.',
                            'display_order': 2,
                            'items': [
                                {
                                    'name': 'Chicken Tikka Platter',
                                    'description': 'Marinated chicken pieces grilled in tandoor, served with mint chutney.',
                                    'price': Decimal('449.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1603360946369-dc9bb6258143?auto=format&fit=crop&w=600&q=80',
                                    'is_spicy': True
                                },
                                {
                                    'name': 'Paneer Tikka',
                                    'description': 'Cubes of paneer marinated in yogurt and spices, grilled to perfection.',
                                    'price': Decimal('389.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1633919117791-b9b8e68c8c35?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True
                                },
                                {
                                    'name': 'Tandoori Chicken',
                                    'description': 'Whole chicken leg marinated in yogurt and tandoori spices, charcoal grilled.',
                                    'price': Decimal('499.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1596797038530-2c107229654b?auto=format&fit=crop&w=600&q=80',
                                    'is_spicy': True,
                                    'preparation_time_minutes': 25
                                },
                                {
                                    'name': 'Seekh Kebab',
                                    'description': 'Minced lamb kebabs spiced and grilled on skewers, served with onions.',
                                    'price': Decimal('469.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=600&q=80',
                                    'is_spicy': True,
                                    'preparation_time_minutes': 20
                                },
                                {
                                    'name': 'Malai Tikka',
                                    'description': 'Creamy marinated chicken tikka, grilled to perfection with a subtle flavor.',
                                    'price': Decimal('469.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1626089787857-5b27d3a4fa75?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 22
                                }
                            ]
                        },
                        {
                            'name': 'Biryani & Rice',
                            'description': 'Fragrant basmati rice dishes.',
                            'display_order': 3,
                            'items': [
                                {
                                    'name': 'Hyderabadi Chicken Biryani',
                                    'description': 'Layered basmati rice with spiced chicken, served with raita.',
                                    'price': Decimal('549.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1574868804907-d5842f50feca?auto=format&fit=crop&w=600&q=80',
                                    'is_spicy': True,
                                    'preparation_time_minutes': 35
                                },
                                {
                                    'name': 'Mutton Biryani',
                                    'description': 'Slow-cooked mutton layered with fragrant basmati rice, served with raita and salan.',
                                    'price': Decimal('599.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1608748011738-e06e5a029fb2?auto=format&fit=crop&w=600&q=80',
                                    'is_spicy': True,
                                    'preparation_time_minutes': 40
                                },
                                {
                                    'name': 'Veg Biryani',
                                    'description': 'Aromatic basmati rice with mixed vegetables, spices, and saffron.',
                                    'price': Decimal('449.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1589302168068-964664d93dc0?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 30
                                }
                            ]
                        },
                        {
                            'name': 'Bread Basket',
                            'description': 'Freshly baked Indian breads.',
                            'display_order': 4,
                            'items': [
                                {
                                    'name': 'Butter Naan',
                                    'description': 'Soft, fluffy naan brushed with butter.',
                                    'price': Decimal('79.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1606491956689-2ea866880c84?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 8
                                },
                                {
                                    'name': 'Garlic Naan',
                                    'description': 'Naan topped with garlic and coriander, brushed with butter.',
                                    'price': Decimal('99.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1626700051175-6818013e1d4f?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 8
                                },
                                {
                                    'name': 'Laccha Paratha',
                                    'description': 'Layered, flaky paratha, perfect with curries.',
                                    'price': Decimal('89.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1606491956689-2ea866880c84?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 10
                                }
                            ]
                        }
                    ]
                }
            },
            {
                'owner': sakura_owner,
                'restaurant': {
                    'name': 'Sakura Sushi Bar',
                    'description': 'Authentic Japanese sushi and sashimi with premium ingredients.',
                    'cuisine_type': Restaurant.CuisineType.JAPANESE,
                    'phone': '+91 98765 11223',
                    'email': 'reservations@sakurasushi.in',
                    'latitude': Decimal('19.0759'),
                    'longitude': Decimal('72.8776'),
                    'address': '45 Bandra Kurla Complex',
                    'city': 'Mumbai',
                    'state': 'Maharashtra',
                    'postal_code': '400051',
                    'country': 'India',
                    'status': Restaurant.Status.ACTIVE,
                    'rating': Decimal('4.7'),
                    'total_ratings': 189,
                    'delivery_time_minutes': 25,
                    'minimum_order_amount': Decimal('599.00'),
                    'delivery_fee': Decimal('50.00'),
                    'opening_hours': {
                        'monday': {'open': '12:00', 'close': '22:30'},
                        'tuesday': {'open': '12:00', 'close': '22:30'},
                        'wednesday': {'open': '12:00', 'close': '22:30'},
                        'thursday': {'open': '12:00', 'close': '22:30'},
                        'friday': {'open': '12:00', 'close': '23:00'},
                        'saturday': {'open': '12:00', 'close': '23:00'},
                        'sunday': {'open': '12:00', 'close': '22:00'},
                    },
                    'accepts_delivery': True,
                    'accepts_pickup': True,
                    'kyc_verified': True,
                    'logo_image_url': 'https://images.unsplash.com/photo-1579584425555-c3ce17fd4351?auto=format&fit=crop&w=200&q=80',
                    'hero_image_url': 'https://images.unsplash.com/photo-1579584425555-c3ce17fd4351?auto=format&fit=crop&w=900&q=80',
                },
                'menu': {
                    'name': 'Sakura Menu',
                    'description': 'Fresh sushi, sashimi and Japanese classics.',
                    'categories': [
                        {
                            'name': 'Sushi Rolls',
                            'description': 'Hand-rolled maki and uramaki.',
                            'display_order': 1,
                            'items': [
                                {
                                    'name': 'Dragon Roll',
                                    'description': 'Eel, cucumber, avocado, topped with eel sauce.',
                                    'price': Decimal('899.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1579584425555-c3ce17fd4351?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 15
                                },
                                {
                                    'name': 'California Roll',
                                    'description': 'Crab, avocado, cucumber with sesame seeds.',
                                    'price': Decimal('649.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1579584425555-c3ce17fd4351?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': False,
                                    'preparation_time_minutes': 12
                                },
                                {
                                    'name': 'Spicy Tuna Roll',
                                    'description': 'Fresh tuna, spicy mayo, cucumber.',
                                    'price': Decimal('749.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1579584425555-c3ce17fd4351?auto=format&fit=crop&w=600&q=80',
                                    'is_spicy': True,
                                    'preparation_time_minutes': 12
                                },
                                {
                                    'name': 'Rainbow Roll',
                                    'description': 'California roll topped with assorted sashimi in rainbow colors.',
                                    'price': Decimal('999.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1617196034183-421b4917c92d?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 18
                                },
                                {
                                    'name': 'Philadelphia Roll',
                                    'description': 'Smoked salmon, cream cheese, cucumber, avocado.',
                                    'price': Decimal('799.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1579584425555-c3ce17fd4351?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 13
                                },
                                {
                                    'name': 'Spicy Salmon Roll',
                                    'description': 'Fresh salmon, spicy mayo, cucumber, topped with salmon.',
                                    'price': Decimal('849.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1617196034183-421b4917c92d?auto=format&fit=crop&w=600&q=80',
                                    'is_spicy': True,
                                    'preparation_time_minutes': 14
                                },
                                {
                                    'name': 'Eel Avocado Roll',
                                    'description': 'Grilled eel, avocado, cucumber, topped with eel sauce.',
                                    'price': Decimal('949.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1611143669185-af224c5e3252?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 15
                                }
                            ]
                        },
                        {
                            'name': 'Sashimi',
                            'description': 'Premium raw fish slices.',
                            'display_order': 2,
                            'items': [
                                {
                                    'name': 'Salmon Sashimi (6 pcs)',
                                    'description': 'Fresh Atlantic salmon, wasabi and soy sauce.',
                                    'price': Decimal('799.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1617196034183-421b4917c92d?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 8
                                },
                                {
                                    'name': 'Tuna Sashimi (6 pcs)',
                                    'description': 'Premium bluefin tuna, wasabi and soy sauce.',
                                    'price': Decimal('899.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1611143669185-af224c5e3252?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 8
                                },
                                {
                                    'name': 'Tuna Tataki',
                                    'description': 'Seared tuna slices with ponzu sauce and daikon radish.',
                                    'price': Decimal('949.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1611143669185-af224c5e3252?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 10
                                },
                                {
                                    'name': 'Yellowtail Sashimi (6 pcs)',
                                    'description': 'Fresh yellowtail amberjack, wasabi and soy sauce.',
                                    'price': Decimal('849.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1611143669185-af224c5e3252?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 8
                                }
                            ]
                        },
                        {
                            'name': 'Ramen & Noodles',
                            'description': 'Comforting bowls of noodles.',
                            'display_order': 3,
                            'items': [
                                {
                                    'name': 'Tonkotsu Ramen',
                                    'description': 'Rich pork bone broth, chashu, soft-boiled egg, nori.',
                                    'price': Decimal('599.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 20
                                },
                                {
                                    'name': 'Miso Ramen',
                                    'description': 'Savory miso broth with chashu, corn, bean sprouts, nori.',
                                    'price': Decimal('579.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 18
                                },
                                {
                                    'name': 'Shoyu Ramen',
                                    'description': 'Soy sauce-based broth with chashu, menma, scallions, nori.',
                                    'price': Decimal('569.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 18
                                }
                            ]
                        },
                        {
                            'name': 'Appetizers',
                            'description': 'Japanese starters and small plates.',
                            'display_order': 4,
                            'items': [
                                {
                                    'name': 'Edamame',
                                    'description': 'Steamed soybeans sprinkled with sea salt.',
                                    'price': Decimal('199.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1596797038530-2c107229654b?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 5
                                },
                                {
                                    'name': 'Gyoza (6 pcs)',
                                    'description': 'Pan-fried pork dumplings with soy-vinegar dipping sauce.',
                                    'price': Decimal('349.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 12
                                },
                                {
                                    'name': 'Tempura Platter',
                                    'description': 'Assorted vegetables and shrimp tempura with tentsuyu sauce.',
                                    'price': Decimal('449.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1626700051175-6818013e1d4f?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 15
                                }
                            ]
                        }
                    ]
                }
            },
            {
                'owner': thai_owner,
                'restaurant': {
                    'name': 'Bangkok Express',
                    'description': 'Authentic Thai street food with bold flavors.',
                    'cuisine_type': Restaurant.CuisineType.THAI,
                    'phone': '+91 98765 33445',
                    'email': 'hello@bangkokexpress.in',
                    'latitude': Decimal('19.0760'),
                    'longitude': Decimal('72.8777'),
                    'address': '23 Andheri West',
                    'city': 'Mumbai',
                    'state': 'Maharashtra',
                    'postal_code': '400053',
                    'country': 'India',
                    'status': Restaurant.Status.ACTIVE,
                    'rating': Decimal('4.5'),
                    'total_ratings': 156,
                    'delivery_time_minutes': 30,
                    'minimum_order_amount': Decimal('449.00'),
                    'delivery_fee': Decimal('40.00'),
                    'opening_hours': {
                        'monday': {'open': '11:30', 'close': '23:00'},
                        'tuesday': {'open': '11:30', 'close': '23:00'},
                        'wednesday': {'open': '11:30', 'close': '23:00'},
                        'thursday': {'open': '11:30', 'close': '23:00'},
                        'friday': {'open': '11:30', 'close': '23:30'},
                        'saturday': {'open': '11:30', 'close': '23:30'},
                        'sunday': {'open': '11:30', 'close': '23:00'},
                    },
                    'accepts_delivery': True,
                    'accepts_pickup': True,
                    'kyc_verified': True,
                    'logo_image_url': 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=200&q=80',
                    'hero_image_url': 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=900&q=80',
                },
                'menu': {
                    'name': 'Thai Street Food',
                    'description': 'Pad thai, curries and Thai classics.',
                    'categories': [
                        {
                            'name': 'Curries',
                            'description': 'Aromatic Thai curries.',
                            'display_order': 1,
                            'items': [
                                {
                                    'name': 'Green Curry with Chicken',
                                    'description': 'Coconut milk, Thai basil, eggplant, served with jasmine rice.',
                                    'price': Decimal('549.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=600&q=80',
                                    'is_spicy': True,
                                    'preparation_time_minutes': 25
                                },
                                {
                                    'name': 'Massaman Curry',
                                    'description': 'Mild curry with potatoes, peanuts, served with roti.',
                                    'price': Decimal('529.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 25
                                },
                                {
                                    'name': 'Red Curry with Chicken',
                                    'description': 'Spicy red curry paste with coconut milk, Thai basil, served with jasmine rice.',
                                    'price': Decimal('539.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?auto=format&fit=crop&w=600&q=80',
                                    'is_spicy': True,
                                    'preparation_time_minutes': 25
                                },
                                {
                                    'name': 'Yellow Curry',
                                    'description': 'Mild yellow curry with potatoes, carrots, coconut milk, served with roti.',
                                    'price': Decimal('519.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 23
                                }
                            ]
                        },
                        {
                            'name': 'Noodles & Rice',
                            'description': 'Stir-fried noodles and rice dishes.',
                            'display_order': 2,
                            'items': [
                                {
                                    'name': 'Pad Thai',
                                    'description': 'Stir-fried rice noodles with shrimp, tofu, bean sprouts.',
                                    'price': Decimal('449.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 18
                                },
                                {
                                    'name': 'Thai Fried Rice',
                                    'description': 'Jasmine rice with vegetables, egg, Thai basil.',
                                    'price': Decimal('399.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1608748011738-e06e5a029fb2?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 15
                                },
                                {
                                    'name': 'Pad See Ew',
                                    'description': 'Wide rice noodles stir-fried with soy sauce, egg, Chinese broccoli.',
                                    'price': Decimal('429.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 16
                                },
                                {
                                    'name': 'Tom Yum Fried Rice',
                                    'description': 'Jasmine rice fried with tom yum paste, vegetables, and Thai herbs.',
                                    'price': Decimal('439.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1589302168068-964664d93dc0?auto=format&fit=crop&w=600&q=80',
                                    'is_spicy': True,
                                    'preparation_time_minutes': 18
                                },
                                {
                                    'name': 'Pineapple Fried Rice',
                                    'description': 'Jasmine rice with pineapple, cashews, raisins, curry powder.',
                                    'price': Decimal('459.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1633919117791-b9b8e68c8c35?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 17
                                }
                            ]
                        },
                        {
                            'name': 'Appetizers',
                            'description': 'Thai starters and small bites.',
                            'display_order': 3,
                            'items': [
                                {
                                    'name': 'Thai Spring Rolls (4 pcs)',
                                    'description': 'Crispy vegetable spring rolls with sweet chili sauce.',
                                    'price': Decimal('249.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1626700051175-6818013e1d4f?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 12
                                },
                                {
                                    'name': 'Thai Fish Cakes (4 pcs)',
                                    'description': 'Spiced fish cakes with cucumber relish and sweet chili sauce.',
                                    'price': Decimal('299.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=600&q=80',
                                    'is_spicy': True,
                                    'preparation_time_minutes': 15
                                },
                                {
                                    'name': 'Som Tam Salad',
                                    'description': 'Green papaya salad with tomatoes, peanuts, lime dressing.',
                                    'price': Decimal('259.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'is_spicy': True,
                                    'preparation_time_minutes': 10
                                }
                            ]
                        }
                    ]
                }
            }
            ,
            {
                'owner': koramangala_owner,
                'restaurant': {
                    'name': 'Koramangala Smokehouse',
                    'description': 'Live-fire grills, biryanis, and late-night bowls designed for delivery.',
                    'cuisine_type': Restaurant.CuisineType.AMERICAN,
                    'cuisine_types': [Restaurant.CuisineType.AMERICAN, Restaurant.CuisineType.FAST_FOOD],
                    'restaurant_type': Restaurant.RestaurantType.NON_VEG,
                    'phone': '+91 99000 11221',
                    'email': 'ops@korasmokehouse.in',
                    'latitude': Decimal('12.9352'),
                    'longitude': Decimal('77.6245'),
                    'address': '80 Feet Road, Koramangala 4th Block',
                    'city': 'Bengaluru',
                    'state': 'Karnataka',
                    'postal_code': '560034',
                    'country': 'India',
                    'status': Restaurant.Status.ACTIVE,
                    'rating': Decimal('4.5'),
                    'total_ratings': 210,
                    'delivery_time_minutes': 27,
                    'minimum_order_amount': Decimal('399.00'),
                    'delivery_fee': Decimal('35.00'),
                    'delivery_radius_km': Decimal('6.0'),
                    'manager_contact_name': 'Neha Rao',
                    'manager_contact_phone': '+91 99000 11221',
                    'manager_contact_email': 'neha@korasmokehouse.in',
                    'fssai_license_number': 'FSSAI-KORA-2024',
                    'gst_number': '29ABCDE1234F1Z5',
                    'bank_account_number': '123456789012',
                    'bank_ifsc_code': 'HDFC0000123',
                    'support_phone': '+91 99000 11221',
                    'support_email': 'support@korasmokehouse.in',
                    'is_multi_branch': True,
                    'opening_hours': {
                        'monday': {'open': '11:00', 'close': '23:59'},
                        'tuesday': {'open': '11:00', 'close': '23:59'},
                        'wednesday': {'open': '11:00', 'close': '23:59'},
                        'thursday': {'open': '11:00', 'close': '23:59'},
                        'friday': {'open': '11:00', 'close': '23:59'},
                        'saturday': {'open': '11:00', 'close': '23:59'},
                        'sunday': {'open': '11:00', 'close': '23:59'},
                    },
                    'accepts_delivery': True,
                    'accepts_pickup': True,
                    'logo_image_url': 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=200&q=80',
                    'hero_image_url': 'https://images.unsplash.com/photo-1529042410759-befb1204b468?auto=format&fit=crop&w=900&q=80',
                },
                'menu': {
                    'name': 'Koramangala All-day',
                    'description': 'Smoked meats, rice bowls, and bar snacks.',
                    'categories': [
                        {
                            'name': 'Smoked Bowls',
                            'description': 'Slow-smoked meats over fragrant rice.',
                            'display_order': 1,
                            'items': [
                                {
                                    'name': 'Smoked Butter Chicken Bowl',
                                    'description': 'Charcoal smoked chicken tikka with butter masala gravy on jeera rice.',
                                    'price': Decimal('489.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1608039829570-0d5cec3f9a96?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 22
                                },
                                {
                                    'name': 'BBQ Jackfruit Bowl',
                                    'description': 'Tamarind glazed jackfruit, pickled veggies, millet rice.',
                                    'price': Decimal('429.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1626700051175-6818013e1d4f?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 18
                                },
                                {
                                    'name': 'Smoky Lamb Nihari Bowl',
                                    'description': 'Wood-smoked lamb, saffron rice, roasted garlic yogurt, crispy onions.',
                                    'price': Decimal('539.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 24
                                },
                                {
                                    'name': 'BBQ Chicken Rice Bowl',
                                    'description': 'Charcoal grilled chicken, barbecue sauce, coleslaw, basmati rice.',
                                    'price': Decimal('469.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1603360946369-dc9bb6258143?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 20
                                },
                                {
                                    'name': 'Pulled Pork Bowl',
                                    'description': 'Slow-smoked pulled pork, corn salsa, black beans, cilantro rice.',
                                    'price': Decimal('499.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1626089787857-5b27d3a4fa75?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 22
                                }
                            ]
                        },
                        {
                            'name': 'Night Bites',
                            'description': 'Perfect for post-midnight cravings.',
                            'display_order': 2,
                            'items': [
                                {
                                    'name': 'Chaat Spiced Wings',
                                    'description': 'Smoked chicken wings tossed in amchur and chilli butter.',
                                    'price': Decimal('349.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1608039829570-0d5cec3f9a96?auto=format&fit=crop&w=600&q=80',
                                    'is_spicy': True,
                                    'preparation_time_minutes': 15
                                },
                                {
                                    'name': 'Loaded Peri Fries',
                                    'description': 'Twice cooked fries, peri-peri dust, garlic aioli.',
                                    'price': Decimal('249.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 12
                                },
                                {
                                    'name': 'Bonfire Paneer Tikka',
                                    'description': 'Smoked malai paneer skewers, chilli butter baste, pickled onions.',
                                    'price': Decimal('369.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1633919117791-b9b8e68c8c35?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 16
                                },
                                {
                                    'name': 'Smoked Chicken Wings (6 pcs)',
                                    'description': 'Charcoal smoked wings with honey BBQ glaze.',
                                    'price': Decimal('329.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1608039829570-0d5cec3f9a96?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 18
                                },
                                {
                                    'name': 'Nachos Supreme',
                                    'description': 'Crispy nachos loaded with cheese, jalapeños, sour cream, salsa.',
                                    'price': Decimal('299.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1611143669185-af224c5e3252?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 10
                                }
                            ]
                        },
                        {
                            'name': 'Burgers & Wraps',
                            'description': 'Smoked meats in buns and wraps.',
                            'display_order': 3,
                            'items': [
                                {
                                    'name': 'Smoked Chicken Burger',
                                    'description': 'Charcoal smoked chicken patty, coleslaw, pickles, BBQ sauce, brioche bun.',
                                    'price': Decimal('379.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1603360946369-dc9bb6258143?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 15
                                },
                                {
                                    'name': 'Pulled Pork Wrap',
                                    'description': 'Slow-smoked pulled pork, coleslaw, chipotle mayo, tortilla wrap.',
                                    'price': Decimal('359.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1626089787857-5b27d3a4fa75?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 12
                                },
                                {
                                    'name': 'BBQ Chicken Wrap',
                                    'description': 'Grilled chicken, lettuce, tomatoes, onions, BBQ sauce, tortilla.',
                                    'price': Decimal('339.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1608039829570-0d5cec3f9a96?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 10
                                }
                            ]
                        }
                    ]
                },
                'branches': [
                    {
                        'name': 'Koramangala Cloud Kitchen',
                        'branch_type': RestaurantBranch.BranchType.MAIN,
                        'address_line1': '80 Feet Road',
                        'city': 'Bengaluru',
                        'state': 'Karnataka',
                        'postal_code': '560034',
                        'country': 'India',
                        'service_radius_km': Decimal('6.0'),
                        'is_primary': True,
                        'supports_delivery': True,
                        'supports_pickup': True
                    },
                    {
                        'name': 'Indiranagar Pickup Hub',
                        'branch_type': RestaurantBranch.BranchType.PICKUP,
                        'address_line1': '12th Main, Indiranagar',
                        'city': 'Bengaluru',
                        'state': 'Karnataka',
                        'postal_code': '560038',
                        'country': 'India',
                        'service_radius_km': Decimal('4.0'),
                        'supports_delivery': False,
                        'supports_pickup': True
                    }
                ],
                'managers': [
                    {
                        'first_name': 'Rakesh',
                        'last_name': 'Menon',
                        'email': 'rakesh@korasmokehouse.in',
                        'phone': '+91 99000 33445',
                        'role': ManagerProfile.ManagerRole.KITCHEN_MANAGER,
                        'is_primary': True
                    },
                    {
                        'first_name': 'Aditi',
                        'last_name': 'Pai',
                        'email': 'aditi@korasmokehouse.in',
                        'phone': '+91 99555 11223',
                        'role': ManagerProfile.ManagerRole.OPERATIONS,
                        'is_primary': False
                    }
                ]
            },
            {
                'owner': indiranagar_owner,
                'restaurant': {
                    'name': 'Indiranagar Green Bowl',
                    'description': 'Plant-forward kitchen with millet bowls, smoothie jars, and cold-pressed brews.',
                    'cuisine_type': Restaurant.CuisineType.VEGETARIAN,
                    'cuisine_types': [Restaurant.CuisineType.VEGETARIAN, Restaurant.CuisineType.MEDITERRANEAN],
                    'restaurant_type': Restaurant.RestaurantType.PURE_VEG,
                    'phone': '+91 98450 99887',
                    'email': 'hello@greenbowl.in',
                    'latitude': Decimal('12.9716'),
                    'longitude': Decimal('77.6411'),
                    'address': '100 Feet Road, Indiranagar',
                    'city': 'Bengaluru',
                    'state': 'Karnataka',
                    'postal_code': '560038',
                    'country': 'India',
                    'status': Restaurant.Status.ACTIVE,
                    'rating': Decimal('4.7'),
                    'total_ratings': 178,
                    'delivery_time_minutes': 24,
                    'minimum_order_amount': Decimal('299.00'),
                    'delivery_fee': Decimal('30.00'),
                    'delivery_radius_km': Decimal('5.0'),
                    'manager_contact_name': 'Varun Iyer',
                    'manager_contact_phone': '+91 98450 99887',
                    'manager_contact_email': 'varun@greenbowl.in',
                    'fssai_license_number': 'FSSAI-INDI-2024',
                    'gst_number': '29XYZDE1234F1Z4',
                    'support_phone': '+91 98450 99887',
                    'support_email': 'care@greenbowl.in',
                    'is_multi_branch': False,
                    'opening_hours': {
                        'monday': {'open': '09:00', 'close': '22:00'},
                        'tuesday': {'open': '09:00', 'close': '22:00'},
                        'wednesday': {'open': '09:00', 'close': '22:00'},
                        'thursday': {'open': '09:00', 'close': '22:00'},
                        'friday': {'open': '09:00', 'close': '23:00'},
                        'saturday': {'open': '09:00', 'close': '23:00'},
                        'sunday': {'open': '09:00', 'close': '21:00'},
                    },
                    'accepts_delivery': True,
                    'accepts_pickup': True,
                    'logo_image_url': 'https://images.unsplash.com/photo-1478144592103-25e218a04891?auto=format&fit=crop&w=200&q=80',
                    'hero_image_url': 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=900&q=80',
                },
                'menu': {
                    'name': 'Green Bowl Menu',
                    'description': 'Millet bowls, smoothie jars, and salads',
                    'categories': [
                        {
                            'name': 'Millet Bowls',
                            'description': 'High fibre bowls with local grains.',
                            'display_order': 1,
                            'items': [
                                {
                                    'name': 'Roasted Paneer Millet Bowl',
                                    'description': 'Foxtail millet, charred paneer, tahini dressing, pickled veggies.',
                                    'price': Decimal('379.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1626700051175-6818013e1d4f?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 15
                                },
                                {
                                    'name': 'Thai Peanut Tempeh Bowl',
                                    'description': 'Barnyard millet, tempeh, peanut satay, microgreens.',
                                    'price': Decimal('399.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1633919117791-b9b8e68c8c35?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'is_spicy': True,
                                    'preparation_time_minutes': 17
                                },
                                {
                                    'name': 'Smoked Beet & Quinoa Bowl',
                                    'description': 'Red quinoa, smoked beets, pistachio crunch, kokum dressing.',
                                    'price': Decimal('389.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 15
                                },
                                {
                                    'name': 'Mediterranean Millet Bowl',
                                    'description': 'Pearl millet, roasted vegetables, feta, olives, hummus.',
                                    'price': Decimal('389.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 16
                                },
                                {
                                    'name': 'Avocado & Black Bean Bowl',
                                    'description': 'Finger millet, black beans, avocado, corn salsa, lime dressing.',
                                    'price': Decimal('359.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1626700051175-6818013e1d4f?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 14
                                }
                            ]
                        },
                        {
                            'name': 'Smoothie Jars',
                            'description': 'Cold-pressed smoothies with granola toppers.',
                            'display_order': 2,
                            'items': [
                                {
                                    'name': 'Monk Fruit Berry Jar',
                                    'description': 'Blueberries, almond milk, chia crunch.',
                                    'price': Decimal('299.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 8
                                },
                                {
                                    'name': 'Turmeric Glow Jar',
                                    'description': 'Mango, turmeric, coconut yogurt, toasted seeds.',
                                    'price': Decimal('309.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 8
                                },
                                {
                                    'name': 'Espresso Almond Crunch',
                                    'description': 'Cold brew, soaked almonds, cacao nib crumble.',
                                    'price': Decimal('319.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 7
                                },
                                {
                                    'name': 'Green Detox Jar',
                                    'description': 'Spinach, kale, green apple, cucumber, mint, chia seeds.',
                                    'price': Decimal('289.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 8
                                }
                            ]
                        },
                        {
                            'name': 'Salads',
                            'description': 'Fresh, healthy salads with local produce.',
                            'display_order': 3,
                            'items': [
                                {
                                    'name': 'Quinoa Salad',
                                    'description': 'Red quinoa, roasted vegetables, feta cheese, lemon vinaigrette.',
                                    'price': Decimal('349.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 12
                                },
                                {
                                    'name': 'Mediterranean Salad',
                                    'description': 'Mixed greens, cherry tomatoes, cucumber, olives, feta, balsamic.',
                                    'price': Decimal('329.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 10
                                },
                                {
                                    'name': 'Kale Caesar Salad',
                                    'description': 'Kale, romaine, parmesan, croutons, caesar dressing.',
                                    'price': Decimal('339.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 10
                                }
                            ]
                        }
                    ]
                },
                'branches': [
                    {
                        'name': 'Indiranagar Studio',
                        'branch_type': RestaurantBranch.BranchType.MAIN,
                        'address_line1': '100 Feet Road',
                        'city': 'Bengaluru',
                        'state': 'Karnataka',
                        'postal_code': '560038',
                        'country': 'India',
                        'service_radius_km': Decimal('5.0'),
                        'is_primary': True,
                        'supports_delivery': True,
                        'supports_pickup': True
                    }
                ],
                'managers': [
                    {
                        'first_name': 'Meera',
                        'last_name': 'Nair',
                        'email': 'meera@greenbowl.in',
                        'phone': '+91 98450 22110',
                        'role': ManagerProfile.ManagerRole.GENERAL_MANAGER,
                        'is_primary': True
                    }
                ]
            },
            {
                'owner': bangalore_owner,
                'restaurant': {
                    'name': 'MG Road Spice Studio',
                    'description': 'Progressive Indian tasting kitchen pairing heirloom recipes with Bangalore produce.',
                    'cuisine_type': Restaurant.CuisineType.INDIAN,
                    'cuisine_types': [Restaurant.CuisineType.INDIAN, Restaurant.CuisineType.THAI],
                    'restaurant_type': Restaurant.RestaurantType.NON_VEG,
                    'phone': '+91 99800 66778',
                    'email': 'hello@spicestudio.in',
                    'latitude': Decimal('12.9756'),
                    'longitude': Decimal('77.6033'),
                    'address': '1 MG Road, Bengaluru',
                    'city': 'Bengaluru',
                    'state': 'Karnataka',
                    'postal_code': '560001',
                    'country': 'India',
                    'status': Restaurant.Status.ACTIVE,
                    'rating': Decimal('4.8'),
                    'total_ratings': 320,
                    'delivery_time_minutes': 28,
                    'minimum_order_amount': Decimal('349.00'),
                    'delivery_fee': Decimal('35.00'),
                    'delivery_radius_km': Decimal('7.0'),
                    'manager_contact_name': 'Aarav Iyengar',
                    'manager_contact_phone': '+91 99800 66778',
                    'manager_contact_email': 'ops@spicestudio.in',
                    'fssai_license_number': 'FSSAI-BLR-2024',
                    'gst_number': '29ABCDE1234F1Z5',
                    'support_phone': '+91 99800 66778',
                    'support_email': 'support@spicestudio.in',
                    'opening_hours': {
                        'monday': {'open': '11:00', 'close': '23:00'},
                        'tuesday': {'open': '11:00', 'close': '23:00'},
                        'wednesday': {'open': '11:00', 'close': '23:00'},
                        'thursday': {'open': '11:00', 'close': '23:00'},
                        'friday': {'open': '11:00', 'close': '23:30'},
                        'saturday': {'open': '11:00', 'close': '23:30'},
                        'sunday': {'open': '11:00', 'close': '22:30'},
                    },
                    'accepts_delivery': True,
                    'accepts_pickup': True,
                    'logo_image_url': 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=200&q=80',
                    'hero_image_url': 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=900&q=80',
                },
                'menu': {
                    'name': 'Spice Studio Menu',
                    'description': 'Tasting plates, curry flights, and charcoal grills.',
                    'categories': [
                        {
                            'name': 'Tasting Plates',
                            'description': 'Small plates designed for pairing.',
                            'display_order': 1,
                            'items': [
                                {
                                    'name': 'Charred Tandoori Broccoli',
                                    'description': 'Gunpowder spice, burnt lemon yogurt, pickled pearl onions.',
                                    'price': Decimal('389.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1626700051175-6818013e1d4f?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 12
                                },
                                {
                                    'name': 'Malai Chicken Slayer',
                                    'description': 'Cream cheese marinated chicken, smoked chili oil, millet crisps.',
                                    'price': Decimal('429.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1608039829570-0d5cec3f9a96?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 15
                                },
                                {
                                    'name': 'Gunpowder Crab Cakes',
                                    'description': 'Pepper crust, coconut chutney espuma, radish salad.',
                                    'price': Decimal('489.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 14
                                },
                                {
                                    'name': 'Thai-Spiced Cauliflower Bites',
                                    'description': 'Crispy cauliflower tossed in Thai chili sauce, peanuts, cilantro.',
                                    'price': Decimal('369.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1633919117791-b9b8e68c8c35?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'is_spicy': True,
                                    'preparation_time_minutes': 13
                                },
                                {
                                    'name': 'Fusion Fish Tacos',
                                    'description': 'Crispy fish, thai coleslaw, chipotle mayo, soft tortillas.',
                                    'price': Decimal('459.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 16
                                }
                            ]
                        },
                        {
                            'name': 'Curry Flights',
                            'description': 'Mini pots of regional gravies with khameeri breads.',
                            'display_order': 2,
                            'items': [
                                {
                                    'name': 'Coorg Koli Curry',
                                    'description': 'Pepper chicken, pandi masala, akki rotti crisps.',
                                    'price': Decimal('499.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1608039829570-0d5cec3f9a96?auto=format&fit=crop&w=600&q=80',
                                    'is_spicy': True,
                                    'preparation_time_minutes': 30
                                },
                                {
                                    'name': 'Malabar Pumpkin Stew',
                                    'description': 'Coconut milk, curry leaf tadka, jackfruit chips.',
                                    'price': Decimal('379.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1626700051175-6818013e1d4f?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 25
                                },
                                {
                                    'name': 'Lucknowi Nihari Pot',
                                    'description': 'Slow-cooked mutton, saffron sheermal shards, pickled onions.',
                                    'price': Decimal('549.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=600&q=80',
                                    'is_spicy': True,
                                    'preparation_time_minutes': 40
                                },
                                {
                                    'name': 'Thai Green Curry with Tofu',
                                    'description': 'Coconut milk, Thai basil, eggplant, crispy tofu.',
                                    'price': Decimal('459.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'is_spicy': True,
                                    'preparation_time_minutes': 22
                                },
                                {
                                    'name': 'Chettinad Chicken Curry',
                                    'description': 'Spicy South Indian curry with coconut, curry leaves, served with appam.',
                                    'price': Decimal('529.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1608039829570-0d5cec3f9a96?auto=format&fit=crop&w=600&q=80',
                                    'is_spicy': True,
                                    'preparation_time_minutes': 28
                                }
                            ]
                        },
                        {
                            'name': 'Desserts',
                            'description': 'Indian and fusion desserts.',
                            'display_order': 3,
                            'items': [
                                {
                                    'name': 'Gulab Jamun (2 pcs)',
                                    'description': 'Soft, syrupy milk dumplings, served warm.',
                                    'price': Decimal('149.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 5
                                },
                                {
                                    'name': 'Kheer',
                                    'description': 'Creamy rice pudding with cardamom, saffron, nuts.',
                                    'price': Decimal('179.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 6
                                },
                                {
                                    'name': 'Mango Lassi',
                                    'description': 'Sweet mango yogurt drink, topped with pistachios.',
                                    'price': Decimal('159.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 5
                                }
                            ]
                        }
                    ]
                },
                'branches': [
                    {
                        'name': 'MG Road Flagship',
                        'branch_type': RestaurantBranch.BranchType.MAIN,
                        'address_line1': '1 MG Road',
                        'city': 'Bengaluru',
                        'state': 'Karnataka',
                        'postal_code': '560001',
                        'country': 'India',
                        'service_radius_km': Decimal('7.0'),
                        'is_primary': True,
                    }
                ],
                'managers': [
                    {
                        'first_name': 'Ila',
                        'last_name': 'Narayan',
                        'email': 'ila@spicestudio.in',
                        'phone': '+91 99800 66779',
                        'role': ManagerProfile.ManagerRole.KITCHEN_MANAGER,
                        'is_primary': True
                    }
                ]
            },
            {
                'owner': whitefield_owner,
                'restaurant': {
                    'name': 'Whitefield Vegan CoLab',
                    'description': 'Bangalore’s first plant-based commissary powering smoothie bowls, salads, and keto-friendly desserts.',
                    'cuisine_type': Restaurant.CuisineType.VEGAN,
                    'cuisine_types': [Restaurant.CuisineType.VEGAN, Restaurant.CuisineType.MEDITERRANEAN],
                    'restaurant_type': Restaurant.RestaurantType.PURE_VEG,
                    'phone': '+91 99777 88990',
                    'email': 'team@vegancolab.in',
                    'latitude': Decimal('12.9698'),
                    'longitude': Decimal('77.7499'),
                    'address': 'ITPL Main Road, Whitefield',
                    'city': 'Bengaluru',
                    'state': 'Karnataka',
                    'postal_code': '560066',
                    'country': 'India',
                    'status': Restaurant.Status.ACTIVE,
                    'rating': Decimal('4.9'),
                    'total_ratings': 142,
                    'delivery_time_minutes': 22,
                    'minimum_order_amount': Decimal('249.00'),
                    'delivery_fee': Decimal('25.00'),
                    'delivery_radius_km': Decimal('6.0'),
                    'manager_contact_name': 'Sahana Prakash',
                    'manager_contact_phone': '+91 99777 88990',
                    'manager_contact_email': 'ops@vegancolab.in',
                    'support_phone': '+91 99777 88990',
                    'support_email': 'support@vegancolab.in',
                    'opening_hours': {
                        'monday': {'open': '08:00', 'close': '21:30'},
                        'tuesday': {'open': '08:00', 'close': '21:30'},
                        'wednesday': {'open': '08:00', 'close': '21:30'},
                        'thursday': {'open': '08:00', 'close': '21:30'},
                        'friday': {'open': '08:00', 'close': '22:00'},
                        'saturday': {'open': '08:00', 'close': '22:00'},
                        'sunday': {'open': '08:00', 'close': '21:00'},
                    },
                    'accepts_delivery': True,
                    'accepts_pickup': True,
                },
                'menu': {
                    'name': 'Colab Menu',
                    'description': 'Smoothie bowls, salads, vegan desserts.',
                    'categories': [
                        {
                            'name': 'Smoothie Bowls',
                            'display_order': 1,
                            'items': [
                                {
                                    'name': 'Cacao Almond Bowl',
                                    'description': 'Cacao nibs, soaked almonds, chia crumble.',
                                    'price': Decimal('329.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'is_vegan': True,
                                    'preparation_time_minutes': 8
                                },
                                {
                                    'name': 'Dragonfruit Crunch',
                                    'description': 'Pitaya, coconut kefir, granola shards.',
                                    'price': Decimal('339.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'is_vegan': True,
                                    'preparation_time_minutes': 8
                                },
                                {
                                    'name': 'Mint Julep Bowl',
                                    'description': 'Spearmint, lime zest chia pudding, roasted cashews.',
                                    'price': Decimal('329.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'is_vegan': True,
                                    'preparation_time_minutes': 8
                                },
                                {
                                    'name': 'Acai Berry Bowl',
                                    'description': 'Acai base, mixed berries, banana, granola, coconut flakes.',
                                    'price': Decimal('349.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'is_vegan': True,
                                    'preparation_time_minutes': 9
                                },
                                {
                                    'name': 'Tropical Paradise Bowl',
                                    'description': 'Mango, pineapple, coconut, banana, chia seeds, hemp hearts.',
                                    'price': Decimal('339.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'is_vegan': True,
                                    'preparation_time_minutes': 8
                                }
                            ]
                        },
                        {
                            'name': 'Salads',
                            'display_order': 2,
                            'items': [
                                {
                                    'name': 'Sourdough Panzanella',
                                    'description': 'Vegan feta, charred sourdough, basil oil.',
                                    'price': Decimal('289.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'is_vegan': True,
                                    'preparation_time_minutes': 10
                                },
                                {
                                    'name': 'Keto Tofu Crunch',
                                    'description': 'Baked tofu, activated seeds, avocado tahini.',
                                    'price': Decimal('309.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'is_vegan': True,
                                    'preparation_time_minutes': 12
                                },
                                {
                                    'name': 'Harissa Chickpea Salad',
                                    'description': 'Warm chickpeas, harissa oil, crispy kale, citrus dressing.',
                                    'price': Decimal('289.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?auto=format&fit=crop&w=600&q=80',
                                    'is_spicy': True,
                                    'is_vegetarian': True,
                                    'is_vegan': True,
                                    'preparation_time_minutes': 11
                                },
                                {
                                    'name': 'Quinoa Power Salad',
                                    'description': 'Quinoa, roasted vegetables, pumpkin seeds, lemon tahini dressing.',
                                    'price': Decimal('319.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'is_vegan': True,
                                    'preparation_time_minutes': 13
                                }
                            ]
                        },
                        {
                            'name': 'Power Bowls',
                            'description': 'Nutritious, protein-packed vegan bowls.',
                            'display_order': 3,
                            'items': [
                                {
                                    'name': 'Buddha Bowl',
                                    'description': 'Brown rice, roasted vegetables, chickpeas, tahini, avocado, seeds.',
                                    'price': Decimal('369.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1626700051175-6818013e1d4f?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'is_vegan': True,
                                    'preparation_time_minutes': 15
                                },
                                {
                                    'name': 'Acai Power Bowl',
                                    'description': 'Acai base, banana, berries, granola, almond butter, coconut.',
                                    'price': Decimal('359.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1626700051175-6818013e1d4f?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'is_vegan': True,
                                    'preparation_time_minutes': 10
                                },
                                {
                                    'name': 'Protein Bowl',
                                    'description': 'Quinoa, tempeh, black beans, kale, roasted sweet potato, avocado.',
                                    'price': Decimal('389.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1626700051175-6818013e1d4f?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'is_vegan': True,
                                    'preparation_time_minutes': 17
                                }
                            ]
                        }
                    ]
                },
                'branches': [
                    {
                        'name': 'Whitefield Commissary',
                        'branch_type': RestaurantBranch.BranchType.CLOUD,
                        'address_line1': 'ITPL Main Road',
                        'city': 'Bengaluru',
                        'state': 'Karnataka',
                        'postal_code': '560066',
                        'country': 'India',
                        'service_radius_km': Decimal('6.0'),
                        'supports_delivery': True,
                        'is_primary': True
                    }
                ],
                'managers': [
                    {
                        'first_name': 'Mansi',
                        'last_name': 'Kulkarni',
                        'email': 'mansi@vegancolab.in',
                        'phone': '+91 99777 88991',
                        'role': ManagerProfile.ManagerRole.OPERATIONS,
                        'is_primary': True
                    }
                ]
            }
        ]
        
        # Create restaurants and menus
        for seed_data in restaurants_seed_data:
            owner = seed_data['owner']
            restaurant_data = seed_data['restaurant']
            menu_data = seed_data['menu']
            
            restaurant, restaurant_created = Restaurant.objects.get_or_create(
                owner=owner,
                name=restaurant_data['name'],
                defaults=restaurant_data
            )
            
            if restaurant_created:
                self.stdout.write(f'Created restaurant: {restaurant.name}')
            else:
                self.stdout.write(f'Restaurant already exists: {restaurant.name}')
                # Update existing restaurant
                for key, value in restaurant_data.items():
                    setattr(restaurant, key, value)
                restaurant.save()
            
            RestaurantSettings.objects.get_or_create(
                restaurant=restaurant,
                defaults={
                    'default_prep_time_minutes': restaurant_data.get('estimated_preparation_time', 20),
                    'max_delivery_distance_km': restaurant_data.get('delivery_radius_km', Decimal('5.0')),
                    'is_online': True,
                    'sla_threshold_minutes': 35,
                    'delivery_radius_settings': {
                        'default': float(restaurant_data.get('delivery_radius_km', Decimal('5.0')))
                    },
                }
            )

            for branch_data in seed_data.get('branches', []):
                branch_defaults = branch_data.copy()
                RestaurantBranch.objects.get_or_create(
                    restaurant=restaurant,
                    name=branch_defaults.pop('name'),
                    defaults=branch_defaults
                )

            for manager_data in seed_data.get('managers', []):
                manager_defaults = manager_data.copy()
                email = manager_defaults.pop('email', None)
                if not email:
                    email = f"{manager_defaults['first_name'].lower()}@{restaurant.name.lower().replace(' ', '')}.in"
                ManagerProfile.objects.get_or_create(
                    restaurant=restaurant,
                    email=email,
                    defaults=manager_defaults
                )

            # Create menu
            menu, menu_created = Menu.objects.get_or_create(
                restaurant=restaurant,
                name=menu_data['name'],
                defaults={
                    'description': menu_data.get('description', ''),
                    'is_active': True
                }
            )
            
            if menu_created:
                self.stdout.write(f'Created menu: {menu.name}')
            
            # Create categories and items
            for category_data in menu_data.get('categories', []):
                category, cat_created = MenuCategory.objects.get_or_create(
                    menu=menu,
                    name=category_data['name'],
                    defaults={
                        'description': category_data.get('description', ''),
                        'display_order': category_data.get('display_order', 0),
                        'is_active': True
                    }
                )
                
                if cat_created:
                    self.stdout.write(f'Created category: {category.name}')
                
                # Create menu items
                for item_data in category_data.get('items', []):
                    modifiers = item_data.pop('modifiers', [])
                    
                    # Try to get existing item, or create new one
                    item, item_created = MenuItem.objects.get_or_create(
                        category=category,
                        name=item_data['name'],
                        defaults={
                            'description': item_data.get('description', ''),
                            'price': item_data['price'],
                            'image_url': item_data.get('image_url', ''),
                            'is_available': True,
                            'is_deleted': False,
                            'preparation_time_minutes': item_data.get('preparation_time_minutes', 15),
                            'is_vegetarian': item_data.get('is_vegetarian', False),
                            'is_vegan': item_data.get('is_vegan', False),
                            'is_spicy': item_data.get('is_spicy', False),
                            'display_order': item_data.get('display_order', 0)
                        }
                    )
                    
                    # Update existing item to ensure it has latest data and is not deleted
                    if not item_created:
                        item.description = item_data.get('description', item.description)
                        item.price = item_data['price']
                        item.image_url = item_data.get('image_url', item.image_url)
                        item.is_available = True
                        item.is_deleted = False
                        item.preparation_time_minutes = item_data.get('preparation_time_minutes', item.preparation_time_minutes)
                        item.is_vegetarian = item_data.get('is_vegetarian', False)
                        item.is_vegan = item_data.get('is_vegan', False)
                        item.is_spicy = item_data.get('is_spicy', False)
                        item.display_order = item_data.get('display_order', item.display_order)
                        item.save()
                        self.stdout.write(f'Updated item: {item.name}')
                    else:
                        self.stdout.write(f'Created item: {item.name}')
                    
                    # Create modifiers
                    for mod_data in modifiers:
                        ItemModifier.objects.get_or_create(
                            menu_item=item,
                            name=mod_data['name'],
                            defaults={
                                'type': mod_data['type'],
                                'price': mod_data['price'],
                                'is_available': True,
                                'is_deleted': False
                            }
                        )
        
        # Seed Promotions (Offers)
        self.stdout.write('Seeding promotions...')
        promo_data = [
            {
                'name': 'Welcome Offer',
                'code': 'WELCOME50',
                'description': 'Get 50% off on your first order',
                'discount_type': Promotion.DiscountType.PERCENTAGE,
                'discount_value': Decimal('50.00'),
                'minimum_order_amount': Decimal('200.00'),
                'maximum_discount': Decimal('150.00'),
                'valid_from': timezone.now() - timezone.timedelta(days=1),
                'valid_until': timezone.now() + timezone.timedelta(days=30),
                'offer_type': Promotion.OfferType.PLATFORM,
                'priority': 10
            },
            {
                'name': 'Free Delivery',
                'code': 'FREEDEL',
                'description': 'Free delivery on orders above ₹500',
                'discount_type': Promotion.DiscountType.FREE_DELIVERY,
                'discount_value': Decimal('0.00'),
                'minimum_order_amount': Decimal('500.00'),
                'valid_from': timezone.now() - timezone.timedelta(days=1),
                'valid_until': timezone.now() + timezone.timedelta(days=30),
                'offer_type': Promotion.OfferType.PLATFORM,
                'priority': 5
            }
        ]
        
        for p_data in promo_data:
            Promotion.objects.get_or_create(
                code=p_data['code'],
                defaults=p_data
            )

        # Restaurant specific promotions
        pizza_palace = Restaurant.objects.filter(name='Pizza Palace Mumbai').first()
        if pizza_palace:
            Promotion.objects.get_or_create(
                code='PIZZA20',
                defaults={
                    'restaurant': pizza_palace,
                    'name': 'Pizza Party',
                    'description': 'Flat 20% off on all pizzas',
                    'discount_type': Promotion.DiscountType.PERCENTAGE,
                    'discount_value': Decimal('20.00'),
                    'minimum_order_amount': Decimal('400.00'),
                    'valid_from': timezone.now() - timezone.timedelta(days=1),
                    'valid_until': timezone.now() + timezone.timedelta(days=30),
                    'offer_type': Promotion.OfferType.RESTAURANT
                }
            )

        # Seed Wallet
        self.stdout.write('Seeding wallet...')
        wallet, _ = Wallet.objects.get_or_create(
            user=customer,
            defaults={'balance': Decimal('1500.00')}
        )
        
        # Add some transactions if wallet was just created or has no transactions
        if not WalletTransaction.objects.filter(wallet=wallet).exists():
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type=WalletTransaction.TransactionType.CREDIT,
                source=WalletTransaction.TransactionSource.ADD_MONEY,
                amount=Decimal('1000.00'),
                balance_after=Decimal('1000.00'),
                description='Added money to wallet',
                gateway_transaction_id='txn_123456'
            )
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type=WalletTransaction.TransactionType.CREDIT,
                source=WalletTransaction.TransactionSource.CASHBACK,
                amount=Decimal('500.00'),
                balance_after=Decimal('1500.00'),
                description='Cashback from order #ORD-9988'
            )

        # Seed Membership Plans
        self.stdout.write('Seeding membership plans...')
        gold_plan, _ = MembershipPlan.objects.get_or_create(
            name='PlatePal Gold',
            plan_type=MembershipPlan.PlanType.MONTHLY,
            defaults={
                'price': Decimal('199.00'),
                'description': 'Free delivery on all orders above ₹199',
                'benefits': {
                    'free_delivery': True,
                    'free_delivery_threshold': 199,
                    'priority_support': False
                },
                'duration_days': 30,
                'is_featured': False
            }
        )
        
        platinum_plan, _ = MembershipPlan.objects.get_or_create(
            name='PlatePal Platinum',
            plan_type=MembershipPlan.PlanType.YEARLY,
            defaults={
                'price': Decimal('1499.00'),
                'description': 'Free delivery, 5% extra discount, and priority support',
                'benefits': {
                    'free_delivery': True,
                    'free_delivery_threshold': 0,
                    'discount_percentage': 5,
                    'priority_support': True
                },
                'duration_days': 365,
                'is_featured': True
            }
        )

        # Subscribe customer to Gold plan
        if not Subscription.objects.filter(user=customer, status=Subscription.Status.ACTIVE).exists():
            Subscription.objects.create(
                user=customer,
                plan=gold_plan,
                status=Subscription.Status.ACTIVE,
                start_date=timezone.now(),
                end_date=timezone.now() + timezone.timedelta(days=30),
                payment_transaction_id='sub_txn_778899',
                auto_renew=True
            )

        # Seed Loyalty/Rewards
        self.stdout.write('Seeding loyalty tiers...')
        tiers = [
            {'name': 'Bronze', 'level': 1, 'min_points': 0, 'benefits': {'multiplier': 1.0}},
            {'name': 'Silver', 'level': 2, 'min_points': 1000, 'benefits': {'multiplier': 1.2}},
            {'name': 'Gold', 'level': 3, 'min_points': 5000, 'benefits': {'multiplier': 1.5, 'priority_support': True}},
            {'name': 'Platinum', 'level': 4, 'min_points': 10000, 'benefits': {'multiplier': 2.0, 'exclusive_access': True}},
        ]
        
        for tier_data in tiers:
            LoyaltyTier.objects.get_or_create(
                level=tier_data['level'],
                defaults={
                    'name': tier_data['name'],
                    'min_points': tier_data['min_points'],
                    'benefits': tier_data['benefits']
                }
            )

        # Give customer some points
        user_loyalty, _ = UserLoyalty.objects.get_or_create(user=customer)
        if user_loyalty.total_points == 0:
            points_to_add = 1250
            user_loyalty.total_points = points_to_add
            user_loyalty.available_points = points_to_add
            user_loyalty.lifetime_points_earned = points_to_add
            user_loyalty.update_tier()
            user_loyalty.save()
            
            RewardPoint.objects.create(
                user=customer,
                transaction_type=RewardPoint.TransactionType.EARNED,
                points=points_to_add,
                balance_after=points_to_add,
                description='Bonus points for joining'
            )

        # Seed Support Tickets
        self.stdout.write('Seeding support tickets...')
        if not SupportTicket.objects.filter(user=customer).exists():
            SupportTicket.objects.create(
                user=customer,
                ticket_number='TKT-2024-001',
                category=SupportTicket.Category.ORDER_ISSUE,
                subject='Item missing from order',
                description='I ordered 2 pizzas but only received 1.',
                status=SupportTicket.Status.RESOLVED,
                priority=SupportTicket.Priority.HIGH,
                created_at=timezone.now() - timezone.timedelta(days=5),
                resolved_at=timezone.now() - timezone.timedelta(days=4)
            )
            
            SupportTicket.objects.create(
                user=customer,
                ticket_number='TKT-2024-002',
                subject='Refund not received',
                description='My order was cancelled yesterday but I haven\'t received the refund yet.',
                status=SupportTicket.Status.OPEN,
                priority=SupportTicket.Priority.MEDIUM,
                created_at=timezone.now() - timezone.timedelta(hours=2)
            )

        # ==========================================
        # Seed Delivery Data
        # ==========================================
        self.stdout.write('Seeding delivery data...')

        # 1. Rider Profile & Onboarding
        RiderProfile.objects.get_or_create(
            rider=rider,
            defaults={
                'vehicle_type': 'BIKE',
                'vehicle_registration_number': 'MH-01-AB-1234',
                'vehicle_model': 'Honda Activa',
                'vehicle_color': 'White',
                'driver_license_number': 'DL-MH-2020-1234567',
                'emergency_contact_name': 'Jane Doe',
                'emergency_contact_phone': '+91 98765 20001',
                'emergency_contact_relationship': 'Spouse',
                'profile_completion_percentage': 100
            }
        )
        
        RiderBankDetail.objects.get_or_create(
            rider=rider,
            defaults={
                'bank_name': 'HDFC Bank',
                'account_holder_name': 'Delivery Rider',
                'account_number': '1234567890',
                'ifsc_code': 'HDFC0001234',
                'bank_branch': 'Mumbai Central',
                'is_verified': True,
                'verified_at': timezone.now()
            }
        )

        # 2. Wallet
        wallet, _ = RiderWallet.objects.get_or_create(
            rider=rider,
            defaults={'balance': Decimal('1500.00'), 'currency': 'INR'}
        )
        
        if not wallet.transactions.exists():
            RiderWalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='CREDIT',
                source='EARNINGS',
                amount=Decimal('500.00'),
                balance_after=Decimal('500.00'),
                description='Earnings for Order #123'
            )
            RiderWalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='CREDIT',
                source='BONUS',
                amount=Decimal('1000.00'),
                balance_after=Decimal('1500.00'),
                description='Joining Bonus'
            )

        # 3. Shifts
        # Active shift
        RiderShift.objects.get_or_create(
            rider=rider,
            status='ACTIVE',
            defaults={
                'scheduled_start': timezone.now() - timezone.timedelta(hours=4),
                'scheduled_end': timezone.now() + timezone.timedelta(hours=4),
                'actual_start': timezone.now() - timezone.timedelta(hours=2),
                'time_online_minutes': 120,
                'distance_traveled_km': Decimal('15.5'),
                'deliveries_completed': 2,
                'earnings_total': Decimal('250.00')
            }
        )
        
        # Past shift
        RiderShift.objects.get_or_create(
            rider=rider,
            status='COMPLETED',
            actual_start=timezone.now() - timezone.timedelta(days=1, hours=8),
            defaults={
                'scheduled_start': timezone.now() - timezone.timedelta(days=1, hours=8),
                'scheduled_end': timezone.now() - timezone.timedelta(days=1),
                'actual_end': timezone.now() - timezone.timedelta(days=1),
                'time_online_minutes': 480,
                'distance_traveled_km': Decimal('45.2'),
                'deliveries_completed': 8,
                'earnings_total': Decimal('1200.00')
            }
        )

        # 4. Orders & Deliveries
        # We need a restaurant for orders. Use 'Spice Garden' (first one usually)
        restaurant = Restaurant.objects.first()
        if not restaurant:
            self.stdout.write('No restaurant found, skipping delivery orders seeding.')
        else:
            # Past Delivered Order
            order_delivered, created = Order.objects.get_or_create(
                order_number=f'ORD-{timezone.now().strftime("%Y%m%d")}-9001',
                defaults={
                    'customer': customer,
                    'restaurant': restaurant,
                    'total_amount': Decimal('500.00'),
                    'status': 'DELIVERED',
                    'delivery_address': address
                }
            )
            if created:
                delivery_past = Delivery.objects.create(
                    order=order_delivered,
                    rider=rider,
                    pickup_address=restaurant.address,
                    delivery_address=address,
                    status='DELIVERED',
                    base_fee=Decimal('40.00'),
                    distance_fee=Decimal('10.00'),
                    tip_amount=Decimal('20.00'),
                    total_earnings=Decimal('70.00'),
                    actual_pickup_time=timezone.now() - timezone.timedelta(hours=2),
                    actual_delivery_time=timezone.now() - timezone.timedelta(hours=1, minutes=30)
                )
                RiderEarnings.objects.create(
                    rider=rider,
                    delivery=delivery_past,
                    base_fee=Decimal('40.00'),
                    distance_fee=Decimal('10.00'),
                    tip_amount=Decimal('20.00'),
                    total_amount=Decimal('70.00'),
                    payout_period_start=timezone.now().date(),
                    payout_period_end=timezone.now().date() + timezone.timedelta(days=7)
                )

            # Active Delivery (In Transit)
            order_active, created = Order.objects.get_or_create(
                order_number=f'ORD-{timezone.now().strftime("%Y%m%d")}-9002',
                defaults={
                    'customer': customer,
                    'restaurant': restaurant,
                    'total_amount': Decimal('750.00'),
                    'status': 'OUT_FOR_DELIVERY',
                    'delivery_address': address
                }
            )
            if created:
                Delivery.objects.create(
                    order=order_active,
                    rider=rider,
                    pickup_address=restaurant.address,
                    delivery_address=address,
                    status='IN_TRANSIT',
                    base_fee=Decimal('50.00'),
                    distance_fee=Decimal('15.00'),
                    total_earnings=Decimal('65.00'),
                    actual_pickup_time=timezone.now() - timezone.timedelta(minutes=15),
                    estimated_delivery_time=timezone.now() + timezone.timedelta(minutes=10)
                )

            # Offer (Pending)
            order_offer, created = Order.objects.get_or_create(
                order_number=f'ORD-{timezone.now().strftime("%Y%m%d")}-9003',
                defaults={
                    'customer': customer,
                    'restaurant': restaurant,
                    'total_amount': Decimal('300.00'),
                    'status': 'ASSIGNED',
                    'delivery_address': address
                }
            )
            if created:
                delivery_offer_obj = Delivery.objects.create(
                    order=order_offer,
                    pickup_address=restaurant.address,
                    delivery_address=address,
                    status='PENDING',
                    base_fee=Decimal('30.00'),
                    distance_fee=Decimal('5.00'),
                    total_earnings=Decimal('35.00')
                )
                DeliveryOffer.objects.create(
                    delivery=delivery_offer_obj,
                    rider=rider,
                    status='SENT',
                    estimated_earnings=Decimal('35.00'),
                    distance_km=Decimal('3.5'),
                    estimated_pickup_time=timezone.now() + timezone.timedelta(minutes=15),
                    estimated_drop_time=timezone.now() + timezone.timedelta(minutes=45),
                    expires_at=timezone.now() + timezone.timedelta(minutes=2)
                )



        self.stdout.write('Delivery data seeded successfully!')

        # ==========================================
        # Seed Restaurant-Specific Data
        # ==========================================
        self.stdout.write('Seeding restaurant-specific data...')

        # Get first restaurant for seeding
        restaurant = Restaurant.objects.filter(owner__email='restaurant@platepal.com').first()
        
        if restaurant:
            # 1. Inventory Data
            self.stdout.write('Seeding inventory data...')
            
            # Create inventory items
            tomatoes, _ = InventoryItem.objects.get_or_create(
                restaurant=restaurant,
                name='Tomatoes',
                defaults={
                    'sku': 'VEG-001',
                    'category': 'Vegetables',
                    'unit': 'KG',
                    'current_stock': Decimal('25.00'),
                    'reorder_level': Decimal('10.00'),
                    'low_stock_threshold': Decimal('5.00'),
                    'max_capacity': Decimal('100.00')
                }
            )
            
            cheese, _ = InventoryItem.objects.get_or_create(
                restaurant=restaurant,
                name='Mozzarella Cheese',
                defaults={
                    'sku': 'DAIRY-001',
                    'category': 'Dairy',
                    'unit': 'KG',
                    'current_stock': Decimal('3.50'),
                    'reorder_level': Decimal('5.00'),
                    'low_stock_threshold': Decimal('2.00'),
                    'max_capacity': Decimal('20.00')
                }
            )
            
            flour, _ = InventoryItem.objects.get_or_create(
                restaurant=restaurant,
                name='Pizza Flour',
                defaults={
                    'sku': 'GRAIN-001',
                    'category': 'Grains',
                    'unit': 'KG',
                    'current_stock': Decimal('45.00'),
                    'reorder_level': Decimal('20.00'),
                    'low_stock_threshold': Decimal('10.00'),
                    'max_capacity': Decimal('200.00')
                }
            )
            
            olive_oil, _ = InventoryItem.objects.get_or_create(
                restaurant=restaurant,
                name='Olive Oil',
                defaults={
                    'sku': 'OIL-001',
                    'category': 'Oils',
                    'unit': 'L',
                    'current_stock': Decimal('8.00'),
                    'reorder_level': Decimal('5.00'),
                    'low_stock_threshold': Decimal('3.00'),
                    'max_capacity': Decimal('50.00')
                }
            )
            
            # Create stock movements
            StockMovement.objects.get_or_create(
                inventory_item=tomatoes,
                movement_type='INBOUND',
                defaults={
                    'quantity': Decimal('50.00'),
                    'unit_cost': Decimal('2.50'),
                    'notes': 'Weekly stock replenishment'
                }
            )
            
            StockMovement.objects.get_or_create(
                inventory_item=cheese,
                movement_type='OUTBOUND',
                defaults={
                    'quantity': Decimal('1.50'),
                    'unit_cost': Decimal('12.00'),
                    'notes': 'Used for pizza orders'
                }
            )
            
            # 2. Reviews Data
            self.stdout.write('Seeding reviews data...')
            
            # Get some completed orders
            completed_orders = Order.objects.filter(
                restaurant=restaurant,
                status='DELIVERED'
            )[:3]
            
            for idx, order in enumerate(completed_orders):
                review, created = Review.objects.get_or_create(
                    order=order,
                    defaults={
                        'customer': order.customer,
                        'restaurant': restaurant,
                        'rating': 4 + (idx % 2),  # 4 or 5 stars
                        'comment': [
                            'Amazing food! The pizza was delicious and arrived hot.',
                            'Great service and tasty food. Will order again!',
                            'Excellent quality and fast delivery. Highly recommended!'
                        ][idx],
                        'delivery_rating': 5,
                        'food_rating': 4 + (idx % 2),
                        'packaging_rating': 5
                    }
                )
                
                if created:
                    # Add item reviews
                    order_items = order.items.all()[:2]
                    for item in order_items:
                        ItemReview.objects.get_or_create(
                            review=review,
                            menu_item=item.menu_item,
                            defaults={
                                'rating': 4 + (idx % 2),
                                'comment': 'Delicious!'
                            }
                        )
            
            # 3. Finance Data (Settlements & Payouts)
            self.stdout.write('Seeding finance data...')
            
            # Create settlement cycles
            settlement, _ = SettlementCycle.objects.get_or_create(
                restaurant=restaurant,
                cycle_start=timezone.now() - timezone.timedelta(days=7),
                cycle_end=timezone.now(),
                defaults={
                    'total_sales': Decimal('15000.00'),
                    'commission_amount': Decimal('3000.00'),
                    'packaging_fee': Decimal('500.00'),
                    'delivery_fee_share': Decimal('1000.00'),
                    'tax_amount': Decimal('1500.00'),
                    'net_payout': Decimal('9000.00'),
                    'status': 'COMPLETED',
                    'processed_at': timezone.now() - timezone.timedelta(days=1),
                    'payout_reference': 'PAY-2024-001'
                }
            )
            
            # Create payout
            Payout.objects.get_or_create(
                settlement=settlement,
                restaurant=restaurant,
                defaults={
                    'amount': Decimal('9000.00'),
                    'bank_account_number': '****1234',
                    'bank_ifsc_code': 'HDFC0001234',
                    'bank_name': 'HDFC Bank',
                    'account_holder_name': restaurant.name,
                    'status': 'COMPLETED',
                    'initiated_at': timezone.now() - timezone.timedelta(days=1),
                    'processed_at': timezone.now() - timezone.timedelta(hours=12),
                    'utr_number': 'UTR202400001234'
                }
            )
            
            # Pending settlement
            SettlementCycle.objects.get_or_create(
                restaurant=restaurant,
                cycle_start=timezone.now() - timezone.timedelta(days=1),
                cycle_end=timezone.now() + timezone.timedelta(days=6),
                defaults={
                    'total_sales': Decimal('2500.00'),
                    'commission_amount': Decimal('500.00'),
                    'packaging_fee': Decimal('100.00'),
                    'delivery_fee_share': Decimal('200.00'),
                    'tax_amount': Decimal('250.00'),
                    'net_payout': Decimal('1450.00'),
                    'status': 'PENDING'
                }
            )
            
            # 4. Enhanced KDS Data (Active Orders)
            self.stdout.write('Seeding KDS active orders...')
            
            # Create orders in different KDS stages
            # PENDING = new orders, PREPARING = being prepared, READY = ready for pickup
            kds_statuses = ['PENDING', 'PREPARING', 'READY']
            
            for idx, status in enumerate(kds_statuses):
                order, created = Order.objects.get_or_create(
                    order_number=f'KDS-{timezone.now().strftime("%Y%m%d")}-{idx+1:03d}',
                    defaults={
                        'customer': customer,
                        'restaurant': restaurant,
                        'status': status,
                        'total_amount': Decimal('450.00') + (idx * 100),
                        'delivery_address': address,
                        'special_instructions': 'Extra cheese' if idx == 0 else ''
                    }
                )
                
                if created:
                    # Add order items - get menu items through the menu relationship
                    menu = restaurant.menus.first()
                    if menu:
                        menu_items = MenuItem.objects.filter(category__menu=menu)[:2]
                        for item in menu_items:
                            OrderItem.objects.create(
                                order=order,
                                menu_item=item,
                                name=item.name,
                                description=item.description,
                                quantity=1 + idx,
                                unit_price=item.price,
                                total_price=item.price * (1 + idx),
                                selected_modifiers=[
                                    {'name': 'Extra Cheese', 'price': '2.00'},
                                    {'name': 'Spicy', 'price': '0.00'}
                                ] if idx == 0 else []
                            )
            
            self.stdout.write('Restaurant-specific data seeded successfully!')
        else:
            self.stdout.write('No restaurant found for seeding restaurant-specific data.')

        # ==========================================
        # Seed Admin Dashboard Data
        # ==========================================
        self.stdout.write('Seeding admin dashboard data...')

        # 1. Roles & Permissions
        super_admin_role, _ = Role.objects.get_or_create(
            name='Super Admin',
            defaults={'description': 'Full access to all resources', 'is_system': True}
        )
        support_role, _ = Role.objects.get_or_create(
            name='Support Agent',
            defaults={'description': 'Access to user support and order management'}
        )
        moderator_role, _ = Role.objects.get_or_create(
            name='Content Moderator',
            defaults={'description': 'Access to reviews and content moderation'}
        )

        # Assign role to admin user
        admin_profile, created = AdminUser.objects.get_or_create(
            user=admin,
            defaults={'role': super_admin_role}
        )
        if not created and not admin_profile.role:
            admin_profile.role = super_admin_role
            admin_profile.save()

        # 2. Operations Data
        # System Health Metrics
        services = ['API Gateway', 'Database', 'Cache', 'Payment Service', 'Notification Service']
        metrics = ['cpu_usage', 'memory_usage', 'latency_ms', 'error_rate']
        
        for service in services:
            for metric in metrics:
                val = 0
                if metric == 'cpu_usage': val = 45.5
                elif metric == 'memory_usage': val = 62.3
                elif metric == 'latency_ms': val = 120.5
                elif metric == 'error_rate': val = 0.05
                
                SystemHealthMetric.objects.create(
                    service_name=service,
                    metric_type=metric,
                    value=val,
                    status='healthy'
                )

        # Incidents
        Incident.objects.create(
            title='Payment Gateway Latency',
            description='High latency observed in payment processing.',
            status=Incident.Status.RESOLVED,
            severity=Incident.Severity.MEDIUM,
            affected_services=['Payment Service'],
            reported_by=admin,
            resolved_at=timezone.now() - timezone.timedelta(days=2),
            resolved_by=admin,
            root_cause='Third-party provider outage',
            resolution='Failed over to backup provider'
        )
        Incident.objects.create(
            title='Search Indexing Delay',
            description='New restaurant items are taking longer to appear in search.',
            status=Incident.Status.OPEN,
            severity=Incident.Severity.LOW,
            affected_services=['Search Service'],
            reported_by=admin
        )

        # Maintenance Window
        MaintenanceWindow.objects.create(
            title='Database Upgrade',
            description='Upgrading primary database to latest version.',
            start_time=timezone.now() + timezone.timedelta(days=3),
            end_time=timezone.now() + timezone.timedelta(days=3, hours=2),
            affected_services=['All Services'],
            is_active=True,
            user_message='System will be under maintenance on Sunday 2 AM - 4 AM.'
        )

        # 3. Advanced Features
        # Feature Flags
        FeatureFlag.objects.get_or_create(
            name='new_checkout_flow',
            defaults={
                'description': 'Redesigned checkout experience',
                'is_enabled': True,
                'rollout_percentage': 50
            }
        )
        FeatureFlag.objects.get_or_create(
            name='dark_mode_beta',
            defaults={
                'description': 'Dark mode for web app',
                'is_enabled': False,
                'rollout_percentage': 0
            }
        )

        # Fraud Rules
        rule, _ = FraudDetectionRule.objects.get_or_create(
            name='High Value Order',
            defaults={
                'rule_type': 'transaction_amount',
                'action': 'flag',
                'risk_score_threshold': 80
            }
        )

        # Fraud Flag
        FraudFlag.objects.create(
            user=customer,
            risk_score=85,
            reason='Unusual high value order from new device',
            rule_triggered=rule,
            status='PENDING'
        )

        # Chargeback
        if 'order_delivered' in locals():
             # Get or create a payment method for the customer
             payment_method, _ = PaymentMethod.objects.get_or_create(
                 user=customer,
                 type='CARD',
                 defaults={
                     'last_four': '4242',
                     'provider': 'Visa',
                     'is_default': True
                 }
             )

             if not Chargeback.objects.filter(chargeback_id='CB-2024-001').exists():
                 Chargeback.objects.create(
                    order=order_delivered,
                    payment=Payment.objects.create(  # Create dummy payment for chargeback
                        order=order_delivered,
                        user=customer,
                        amount=order_delivered.total_amount,
                        payment_method=payment_method,
                        method_type='CARD',
                        status='COMPLETED',
                        transaction_id=f'TXN-{timezone.now().strftime("%Y%m%d")}-CB'
                    ),
                    chargeback_id='CB-2024-001',
                    reason='Item not received',
                    amount=order_delivered.total_amount,
                    status=Chargeback.Status.UNDER_REVIEW,
                    received_date=timezone.now() - timezone.timedelta(days=1),
                    due_date=timezone.now() + timezone.timedelta(days=14)
                )

        # 4. Automation
        AutomationRule.objects.get_or_create(
            name='Auto-Refund Cancelled Orders',
            defaults={
                'trigger_type': 'EVENT',
                'action_type': 'REFUND',
                'is_active': True,
                'description': 'Automatically process refund when order is cancelled by restaurant'
            }
        )

        ScheduledJob.objects.get_or_create(
            name='Daily Settlement Run',
            defaults={
                'job_type': 'settlement_run',
                'cron_expression': '0 2 * * *',
                'status': 'PENDING',
                'next_run_at': timezone.now() + timezone.timedelta(hours=12)
            }
        )

        # 5. Audit Logs
        AuditLogEntry.objects.create(
            user=admin,
            action='user.ban',
            resource_type='user',
            resource_id=str(rider.id),
            reason='Violation of terms',
            ip_address='192.168.1.100'
        )
        AuditLogEntry.objects.create(
            user=admin,
            action='restaurant.approve',
            resource_type='restaurant',
            resource_id='1',
            ip_address='192.168.1.100'
        )

        self.stdout.write('Admin dashboard data seeded successfully!')

        self.stdout.write(self.style.SUCCESS('Successfully seeded database'))
        self.stdout.write('Test Accounts:')
        self.stdout.write('  Admin: admin@platepal.com / admin123')
        self.stdout.write('  Restaurant: restaurant@platepal.com / restaurant123')
        self.stdout.write('  Customer: customer@platepal.com / customer123')
        self.stdout.write('  Rider: rider@platepal.com / rider123')
        self.stdout.write('\nMumbai Restaurant accounts:')
        self.stdout.write(f'  Pizza Palace Mumbai: restaurant@platepal.com / restaurant123')
        self.stdout.write(f'  Mumbai Masala House: mumbai@platepal.com / masala123')
        self.stdout.write(f'  Sakura Sushi Bar: sakura@platepal.com / sakura123')
        self.stdout.write(f'  Bangkok Express: thai@platepal.com / thai123')
        self.stdout.write('\nBangalore Restaurant accounts:')
        self.stdout.write(f'  Kora Smokehouse (Koramangala): koramangala@platepal.com / bangalore123')
        self.stdout.write(f'  Indiranagar Green Bowl (Indiranagar): indiranagar@platepal.com / indira123')
        self.stdout.write(f'  MG Road Spice Studio (MG Road): bangalore@platepal.com / bangalore123')
        self.stdout.write(f'  Whitefield Vegan CoLab (Whitefield): whitefield@platepal.com / white123')

