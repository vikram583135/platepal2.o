"""
Seed delivery user with complete onboarding details
Creates a delivery rider user with all onboarding steps completed and approved
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from apps.deliveries.models import (
    RiderProfile,
    RiderOnboarding,
    RiderBankDetail,
    RiderWallet,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed delivery user with complete onboarding details'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='rider@platepal.com',
            help='Email for the delivery user (default: rider@platepal.com)',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='rider123',
            help='Password for the delivery user (default: rider123)',
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing user and onboarding data if they exist',
        )

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        update = options['update']

        self.stdout.write(self.style.SUCCESS(f'Creating delivery user: {email}'))

        # Create or get delivery user
        rider, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': 'Delivery',
                'last_name': 'Rider',
                'phone': '+91 98765 20000',
                'role': User.Role.DELIVERY,
                'is_email_verified': True,
            }
        )

        if created:
            rider.set_password(password)
            rider.save()
            self.stdout.write(self.style.SUCCESS(f'[OK] Created delivery user: {rider.email}'))
        else:
            if update:
                # Update existing user
                rider.first_name = 'Delivery'
                rider.last_name = 'Rider'
                if not rider.phone:
                    rider.phone = '+91 98765 20000'
                rider.role = User.Role.DELIVERY
                rider.is_email_verified = True
                rider.set_password(password)
                rider.save()
                self.stdout.write(self.style.SUCCESS(f'[OK] Updated delivery user: {rider.email}'))
            else:
                self.stdout.write(self.style.WARNING(f'  Delivery user already exists: {rider.email}'))

        # Create or update RiderProfile
        profile, profile_created = RiderProfile.objects.get_or_create(
            rider=rider,
            defaults={
                'date_of_birth': date(1990, 1, 15),
                'government_id_number': 'A123456789',
                'vehicle_type': 'BIKE',
                'vehicle_registration_number': 'MH01AB1234',
                'vehicle_model': 'Honda Activa',
                'vehicle_color': 'Red',
                'driver_license_number': 'DL1234567890123',
                'driver_license_expiry': date.today() + timedelta(days=365 * 5),  # 5 years from now
                'emergency_contact_name': 'John Doe',
                'emergency_contact_phone': '+91 98765 10000',
                'emergency_contact_relationship': 'Brother',
                'profile_completion_percentage': 100,
            }
        )

        if profile_created:
            self.stdout.write(self.style.SUCCESS('[OK] Created rider profile'))
        elif update:
            # Update existing profile
            profile.date_of_birth = date(1990, 1, 15)
            profile.government_id_number = 'A123456789'
            profile.vehicle_type = 'BIKE'
            profile.vehicle_registration_number = 'MH01AB1234'
            profile.vehicle_model = 'Honda Activa'
            profile.vehicle_color = 'Red'
            profile.driver_license_number = 'DL1234567890123'
            profile.driver_license_expiry = date.today() + timedelta(days=365 * 5)
            profile.emergency_contact_name = 'John Doe'
            profile.emergency_contact_phone = '+91 98765 10000'
            profile.emergency_contact_relationship = 'Brother'
            profile.profile_completion_percentage = 100
            profile.save()
            self.stdout.write(self.style.SUCCESS('[OK] Updated rider profile'))
        else:
            self.stdout.write(self.style.WARNING('  Rider profile already exists'))

        # Create or update RiderOnboarding with all steps completed and approved
        now = timezone.now()
        onboarding, onboarding_created = RiderOnboarding.objects.get_or_create(
            rider=rider,
            defaults={
                'status': RiderOnboarding.OnboardingStatus.APPROVED,
                'phone_verified': True,
                'email_verified': True,
                'profile_completed': True,
                'documents_uploaded': True,
                'bank_details_added': True,
                'background_check_completed': True,
                'agreement_signed': True,
                'induction_video_watched': True,
                'current_step': 8,  # All steps completed
                'completed_steps': [1, 2, 3, 4, 5, 6, 7, 8],  # All steps
                'started_at': now - timedelta(days=7),
                'completed_at': now - timedelta(days=1),
                'approved_at': now - timedelta(days=1),
            }
        )

        if onboarding_created:
            self.stdout.write(self.style.SUCCESS('[OK] Created rider onboarding (APPROVED)'))
        elif update:
            # Update existing onboarding
            onboarding.status = RiderOnboarding.OnboardingStatus.APPROVED
            onboarding.phone_verified = True
            onboarding.email_verified = True
            onboarding.profile_completed = True
            onboarding.documents_uploaded = True
            onboarding.bank_details_added = True
            onboarding.background_check_completed = True
            onboarding.agreement_signed = True
            onboarding.induction_video_watched = True
            onboarding.current_step = 8
            onboarding.completed_steps = [1, 2, 3, 4, 5, 6, 7, 8]
            if not onboarding.started_at:
                onboarding.started_at = now - timedelta(days=7)
            onboarding.completed_at = now - timedelta(days=1)
            onboarding.approved_at = now - timedelta(days=1)
            onboarding.save()
            self.stdout.write(self.style.SUCCESS('[OK] Updated rider onboarding (APPROVED)'))
        else:
            self.stdout.write(self.style.WARNING('  Rider onboarding already exists'))

        # Create or update RiderBankDetail
        bank_detail, bank_created = RiderBankDetail.objects.get_or_create(
            rider=rider,
            defaults={
                'bank_name': 'HDFC Bank',
                'account_holder_name': f'{rider.first_name} {rider.last_name}',
                'account_number': '1234567890123456',
                'ifsc_code': 'HDFC0000123',
                'bank_branch': 'Mumbai Main Branch',
                'is_verified': True,
                'verified_at': now - timedelta(days=1),
            }
        )

        if bank_created:
            self.stdout.write(self.style.SUCCESS('[OK] Created rider bank details'))
        elif update:
            bank_detail.bank_name = 'HDFC Bank'
            bank_detail.account_holder_name = f'{rider.first_name} {rider.last_name}'
            bank_detail.account_number = '1234567890123456'
            bank_detail.ifsc_code = 'HDFC0000123'
            bank_detail.bank_branch = 'Mumbai Main Branch'
            bank_detail.is_verified = True
            if not bank_detail.verified_at:
                bank_detail.verified_at = now - timedelta(days=1)
            bank_detail.save()
            self.stdout.write(self.style.SUCCESS('[OK] Updated rider bank details'))
        else:
            self.stdout.write(self.style.WARNING('  Rider bank details already exist'))

        # Create or update RiderWallet
        wallet, wallet_created = RiderWallet.objects.get_or_create(
            rider=rider,
            defaults={
                'balance': 0.00,
                'currency': 'USD',
                'pending_payout': 0.00,
            }
        )

        if wallet_created:
            self.stdout.write(self.style.SUCCESS('[OK] Created rider wallet'))
        elif update:
            # Wallet already exists, just confirm
            self.stdout.write(self.style.SUCCESS('[OK] Rider wallet already exists'))
        else:
            self.stdout.write(self.style.WARNING('  Rider wallet already exists'))

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Delivery User Seeded Successfully!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        self.stdout.write(f'Email: {rider.email}')
        self.stdout.write(f'Password: {password}')
        self.stdout.write(f'Onboarding Status: {onboarding.status}')
        self.stdout.write(f'Profile Completion: {profile.profile_completion_percentage}%')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('You can now log in to the Delivery Dashboard!'))
        self.stdout.write(f'URL: http://localhost:3022')
        self.stdout.write('')

