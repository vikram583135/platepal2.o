"""
Management command to complete onboarding for all listed restaurants
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from apps.restaurants.models import (
    Restaurant,
    RestaurantSettings,
    RestaurantDocument,
    RestaurantBranch,
    ManagerProfile,
)

User = get_user_model()

# Restaurant data mapping from credentials file
RESTAURANT_DATA = {
    'restaurant@platepal.com': {
        'name': 'Pizza Palace Mumbai',
        'description': 'Authentic Italian pizzas with wood-fired ovens and fresh ingredients.',
        'cuisine_type': Restaurant.CuisineType.ITALIAN,
        'cuisine_types': [Restaurant.CuisineType.ITALIAN],
        'restaurant_type': Restaurant.RestaurantType.NON_VEG,
        'phone': '+91 98201 11111',
        'email': 'contact@pizzapalace.in',
        'latitude': Decimal('18.9220'),  # Colaba Causeway, Mumbai
        'longitude': Decimal('72.8347'),
        'address': 'Colaba Causeway, Colaba',
        'city': 'Mumbai',
        'state': 'Maharashtra',
        'postal_code': '400005',
        'country': 'India',
        'manager_contact_name': 'Rajesh Kumar',
        'manager_contact_phone': '+91 98201 11112',
        'manager_contact_email': 'manager@pizzapalace.in',
        'support_phone': '+91 98201 11113',
        'support_email': 'support@pizzapalace.in',
        'fssai_license_number': 'FSSAI123456789',
        'gst_number': '27AABCU9603R1ZX',
        'bank_account_number': '1234567890123456',
        'bank_ifsc_code': 'HDFC0001234',
        'is_pure_veg': False,
        'cost_for_two': Decimal('800.00'),
        'minimum_order_amount': Decimal('299.00'),
        'delivery_radius_km': Decimal('8.00'),
        'estimated_preparation_time': 25,
    },
    'mumbai@platepal.com': {
        'name': 'Mumbai Masala House',
        'description': 'Comforting curries simmered overnight in copper pots with stone ground spices.',
        'cuisine_type': Restaurant.CuisineType.INDIAN,
        'cuisine_types': [Restaurant.CuisineType.INDIAN],
        'restaurant_type': Restaurant.RestaurantType.NON_VEG,
        'phone': '+91 98201 22334',
        'email': 'table@mumbaimasala.in',
        'latitude': Decimal('19.0760'),  # Fort, Mumbai
        'longitude': Decimal('72.8777'),
        'address': '7 Residency Road, Fort',
        'city': 'Mumbai',
        'state': 'Maharashtra',
        'postal_code': '400001',
        'country': 'India',
        'manager_contact_name': 'Priya Sharma',
        'manager_contact_phone': '+91 98201 22335',
        'manager_contact_email': 'manager@mumbaimasala.in',
        'support_phone': '+91 98201 22336',
        'support_email': 'support@mumbaimasala.in',
        'fssai_license_number': 'FSSAI234567890',
        'gst_number': '27BBCCU9604R1ZY',
        'bank_account_number': '2345678901234567',
        'bank_ifsc_code': 'ICIC0002345',
        'is_pure_veg': False,
        'cost_for_two': Decimal('600.00'),
        'minimum_order_amount': Decimal('399.00'),
        'delivery_radius_km': Decimal('10.00'),
        'estimated_preparation_time': 28,
    },
    'sakura@platepal.com': {
        'name': 'Sakura Sushi Bar',
        'description': 'Fresh sushi and authentic Japanese cuisine with premium ingredients.',
        'cuisine_type': Restaurant.CuisineType.JAPANESE,
        'cuisine_types': [Restaurant.CuisineType.JAPANESE],
        'restaurant_type': Restaurant.RestaurantType.NON_VEG,
        'phone': '+91 98201 33445',
        'email': 'reservations@sakura.in',
        'latitude': Decimal('19.0596'),  # Bandra Kurla Complex, Mumbai
        'longitude': Decimal('72.8689'),
        'address': 'Bandra Kurla Complex, Bandra East',
        'city': 'Mumbai',
        'state': 'Maharashtra',
        'postal_code': '400051',
        'country': 'India',
        'manager_contact_name': 'Kenji Tanaka',
        'manager_contact_phone': '+91 98201 33446',
        'manager_contact_email': 'manager@sakura.in',
        'support_phone': '+91 98201 33447',
        'support_email': 'support@sakura.in',
        'fssai_license_number': 'FSSAI345678901',
        'gst_number': '27CCDDU9605R1ZZ',
        'bank_account_number': '3456789012345678',
        'bank_ifsc_code': 'AXIS0003456',
        'is_pure_veg': False,
        'cost_for_two': Decimal('1200.00'),
        'minimum_order_amount': Decimal('499.00'),
        'delivery_radius_km': Decimal('12.00'),
        'estimated_preparation_time': 30,
    },
    'thai@platepal.com': {
        'name': 'Bangkok Express',
        'description': 'Authentic Thai street food with bold flavors and fresh herbs.',
        'cuisine_type': Restaurant.CuisineType.THAI,
        'cuisine_types': [Restaurant.CuisineType.THAI],
        'restaurant_type': Restaurant.RestaurantType.NON_VEG,
        'phone': '+91 98201 44556',
        'email': 'orders@bangkokexpress.in',
        'latitude': Decimal('19.1364'),  # Andheri West, Mumbai
        'longitude': Decimal('72.8296'),
        'address': 'Andheri West, Andheri',
        'city': 'Mumbai',
        'state': 'Maharashtra',
        'postal_code': '400053',
        'country': 'India',
        'manager_contact_name': 'Sompong Chen',
        'manager_contact_phone': '+91 98201 44557',
        'manager_contact_email': 'manager@bangkokexpress.in',
        'support_phone': '+91 98201 44558',
        'support_email': 'support@bangkokexpress.in',
        'fssai_license_number': 'FSSAI456789012',
        'gst_number': '27DDEEU9606R1AA',
        'bank_account_number': '4567890123456789',
        'bank_ifsc_code': 'SBIN0004567',
        'is_pure_veg': False,
        'cost_for_two': Decimal('700.00'),
        'minimum_order_amount': Decimal('349.00'),
        'delivery_radius_km': Decimal('9.00'),
        'estimated_preparation_time': 22,
    },
    'koramangala@platepal.com': {
        'name': 'Kora Smokehouse',
        'description': 'BBQ and smoked meats with craft sauces and sides.',
        'cuisine_type': Restaurant.CuisineType.FAST_FOOD,
        'cuisine_types': [Restaurant.CuisineType.FAST_FOOD, Restaurant.CuisineType.AMERICAN],
        'restaurant_type': Restaurant.RestaurantType.NON_VEG,
        'phone': '+91 98765 11111',
        'email': 'orders@korasmokehouse.in',
        'latitude': Decimal('12.9352'),  # Koramangala, Bengaluru
        'longitude': Decimal('77.6245'),
        'address': 'Koramangala, Bengaluru',
        'city': 'Bengaluru',
        'state': 'Karnataka',
        'postal_code': '560095',
        'country': 'India',
        'manager_contact_name': 'Arjun Reddy',
        'manager_contact_phone': '+91 98765 11112',
        'manager_contact_email': 'manager@korasmokehouse.in',
        'support_phone': '+91 98765 11113',
        'support_email': 'support@korasmokehouse.in',
        'fssai_license_number': 'FSSAI567890123',
        'gst_number': '29AAFFU9607R1AB',
        'bank_account_number': '5678901234567890',
        'bank_ifsc_code': 'HDFC0005678',
        'is_pure_veg': False,
        'cost_for_two': Decimal('900.00'),
        'minimum_order_amount': Decimal('449.00'),
        'delivery_radius_km': Decimal('10.00'),
        'estimated_preparation_time': 30,
        'has_branches': True,
    },
    'indiranagar@platepal.com': {
        'name': 'Indiranagar Green Bowl',
        'description': 'Plant-forward kitchen with millet bowls and smoothie jars.',
        'cuisine_type': Restaurant.CuisineType.VEGETARIAN,
        'cuisine_types': [Restaurant.CuisineType.VEGETARIAN, Restaurant.CuisineType.MEDITERRANEAN],
        'restaurant_type': Restaurant.RestaurantType.PURE_VEG,
        'phone': '+91 98765 22222',
        'email': 'hello@greenbowl.in',
        'latitude': Decimal('12.9784'),  # Indiranagar, Bengaluru
        'longitude': Decimal('77.6408'),
        'address': '100 Feet Road, Indiranagar',
        'city': 'Bengaluru',
        'state': 'Karnataka',
        'postal_code': '560038',
        'country': 'India',
        'manager_contact_name': 'Ananya Patel',
        'manager_contact_phone': '+91 98765 22223',
        'manager_contact_email': 'manager@greenbowl.in',
        'support_phone': '+91 98765 22224',
        'support_email': 'support@greenbowl.in',
        'fssai_license_number': 'FSSAI678901234',
        'gst_number': '29BBGGU9608R1AC',
        'bank_account_number': '6789012345678901',
        'bank_ifsc_code': 'ICIC0006789',
        'is_pure_veg': True,
        'cost_for_two': Decimal('500.00'),
        'minimum_order_amount': Decimal('249.00'),
        'delivery_radius_km': Decimal('8.00'),
        'estimated_preparation_time': 20,
    },
    'bangalore@platepal.com': {
        'name': 'MG Road Spice Studio',
        'description': 'Progressive Indian tasting kitchen with modern twists.',
        'cuisine_type': Restaurant.CuisineType.INDIAN,
        'cuisine_types': [Restaurant.CuisineType.INDIAN, Restaurant.CuisineType.THAI],
        'restaurant_type': Restaurant.RestaurantType.NON_VEG,
        'phone': '+91 98765 33333',
        'email': 'reservations@spicestudio.in',
        'latitude': Decimal('12.9716'),  # MG Road, Bengaluru
        'longitude': Decimal('77.5946'),
        'address': 'MG Road, Bengaluru',
        'city': 'Bengaluru',
        'state': 'Karnataka',
        'postal_code': '560001',
        'country': 'India',
        'manager_contact_name': 'Vikram Singh',
        'manager_contact_phone': '+91 98765 33334',
        'manager_contact_email': 'manager@spicestudio.in',
        'support_phone': '+91 98765 33335',
        'support_email': 'support@spicestudio.in',
        'fssai_license_number': 'FSSAI789012345',
        'gst_number': '29CCHHU9609R1AD',
        'bank_account_number': '7890123456789012',
        'bank_ifsc_code': 'AXIS0007890',
        'is_pure_veg': False,
        'cost_for_two': Decimal('1000.00'),
        'minimum_order_amount': Decimal('499.00'),
        'delivery_radius_km': Decimal('12.00'),
        'estimated_preparation_time': 35,
    },
    'whitefield@platepal.com': {
        'name': 'Whitefield Vegan CoLab',
        'description': 'Plant-based commissary with smoothie bowls and salads.',
        'cuisine_type': Restaurant.CuisineType.VEGAN,
        'cuisine_types': [Restaurant.CuisineType.VEGAN, Restaurant.CuisineType.MEDITERRANEAN],
        'restaurant_type': Restaurant.RestaurantType.PURE_VEG,
        'phone': '+91 98765 44444',
        'email': 'hello@vegancolab.in',
        'latitude': Decimal('12.9698'),  # Whitefield, Bengaluru
        'longitude': Decimal('77.7499'),
        'address': 'ITPL Main Road, Whitefield',
        'city': 'Bengaluru',
        'state': 'Karnataka',
        'postal_code': '560066',
        'country': 'India',
        'manager_contact_name': 'Meera Krishnan',
        'manager_contact_phone': '+91 98765 44445',
        'manager_contact_email': 'manager@vegancolab.in',
        'support_phone': '+91 98765 44446',
        'support_email': 'support@vegancolab.in',
        'fssai_license_number': 'FSSAI890123456',
        'gst_number': '29DDIIU9610R1AE',
        'bank_account_number': '8901234567890123',
        'bank_ifsc_code': 'SBIN0008901',
        'is_pure_veg': True,
        'cost_for_two': Decimal('550.00'),
        'minimum_order_amount': Decimal('299.00'),
        'delivery_radius_km': Decimal('10.00'),
        'estimated_preparation_time': 18,
    },
}


class Command(BaseCommand):
    help = 'Complete onboarding for all listed restaurants'

    def handle(self, *args, **options):
        self.stdout.write('Completing onboarding for all restaurants...')
        
        updated_count = 0
        created_count = 0
        
        for owner_email, restaurant_data in RESTAURANT_DATA.items():
            try:
                # Find restaurant owner
                owner = User.objects.filter(email=owner_email, role=User.Role.RESTAURANT).first()
                if not owner:
                    self.stdout.write(self.style.WARNING(f'Owner not found: {owner_email}'))
                    continue
                
                # Get restaurant (handle multiple restaurants per owner)
                restaurants = Restaurant.objects.filter(owner=owner)
                if restaurants.count() > 1:
                    # If multiple, use the one matching the name or first one
                    restaurant = restaurants.filter(name=restaurant_data['name']).first()
                    if not restaurant:
                        restaurant = restaurants.first()
                    created = False
                elif restaurants.exists():
                    restaurant = restaurants.first()
                    created = False
                else:
                    restaurant = Restaurant.objects.create(
                        owner=owner,
                        name=restaurant_data['name']
                    )
                    created = True
                
                if created:
                    created_count += 1
                    self.stdout.write(f'Created restaurant: {restaurant.name}')
                else:
                    updated_count += 1
                    self.stdout.write(f'Updating restaurant: {restaurant.name}')
                
                # Update all restaurant fields
                for key, value in restaurant_data.items():
                    if key == 'has_branches':
                        continue
                    if hasattr(restaurant, key):
                        setattr(restaurant, key, value)
                
                # Set status and onboarding
                restaurant.status = Restaurant.Status.ACTIVE
                restaurant.onboarding_status = Restaurant.OnboardingStatus.APPROVED
                restaurant.kyc_verified = True
                restaurant.kyc_verified_at = timezone.now()
                restaurant.onboarding_completed_at = timezone.now()
                restaurant.country = 'India'  # Ensure country is set
                
                # Set opening hours
                restaurant.opening_hours = {
                    'monday': {'open': '10:00', 'close': '22:30'},
                    'tuesday': {'open': '10:00', 'close': '22:30'},
                    'wednesday': {'open': '10:00', 'close': '22:30'},
                    'thursday': {'open': '10:00', 'close': '22:30'},
                    'friday': {'open': '10:00', 'close': '23:30'},
                    'saturday': {'open': '10:00', 'close': '23:30'},
                    'sunday': {'open': '10:00', 'close': '22:00'},
                }
                
                restaurant.accepts_delivery = True
                restaurant.accepts_pickup = True
                restaurant.save()
                
                # Create or update restaurant settings
                settings, _ = RestaurantSettings.objects.get_or_create(
                    restaurant=restaurant,
                    defaults={
                        'default_prep_time_minutes': restaurant_data.get('estimated_preparation_time', 25),
                        'sla_threshold_minutes': 35,
                        'auto_accept_orders': False,
                        'supports_delivery': True,
                        'supports_pickup': True,
                        'max_delivery_distance_km': float(restaurant_data.get('delivery_radius_km', 10)),
                    }
                )
                
                # Update settings if they exist
                if not _:
                    settings.default_prep_time_minutes = restaurant_data.get('estimated_preparation_time', 25)
                    settings.sla_threshold_minutes = 35
                    settings.auto_accept_orders = False
                    settings.supports_delivery = True
                    settings.supports_pickup = True
                    settings.max_delivery_distance_km = float(restaurant_data.get('delivery_radius_km', 10))
                    settings.save()
                
                # Create manager profile if not exists
                ManagerProfile.objects.get_or_create(
                    restaurant=restaurant,
                    email=restaurant_data['manager_contact_email'],
                    defaults={
                        'first_name': restaurant_data['manager_contact_name'].split()[0],
                        'last_name': ' '.join(restaurant_data['manager_contact_name'].split()[1:]) if len(restaurant_data['manager_contact_name'].split()) > 1 else '',
                        'phone': restaurant_data['manager_contact_phone'],
                        'role': ManagerProfile.ManagerRole.GENERAL_MANAGER,
                        'is_primary': True,
                    }
                )
                
                # Create branches for Kora Smokehouse
                if restaurant_data.get('has_branches') and 'Kora' in restaurant.name:
                    # Main branch
                    RestaurantBranch.objects.get_or_create(
                        restaurant=restaurant,
                        name='Koramangala Cloud Kitchen',
                        defaults={
                            'branch_type': RestaurantBranch.BranchType.CLOUD,
                            'address_line1': 'Koramangala, Bengaluru',
                            'city': 'Bengaluru',
                            'state': 'Karnataka',
                            'postal_code': '560095',
                            'country': 'India',
                            'service_radius_km': Decimal('10.00'),
                            'contact_number': restaurant.phone,
                            'contact_email': restaurant.email,
                            'is_primary': True,
                            'supports_delivery': True,
                            'supports_pickup': True,
                        }
                    )
                    # Secondary branch
                    RestaurantBranch.objects.get_or_create(
                        restaurant=restaurant,
                        name='Indiranagar Pickup Hub',
                        defaults={
                            'branch_type': RestaurantBranch.BranchType.PICKUP,
                            'address_line1': '100 Feet Road, Indiranagar',
                            'city': 'Bengaluru',
                            'state': 'Karnataka',
                            'postal_code': '560038',
                            'country': 'India',
                            'service_radius_km': Decimal('5.00'),
                            'contact_number': restaurant.phone,
                            'contact_email': restaurant.email,
                            'is_primary': False,
                            'supports_delivery': False,
                            'supports_pickup': True,
                        }
                    )
                    restaurant.is_multi_branch = True
                    restaurant.save()
                
                # Create mock documents (marked as approved)
                document_types = [
                    RestaurantDocument.DocumentType.PAN,
                    RestaurantDocument.DocumentType.GST,
                    RestaurantDocument.DocumentType.FSSAI,
                    RestaurantDocument.DocumentType.BANK,
                ]
                
                for doc_type in document_types:
                    # Skip creating actual file documents, just mark as approved if they exist
                    existing_docs = RestaurantDocument.objects.filter(
                        restaurant=restaurant,
                        document_type=doc_type
                    )
                    if existing_docs.exists():
                        for doc in existing_docs:
                            if doc.status != RestaurantDocument.DocumentStatus.APPROVED:
                                doc.status = RestaurantDocument.DocumentStatus.APPROVED
                                doc.reviewed_at = timezone.now()
                                doc.save()
                
                self.stdout.write(self.style.SUCCESS(f'[OK] Completed onboarding for {restaurant.name}'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing {owner_email}: {str(e)}'))
                import traceback
                traceback.print_exc()
        
        self.stdout.write(self.style.SUCCESS(
            f'\nCompleted onboarding for {updated_count + created_count} restaurants '
            f'({created_count} created, {updated_count} updated)'
        ))

