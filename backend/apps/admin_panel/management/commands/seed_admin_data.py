"""
Management command to seed mock data for admin dashboard
Includes: roles, permissions, admin users, API tokens, system health, alerts, incidents,
automation rules, webhooks, feature flags, fraud rules, chargebacks, SLOs, and audit logs
"""
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.admin_panel.models import (
    Role, Permission, RolePermission, AdminUser, APIToken, AdminSession,
    Environment, EnvironmentAccess, SSOProvider, AuditLogEntry,
)
from apps.admin_panel.models_operations import (
    SystemHealthMetric, AlertRule, Incident, IncidentUpdate,
    RateLimitRule, IPWhitelist, IPBlacklist, MaintenanceWindow,
)
from apps.admin_panel.models_automation import (
    AutomationRule, ScheduledJob, JobExecution, Webhook, WebhookDelivery,
)
from apps.admin_panel.models_advanced import (
    FraudDetectionRule, Chargeback, FeatureFlag, SLO,
)
from apps.orders.models import Order
from apps.payments.models import Payment
from apps.restaurants.models import Restaurant

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed admin dashboard with mock data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing admin data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing admin data...'))
            self._clear_data()

        self.stdout.write(self.style.SUCCESS('Starting admin data seeding...'))

        # Seed in order of dependencies
        admin_user = self._seed_admin_users()
        roles, permissions = self._seed_roles_and_permissions()
        self._seed_api_tokens(admin_user)
        self._seed_environments(admin_user)
        self._seed_sso_providers()
        self._seed_system_health_metrics()
        self._seed_alert_rules()
        self._seed_incidents(admin_user)
        self._seed_rate_limits()
        self._seed_ip_lists(admin_user)
        self._seed_maintenance_windows(admin_user)
        self._seed_automation_rules(admin_user)
        self._seed_scheduled_jobs(admin_user)
        self._seed_webhooks(admin_user)
        self._seed_feature_flags(admin_user)
        self._seed_fraud_rules()
        self._seed_chargebacks(admin_user)
        self._seed_slos()
        self._seed_audit_logs(admin_user)

        self.stdout.write(self.style.SUCCESS('\n[SUCCESS] Admin data seeding completed!'))

    def _clear_data(self):
        """Clear existing admin data"""
        AuditLogEntry.objects.all().delete()
        Chargeback.objects.all().delete()
        FraudDetectionRule.objects.all().delete()
        FeatureFlag.objects.all().delete()
        SLO.objects.all().delete()
        WebhookDelivery.objects.all().delete()
        Webhook.objects.all().delete()
        JobExecution.objects.all().delete()
        ScheduledJob.objects.all().delete()
        AutomationRule.objects.all().delete()
        MaintenanceWindow.objects.all().delete()
        IPBlacklist.objects.all().delete()
        IPWhitelist.objects.all().delete()
        RateLimitRule.objects.all().delete()
        IncidentUpdate.objects.all().delete()
        Incident.objects.all().delete()
        AlertRule.objects.all().delete()
        SystemHealthMetric.objects.all().delete()
        SSOProvider.objects.all().delete()
        EnvironmentAccess.objects.all().delete()
        Environment.objects.all().delete()
        AdminSession.objects.all().delete()
        APIToken.objects.all().delete()
        AdminUser.objects.all().delete()
        RolePermission.objects.all().delete()
        Permission.objects.all().delete()
        Role.objects.all().delete()

    def _seed_admin_users(self):
        """Seed admin users"""
        self.stdout.write('  Seeding admin users...')
        
        admin_user, created = User.objects.get_or_create(
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
        if created:
            admin_user.set_password('admin123')
            admin_user.save()

        # Create AdminUser profile
        admin_profile, _ = AdminUser.objects.get_or_create(
            user=admin_user,
            defaults={'is_active': True}
        )

        # Create additional admin users
        admin_users_data = [
            {'email': 'superadmin@platepal.com', 'first_name': 'Super', 'last_name': 'Admin', 'phone': '+91 98765 00002'},
            {'email': 'support@platepal.com', 'first_name': 'Support', 'last_name': 'Manager', 'phone': '+91 98765 00003'},
            {'email': 'ops@platepal.com', 'first_name': 'Operations', 'last_name': 'Manager', 'phone': '+91 98765 00004'},
        ]

        for user_data in admin_users_data:
            user, created = User.objects.get_or_create(
                email=user_data['email'],
                defaults={
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'phone': user_data['phone'],
                    'role': User.Role.ADMIN,
                    'is_staff': True,
                    'is_email_verified': True
                }
            )
            if created:
                user.set_password('admin123')
                user.save()
            AdminUser.objects.get_or_create(
                user=user,
                defaults={'is_active': True}
            )

        return admin_user

    def _seed_roles_and_permissions(self):
        """Seed roles and permissions"""
        self.stdout.write('  Seeding roles and permissions...')

        # Create permissions
        permissions_data = [
            # User management
            {'name': 'View Users', 'codename': 'users.view', 'resource_type': 'user', 'action': 'view'},
            {'name': 'Edit Users', 'codename': 'users.edit', 'resource_type': 'user', 'action': 'edit'},
            {'name': 'Delete Users', 'codename': 'users.delete', 'resource_type': 'user', 'action': 'delete'},
            {'name': 'Ban Users', 'codename': 'users.ban', 'resource_type': 'user', 'action': 'ban'},
            # Order management
            {'name': 'View Orders', 'codename': 'orders.view', 'resource_type': 'order', 'action': 'view'},
            {'name': 'Edit Orders', 'codename': 'orders.edit', 'resource_type': 'order', 'action': 'edit'},
            {'name': 'Refund Orders', 'codename': 'orders.refund', 'resource_type': 'order', 'action': 'refund'},
            # Restaurant management
            {'name': 'View Restaurants', 'codename': 'restaurants.view', 'resource_type': 'restaurant', 'action': 'view'},
            {'name': 'Approve Restaurants', 'codename': 'restaurants.approve', 'resource_type': 'restaurant', 'action': 'approve'},
            {'name': 'Suspend Restaurants', 'codename': 'restaurants.suspend', 'resource_type': 'restaurant', 'action': 'suspend'},
            # System management
            {'name': 'View System Health', 'codename': 'system.view', 'resource_type': 'system', 'action': 'view'},
            {'name': 'Manage Incidents', 'codename': 'system.incidents', 'resource_type': 'system', 'action': 'manage'},
            {'name': 'Manage Feature Flags', 'codename': 'system.feature_flags', 'resource_type': 'system', 'action': 'manage'},
        ]

        permissions = {}
        for perm_data in permissions_data:
            perm, _ = Permission.objects.get_or_create(
                codename=perm_data['codename'],
                defaults=perm_data
            )
            permissions[perm_data['codename']] = perm

        # Create roles
        roles_data = [
            {
                'name': 'Super Admin',
                'description': 'Full system access',
                'is_system': True,
                'permissions': list(permissions.keys())
            },
            {
                'name': 'Support Manager',
                'description': 'User and order management',
                'is_system': False,
                'permissions': ['users.view', 'users.edit', 'users.ban', 'orders.view', 'orders.edit', 'orders.refund']
            },
            {
                'name': 'Operations Manager',
                'description': 'System operations and monitoring',
                'is_system': False,
                'permissions': ['system.view', 'system.incidents', 'restaurants.view', 'restaurants.suspend']
            },
            {
                'name': 'Content Moderator',
                'description': 'Content and restaurant moderation',
                'is_system': False,
                'permissions': ['restaurants.view', 'restaurants.approve', 'users.view']
            },
        ]

        roles = {}
        for role_data in roles_data:
            role, _ = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={
                    'description': role_data['description'],
                    'is_system': role_data['is_system']
                }
            )
            roles[role_data['name']] = role

            # Assign permissions to role
            for perm_codename in role_data['permissions']:
                if perm_codename in permissions:
                    RolePermission.objects.get_or_create(
                        role=role,
                        permission=permissions[perm_codename]
                    )

        return roles, permissions

    def _seed_api_tokens(self, admin_user):
        """Seed API tokens"""
        self.stdout.write('  Seeding API tokens...')

        tokens_data = [
            {'name': 'Production API Token', 'scopes': ['orders.view', 'orders.edit'], 'rate_limit': 5000},
            {'name': 'Analytics Token', 'scopes': ['orders.view', 'users.view'], 'rate_limit': 2000},
            {'name': 'Webhook Token', 'scopes': ['orders.view'], 'rate_limit': 10000},
        ]

        for token_data in tokens_data:
            token, created = APIToken.objects.get_or_create(
                user=admin_user,
                name=token_data['name'],
                defaults={
                    'scopes': token_data['scopes'],
                    'rate_limit': token_data['rate_limit'],
                    'expires_at': timezone.now() + timedelta(days=365),
                    'last_used_at': timezone.now() - timedelta(hours=random.randint(1, 24)),
                    'last_used_ip': f'192.168.1.{random.randint(1, 255)}',
                    'is_active': True
                }
            )
            if not created:
                token.scopes = token_data['scopes']
                token.rate_limit = token_data['rate_limit']
                token.save()

    def _seed_environments(self, admin_user):
        """Seed environments"""
        self.stdout.write('  Seeding environments...')

        environments_data = [
            {'name': 'production', 'display_name': 'Production', 'is_production': True, 'requires_approval': True},
            {'name': 'staging', 'display_name': 'Staging', 'is_production': False, 'requires_approval': False},
            {'name': 'development', 'display_name': 'Development', 'is_production': False, 'requires_approval': False},
        ]

        for env_data in environments_data:
            env, _ = Environment.objects.get_or_create(
                name=env_data['name'],
                defaults={
                    'display_name': env_data['display_name'],
                    'is_production': env_data['is_production'],
                    'requires_approval': env_data['requires_approval'],
                    'api_base_url': f'https://{env_data["name"]}.platepal.com/api',
                    'is_active': True
                }
            )
            # Grant access to admin user
            EnvironmentAccess.objects.get_or_create(
                user=admin_user,
                environment=env,
                defaults={'is_active': True, 'granted_by': admin_user}
            )

    def _seed_sso_providers(self):
        """Seed SSO providers"""
        self.stdout.write('  Seeding SSO providers...')

        providers_data = [
            {'name': 'Google Workspace', 'provider_type': 'OIDC', 'is_active': True},
            {'name': 'Microsoft Azure AD', 'provider_type': 'SAML', 'is_active': True},
            {'name': 'Okta', 'provider_type': 'SAML', 'is_active': False},
        ]

        for provider_data in providers_data:
            SSOProvider.objects.get_or_create(
                name=provider_data['name'],
                defaults=provider_data
            )

    def _seed_system_health_metrics(self):
        """Seed system health metrics"""
        self.stdout.write('  Seeding system health metrics...')

        services = ['api', 'database', 'redis', 'payment_gateway', 'notification_service']
        metric_types = ['latency', 'error_rate', 'cpu', 'memory', 'queue_size']

        for service in services:
            for metric_type in metric_types:
                if metric_type == 'latency':
                    value = random.uniform(50, 200)
                    threshold_warning = 150
                    threshold_critical = 300
                elif metric_type == 'error_rate':
                    value = random.uniform(0, 2)
                    threshold_warning = 1
                    threshold_critical = 5
                elif metric_type == 'cpu':
                    value = random.uniform(20, 80)
                    threshold_warning = 70
                    threshold_critical = 90
                elif metric_type == 'memory':
                    value = random.uniform(40, 85)
                    threshold_warning = 80
                    threshold_critical = 95
                else:  # queue_size
                    value = random.uniform(0, 100)
                    threshold_warning = 50
                    threshold_critical = 100

                status = 'healthy'
                if value >= threshold_critical:
                    status = 'critical'
                elif value >= threshold_warning:
                    status = 'warning'

                SystemHealthMetric.objects.create(
                    service_name=service,
                    metric_type=metric_type,
                    value=value,
                    threshold_warning=threshold_warning,
                    threshold_critical=threshold_critical,
                    status=status
                )

    def _seed_alert_rules(self):
        """Seed alert rules"""
        self.stdout.write('  Seeding alert rules...')

        rules_data = [
            {'name': 'High API Latency', 'service_name': 'api', 'metric_type': 'latency', 'condition': 'gt', 'threshold': 200, 'severity': 'warning'},
            {'name': 'Critical Error Rate', 'service_name': 'api', 'metric_type': 'error_rate', 'condition': 'gt', 'threshold': 5, 'severity': 'critical'},
            {'name': 'High CPU Usage', 'service_name': 'database', 'metric_type': 'cpu', 'condition': 'gt', 'threshold': 85, 'severity': 'warning'},
            {'name': 'Memory Exhaustion', 'service_name': 'redis', 'metric_type': 'memory', 'condition': 'gt', 'threshold': 90, 'severity': 'critical'},
        ]

        for rule_data in rules_data:
            AlertRule.objects.get_or_create(
                name=rule_data['name'],
                defaults={
                    **rule_data,
                    'is_active': True,
                    'notification_channels': ['email', 'slack']
                }
            )

    def _seed_incidents(self, admin_user):
        """Seed incidents"""
        self.stdout.write('  Seeding incidents...')

        incidents_data = [
            {
                'title': 'Payment Gateway Timeout',
                'description': 'Intermittent timeouts when processing payments',
                'status': 'RESOLVED',
                'severity': 'HIGH',
                'affected_services': ['payment_gateway', 'api'],
            },
            {
                'title': 'Database Connection Pool Exhausted',
                'description': 'Database connection pool reached maximum capacity',
                'status': 'INVESTIGATING',
                'severity': 'CRITICAL',
                'affected_services': ['database'],
            },
            {
                'title': 'High API Response Time',
                'description': 'API response times increased by 300%',
                'status': 'OPEN',
                'severity': 'MEDIUM',
                'affected_services': ['api'],
            },
        ]

        for incident_data in incidents_data:
            incident, created = Incident.objects.get_or_create(
                title=incident_data['title'],
                defaults={
                    **incident_data,
                    'reported_by': admin_user,
                    'resolved_at': timezone.now() - timedelta(hours=2) if incident_data['status'] == 'RESOLVED' else None,
                    'resolved_by': admin_user if incident_data['status'] == 'RESOLVED' else None,
                }
            )

            if created and incident_data['status'] == 'RESOLVED':
                IncidentUpdate.objects.create(
                    incident=incident,
                    user=admin_user,
                    message='Issue resolved. Root cause was identified and fixed.',
                    is_public=True
                )

    def _seed_rate_limits(self):
        """Seed rate limit rules"""
        self.stdout.write('  Seeding rate limit rules...')

        rules_data = [
            {'name': 'API General', 'endpoint_pattern': '/api/*', 'requests_per_minute': 60, 'requests_per_hour': 1000},
            {'name': 'Admin Endpoints', 'endpoint_pattern': '/admin/*', 'requests_per_minute': 30, 'requests_per_hour': 500, 'role': 'ADMIN'},
            {'name': 'Public Endpoints', 'endpoint_pattern': '/api/public/*', 'requests_per_minute': 120, 'requests_per_hour': 2000},
        ]

        for rule_data in rules_data:
            RateLimitRule.objects.get_or_create(
                name=rule_data['name'],
                defaults={
                    **rule_data,
                    'burst_limit': 10,
                    'is_active': True
                }
            )

    def _seed_ip_lists(self, admin_user):
        """Seed IP whitelist and blacklist"""
        self.stdout.write('  Seeding IP lists...')

        # Whitelist
        whitelist_ips = [
            {'ip_address': '192.168.1.100', 'description': 'Office Network'},
            {'ip_address': '10.0.0.50', 'description': 'VPN Gateway'},
        ]

        for ip_data in whitelist_ips:
            IPWhitelist.objects.get_or_create(
                ip_address=ip_data['ip_address'],
                defaults={
                    **ip_data,
                    'is_active': True,
                    'added_by': admin_user
                }
            )

        # Blacklist
        blacklist_ips = [
            {'ip_address': '192.168.1.200', 'reason': 'Suspicious activity detected'},
            {'ip_address': '10.0.0.100', 'reason': 'Multiple failed login attempts'},
        ]

        for ip_data in blacklist_ips:
            IPBlacklist.objects.get_or_create(
                ip_address=ip_data['ip_address'],
                defaults={
                    **ip_data,
                    'is_active': True,
                    'added_by': admin_user,
                    'expires_at': timezone.now() + timedelta(days=30)
                }
            )

    def _seed_maintenance_windows(self, admin_user):
        """Seed maintenance windows"""
        self.stdout.write('  Seeding maintenance windows...')

        MaintenanceWindow.objects.get_or_create(
            title='Scheduled Database Maintenance',
            defaults={
                'description': 'Database optimization and index rebuilding',
                'start_time': timezone.now() + timedelta(days=7),
                'end_time': timezone.now() + timedelta(days=7, hours=2),
                'affected_services': ['database', 'api'],
                'is_active': True,
                'user_message': 'Service will be temporarily unavailable during maintenance',
                'created_by': admin_user
            }
        )

    def _seed_automation_rules(self, admin_user):
        """Seed automation rules"""
        self.stdout.write('  Seeding automation rules...')

        rules_data = [
            {
                'name': 'Auto-refund Failed Orders',
                'description': 'Automatically refund orders that fail after 3 attempts',
                'trigger_type': 'EVENT',
                'trigger_config': {'event': 'order.payment_failed'},
                'action_type': 'REFUND',
                'is_active': True,
            },
            {
                'name': 'Suspend Restaurant on Low Rating',
                'description': 'Suspend restaurant if rating drops below 3.0',
                'trigger_type': 'METRIC',
                'trigger_config': {'metric': 'restaurant.rating', 'threshold': 3.0},
                'action_type': 'SUSPEND_PARTNER',
                'is_active': False,
            },
        ]

        for rule_data in rules_data:
            AutomationRule.objects.get_or_create(
                name=rule_data['name'],
                defaults={
                    **rule_data,
                    'conditions': [],
                    'action_config': {},
                    'priority': 0,
                    'created_by': admin_user
                }
            )

    def _seed_scheduled_jobs(self, admin_user):
        """Seed scheduled jobs"""
        self.stdout.write('  Seeding scheduled jobs...')

        jobs_data = [
            {'name': 'Daily Settlement Run', 'job_type': 'settlement_run', 'cron_expression': '0 2 * * *', 'is_active': True},
            {'name': 'Weekly Analytics Report', 'job_type': 'analytics_report', 'cron_expression': '0 9 * * 1', 'is_active': True},
            {'name': 'Monthly Data Sync', 'job_type': 'data_sync', 'cron_expression': '0 3 1 * *', 'is_active': True},
        ]

        for job_data in jobs_data:
            job, created = ScheduledJob.objects.get_or_create(
                name=job_data['name'],
                defaults={
                    **job_data,
                    'description': f'Scheduled {job_data["job_type"]} job',
                    'config': {},
                    'status': 'PENDING',
                    'next_run_at': timezone.now() + timedelta(hours=1)
                }
            )

            if created:
                # Create execution history
                JobExecution.objects.create(
                    job=job,
                    status='COMPLETED',
                    started_at=timezone.now() - timedelta(hours=24),
                    completed_at=timezone.now() - timedelta(hours=23, minutes=50),
                    output={'records_processed': random.randint(100, 1000)}
                )

    def _seed_webhooks(self, admin_user):
        """Seed webhooks"""
        self.stdout.write('  Seeding webhooks...')

        webhooks_data = [
            {
                'name': 'Order Webhook',
                'url': 'https://example.com/webhooks/orders',
                'events': ['order.created', 'order.completed', 'order.cancelled'],
                'status': 'ACTIVE',
            },
            {
                'name': 'Payment Webhook',
                'url': 'https://example.com/webhooks/payments',
                'events': ['payment.success', 'payment.failed'],
                'status': 'ACTIVE',
            },
        ]

        for webhook_data in webhooks_data:
            webhook, created = Webhook.objects.get_or_create(
                name=webhook_data['name'],
                defaults={
                    **webhook_data,
                    'secret': 'webhook_secret_key',
                    'retry_policy': {'max_retries': 3, 'backoff': 'exponential'},
                    'headers': {'Authorization': 'Bearer token'},
                    'is_active': True,
                    'last_triggered_at': timezone.now() - timedelta(minutes=random.randint(1, 60))
                }
            )

            if created:
                # Create delivery history
                WebhookDelivery.objects.create(
                    webhook=webhook,
                    event=webhook_data['events'][0],
                    payload={'order_id': '12345', 'status': 'completed'},
                    response_status=200,
                    success=True,
                    attempt_number=1
                )

    def _seed_feature_flags(self, admin_user):
        """Seed feature flags"""
        self.stdout.write('  Seeding feature flags...')

        flags_data = [
            {'name': 'new_checkout_flow', 'description': 'New checkout experience', 'is_enabled': True, 'rollout_percentage': 50},
            {'name': 'ai_recommendations', 'description': 'AI-powered menu recommendations', 'is_enabled': False, 'rollout_percentage': 0},
            {'name': 'dark_mode', 'description': 'Dark mode UI', 'is_enabled': True, 'rollout_percentage': 100},
            {'name': 'live_tracking', 'description': 'Real-time order tracking', 'is_enabled': True, 'rollout_percentage': 75},
        ]

        for flag_data in flags_data:
            FeatureFlag.objects.get_or_create(
                name=flag_data['name'],
                defaults={
                    **flag_data,
                    'target_audience': {},
                    'created_by': admin_user
                }
            )

    def _seed_fraud_rules(self):
        """Seed fraud detection rules"""
        self.stdout.write('  Seeding fraud detection rules...')

        rules_data = [
            {
                'name': 'High Value Transaction',
                'description': 'Flag transactions above ₹5000',
                'rule_type': 'transaction_amount',
                'conditions': {'amount_threshold': 5000},
                'action': 'flag',
                'risk_score_threshold': 60,
            },
            {
                'name': 'Velocity Check',
                'description': 'Flag multiple transactions in short time',
                'rule_type': 'velocity',
                'conditions': {'max_transactions_per_hour': 5},
                'action': 'require_verification',
                'risk_score_threshold': 70,
            },
        ]

        for rule_data in rules_data:
            FraudDetectionRule.objects.get_or_create(
                name=rule_data['name'],
                defaults={
                    **rule_data,
                    'is_active': True
                }
            )

    def _seed_chargebacks(self, admin_user):
        """Seed chargebacks"""
        self.stdout.write('  Seeding chargebacks...')

        orders = Order.objects.all()[:5]
        if not orders.exists():
            self.stdout.write(self.style.WARNING('    No orders found. Skipping chargebacks.'))
            return

        statuses = ['RECEIVED', 'UNDER_REVIEW', 'EVIDENCE_SUBMITTED', 'WON', 'LOST']
        reasons = ['Unauthorized transaction', 'Product not received', 'Product not as described', 'Duplicate charge']

        for order in orders:
            try:
                payment = Payment.objects.filter(order=order).first()
                if not payment:
                    continue

                chargeback, created = Chargeback.objects.get_or_create(
                    chargeback_id=f'CB-{order.id}-{random.randint(1000, 9999)}',
                    defaults={
                        'order': order,
                        'payment': payment,
                        'reason': random.choice(reasons),
                        'amount': payment.amount,
                        'status': random.choice(statuses),
                        'received_date': timezone.now() - timedelta(days=random.randint(1, 30)),
                        'due_date': timezone.now() + timedelta(days=random.randint(1, 14)),
                        'evidence_bundle': [],
                        'assigned_to': admin_user if random.choice([True, False]) else None
                    }
                )
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'    Error creating chargeback for order {order.id}: {e}'))

    def _seed_slos(self):
        """Seed SLOs"""
        self.stdout.write('  Seeding SLOs...')

        slos_data = [
            {'service_name': 'api', 'metric_name': 'latency', 'target_value': 200, 'current_value': 150, 'window_days': 30},
            {'service_name': 'api', 'metric_name': 'error_rate', 'target_value': 0.1, 'current_value': 0.05, 'window_days': 30},
            {'service_name': 'api', 'metric_name': 'availability', 'target_value': 99.9, 'current_value': 99.95, 'window_days': 30},
            {'service_name': 'payment_gateway', 'metric_name': 'latency', 'target_value': 500, 'current_value': 350, 'window_days': 30},
        ]

        for slo_data in slos_data:
            SLO.objects.get_or_create(
                service_name=slo_data['service_name'],
                metric_name=slo_data['metric_name'],
                defaults={
                    **slo_data,
                    'is_active': True
                }
            )

    def _seed_audit_logs(self, admin_user):
        """Seed audit logs"""
        self.stdout.write('  Seeding audit logs...')

        actions = [
            {'action': 'user.ban', 'resource_type': 'user', 'resource_id': '1'},
            {'action': 'order.refund', 'resource_type': 'order', 'resource_id': '1'},
            {'action': 'restaurant.suspend', 'resource_type': 'restaurant', 'resource_id': '1'},
            {'action': 'feature_flag.update', 'resource_type': 'feature_flag', 'resource_id': '1'},
            {'action': 'api_token.create', 'resource_type': 'api_token', 'resource_id': '1'},
        ]

        for i, action_data in enumerate(actions):
            AuditLogEntry.objects.create(
                user=admin_user,
                **action_data,
                before_state={'status': 'active'},
                after_state={'status': 'inactive'},
                ip_address=f'192.168.1.{random.randint(1, 255)}',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                reason=f'Admin action {i+1}',
                metadata={'source': 'admin_dashboard'}
            )

