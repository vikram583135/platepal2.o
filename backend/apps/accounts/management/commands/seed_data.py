"""
Seed data command for development
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.restaurants.models import (
    Restaurant,
    Menu,
    MenuCategory,
    MenuItem,
    ItemModifier,
    RestaurantSettings,
    RestaurantBranch,
    ManagerProfile,
)
from apps.accounts.models import Address, PaymentMethod, SavedLocation
from decimal import Decimal

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
                                    'image_url': 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=600&q=80',
                                    'is_spicy': True
                                },
                                {
                                    'name': 'Paneer Lababdar',
                                    'description': 'Malai paneer, roasted cashew paste, brown onion masala and kasuri methi smoke.',
                                    'price': Decimal('439.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1608039829570-0d5cec3f9a96?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True
                                },
                                {
                                    'name': 'Coastal Prawn Moilee',
                                    'description': 'Coconut milk curry perfumed with curry leaves, kokum and ginger, served with appam.',
                                    'price': Decimal('529.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=600&q=80',
                                    'is_spicy': True
                                },
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
                                    'image_url': 'https://images.unsplash.com/photo-1608039829570-0d5cec3f9a96?auto=format&fit=crop&w=600&q=80',
                                    'is_spicy': True
                                },
                                {
                                    'name': 'Paneer Tikka',
                                    'description': 'Cubes of paneer marinated in yogurt and spices, grilled to perfection.',
                                    'price': Decimal('389.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1608039829570-0d5cec3f9a96?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True
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
                                    'image_url': 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=600&q=80',
                                    'is_spicy': True,
                                    'preparation_time_minutes': 35
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
                                    'image_url': 'https://images.unsplash.com/photo-1579584425555-c3ce17fd4351?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 8
                                },
                                {
                                    'name': 'Tuna Sashimi (6 pcs)',
                                    'description': 'Premium bluefin tuna, wasabi and soy sauce.',
                                    'price': Decimal('899.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1579584425555-c3ce17fd4351?auto=format&fit=crop&w=600&q=80',
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
                                    'image_url': 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 15
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
                                    'image_url': 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 22
                                },
                                {
                                    'name': 'BBQ Jackfruit Bowl',
                                    'description': 'Tamarind glazed jackfruit, pickled veggies, millet rice.',
                                    'price': Decimal('429.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1529042410759-befb1204b468?auto=format&fit=crop&w=600&q=80',
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 18
                                },
                                {
                                    'name': 'Smoky Lamb Nihari Bowl',
                                    'description': 'Wood-smoked lamb, saffron rice, roasted garlic yogurt, crispy onions.',
                                    'price': Decimal('539.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1505253758473-96b7015fcd40?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 24
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
                                    'is_spicy': True,
                                    'preparation_time_minutes': 15
                                },
                                {
                                    'name': 'Loaded Peri Fries',
                                    'description': 'Twice cooked fries, peri-peri dust, garlic aioli.',
                                    'price': Decimal('249.00'),
                                    'is_vegetarian': True
                                },
                                {
                                    'name': 'Bonfire Paneer Tikka',
                                    'description': 'Smoked malai paneer skewers, chilli butter baste, pickled onions.',
                                    'price': Decimal('369.00'),
                                    'image_url': 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=600&q=80',
                                    'preparation_time_minutes': 16
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
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 15
                                },
                                {
                                    'name': 'Thai Peanut Tempeh Bowl',
                                    'description': 'Barnyard millet, tempeh, peanut satay, microgreens.',
                                    'price': Decimal('399.00'),
                                    'is_vegetarian': True,
                                    'is_spicy': True,
                                    'preparation_time_minutes': 17
                                },
                                {
                                    'name': 'Smoked Beet & Quinoa Bowl',
                                    'description': 'Red quinoa, smoked beets, pistachio crunch, kokum dressing.',
                                    'price': Decimal('389.00'),
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 15
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
                                    'is_vegetarian': True
                                },
                                {
                                    'name': 'Turmeric Glow Jar',
                                    'description': 'Mango, turmeric, coconut yogurt, toasted seeds.',
                                    'price': Decimal('309.00'),
                                    'is_vegetarian': True
                                },
                                {
                                    'name': 'Espresso Almond Crunch',
                                    'description': 'Cold brew, soaked almonds, cacao nib crumble.',
                                    'price': Decimal('319.00'),
                                    'is_vegetarian': True
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
                                    'is_vegetarian': True,
                                    'preparation_time_minutes': 12
                                },
                                {
                                    'name': 'Malai Chicken Slayer',
                                    'description': 'Cream cheese marinated chicken, smoked chili oil, millet crisps.',
                                    'price': Decimal('429.00'),
                                    'preparation_time_minutes': 15
                                },
                                {
                                    'name': 'Gunpowder Crab Cakes',
                                    'description': 'Pepper crust, coconut chutney espuma, radish salad.',
                                    'price': Decimal('489.00'),
                                    'preparation_time_minutes': 14
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
                                    'is_spicy': True
                                },
                                {
                                    'name': 'Malabar Pumpkin Stew',
                                    'description': 'Coconut milk, curry leaf tadka, jackfruit chips.',
                                    'price': Decimal('379.00'),
                                    'is_vegetarian': True
                                },
                                {
                                    'name': 'Lucknowi Nihari Pot',
                                    'description': 'Slow-cooked mutton, saffron sheermal shards, pickled onions.',
                                    'price': Decimal('549.00'),
                                    'is_spicy': True
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
                                    'is_vegetarian': True
                                },
                                {
                                    'name': 'Dragonfruit Crunch',
                                    'description': 'Pitaya, coconut kefir, granola shards.',
                                    'price': Decimal('339.00'),
                                    'is_vegetarian': True
                                },
                                {
                                    'name': 'Mint Julep Bowl',
                                    'description': 'Spearmint, lime zest chia pudding, roasted cashews.',
                                    'price': Decimal('329.00'),
                                    'is_vegetarian': True
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
                                    'is_vegetarian': True
                                },
                                {
                                    'name': 'Keto Tofu Crunch',
                                    'description': 'Baked tofu, activated seeds, avocado tahini.',
                                    'price': Decimal('309.00'),
                                    'is_vegetarian': True
                                },
                                {
                                    'name': 'Harissa Chickpea Salad',
                                    'description': 'Warm chickpeas, harissa oil, crispy kale, citrus dressing.',
                                    'price': Decimal('289.00'),
                                    'is_spicy': True,
                                    'is_vegetarian': True
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
                    item, item_created = MenuItem.objects.get_or_create(
                        category=category,
                        name=item_data['name'],
                        defaults={
                            'description': item_data.get('description', ''),
                            'price': item_data['price'],
                            'image_url': item_data.get('image_url', ''),
                            'is_available': True,
                            'preparation_time_minutes': item_data.get('preparation_time_minutes', 15),
                            'is_vegetarian': item_data.get('is_vegetarian', False),
                            'is_vegan': item_data.get('is_vegan', False),
                            'is_spicy': item_data.get('is_spicy', False),
                            'display_order': item_data.get('display_order', 0)
                        }
                    )
                    
                    if item_created:
                        self.stdout.write(f'Created item: {item.name}')
                    
                    # Create modifiers
                    for mod_data in modifiers:
                        ItemModifier.objects.get_or_create(
                            menu_item=item,
                            name=mod_data['name'],
                            defaults={
                                'type': mod_data['type'],
                                'price': mod_data['price'],
                                'is_available': True
                            }
                        )
        
        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
        self.stdout.write('\nTest accounts:')
        self.stdout.write(f'  Admin: admin@platepal.com / admin123')
        self.stdout.write(f'  Customer: customer@platepal.com / customer123')
        self.stdout.write(f'  Rider: rider@platepal.com / rider123')
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

