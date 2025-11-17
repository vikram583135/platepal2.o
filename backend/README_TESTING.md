# Testing Infrastructure

This document describes the testing infrastructure for the PlatePal delivery backend.

## Test Structure

### Unit Tests
- **Location**: `backend/apps/deliveries/tests/`
- **Files**:
  - `test_models.py` - Tests for all model functionality
  - `test_views.py` - Tests for API endpoints
  - `test_services.py` - Tests for service functions
  - `test_advanced_features.py` - Tests for advanced features (gamification, voice, ML, etc.)

### Integration Tests
- **Location**: `backend/tests/integration/`
- **Files**:
  - `test_delivery_flow.py` - End-to-end delivery flow tests

## Running Tests

### Using Django Test Runner
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.deliveries

# Run specific test file
python manage.py test apps.deliveries.tests.test_models

# Run specific test class
python manage.py test apps.deliveries.tests.test_models.DeliveryModelTestCase

# Run specific test method
python manage.py test apps.deliveries.tests.test_models.DeliveryModelTestCase.test_create_delivery

# Run with verbosity
python manage.py test --verbosity=2

# Run and keep test database
python manage.py test --keepdb
```

### Using pytest (if installed)
```bash
# Install pytest-django
pip install pytest-django

# Run all tests
pytest

# Run specific test file
pytest apps/deliveries/tests/test_models.py

# Run with coverage
pytest --cov=apps.deliveries --cov-report=html
```

## Test Coverage

### Model Tests (`test_models.py`)
- ✅ Delivery model creation and status transitions
- ✅ RiderShift model lifecycle
- ✅ DeliveryOffer creation and expiry
- ✅ RiderWallet and transactions
- ✅ TripLog creation
- ✅ OfflineAction creation and retry logic
- ✅ RiderSettings creation

### View Tests (`test_views.py`)
- ✅ Delivery CRUD operations
- ✅ Pause/resume delivery
- ✅ Unable to deliver flow
- ✅ Shift start/stop
- ✅ Offer acceptance/decline
- ✅ Wallet operations
- ✅ Offline action sync
- ✅ Trip log analytics

### Service Tests (`test_services.py`)
- ✅ Distance calculation (Haversine formula)
- ✅ ETA calculation
- ✅ Navigation deep link generation
- ✅ Earnings breakdown calculation
- ✅ Surge pricing calculation
- ✅ Phone number masking

### Integration Tests (`test_delivery_flow.py`)
- ✅ Complete delivery flow (offer → accept → pickup → deliver)
- ✅ Shift management integration
- ✅ Location tracking integration

## Advanced Features Tests (`test_advanced_features.py`)

### Gamification
- ✅ Rider achievement system
- ✅ Rider leveling system
- ✅ Points and rewards

### Voice Commands
- ✅ Voice command processing
- ✅ Command recognition accuracy

### ML ETA Predictions
- ✅ ETA prediction with traffic/weather factors
- ✅ Confidence scoring

### Multi-Tenant Fleets
- ✅ Tenant fleet creation
- ✅ Rider association with tenants
- ✅ Leaderboard by tenant

## Test Data Setup

Tests use Django's `TestCase` which:
- Creates a fresh test database for each test
- Rolls back all database changes after each test
- Provides `APIClient` for testing API endpoints
- Includes authentication helpers

### Example Test Setup
```python
def setUp(self):
    self.client = APIClient()
    self.rider = User.objects.create_user(
        email='rider@test.com',
        password='testpass123',
        role=User.Role.DELIVERY
    )
```

## Continuous Integration

For CI/CD, add to your pipeline:

```yaml
# Example GitHub Actions
- name: Run Tests
  run: |
    python manage.py test --verbosity=2
    pytest --cov=apps.deliveries --cov-report=xml

- name: Generate Coverage Report
  run: |
    coverage html
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Naming**: Use descriptive test names (test_`action`_`expected_result`)
3. **Assertions**: Use specific assertions (assertEqual, assertTrue, etc.)
4. **Cleanup**: Django TestCase handles database cleanup automatically
5. **Mocking**: Use mocks for external services (payment gateways, SMS, etc.)

## Coverage Goals

- **Minimum**: 70% code coverage
- **Target**: 80%+ code coverage
- **Critical paths**: 100% coverage (authentication, payments, deliveries)

## Running Specific Test Categories

```bash
# Model tests only
python manage.py test apps.deliveries.tests.test_models

# View/API tests only
python manage.py test apps.deliveries.tests.test_views

# Service tests only
python manage.py test apps.deliveries.tests.test_services

# Integration tests only
python manage.py test tests.integration
```

## Test Database

- Tests use a separate test database (prefixed with `test_`)
- Database is created before first test and destroyed after all tests
- Use `--keepdb` flag to reuse test database for faster test runs

