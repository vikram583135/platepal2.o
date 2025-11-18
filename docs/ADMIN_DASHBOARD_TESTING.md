# Admin Dashboard Testing Guide

## Phase 4: Testing & Validation

This document outlines the testing procedures for the admin dashboard after all bug fixes have been implemented.

## Pre-Testing Checklist

- [ ] Backend server is running on `http://localhost:8000`
- [ ] Frontend admin app is running on `http://localhost:3023`
- [ ] Database migrations are up to date
- [ ] Admin user exists (email: `admin@platepal.com`, password: `admin123`)
- [ ] Redis is running (if required)

## 1. Authentication Flow Testing

### Test Cases

1. **Login with Valid Credentials**
   - Navigate to `http://localhost:3023/login`
   - Enter email: `admin@platepal.com`
   - Enter password: `admin123`
   - Expected: Redirect to dashboard, token stored in localStorage

2. **Login with Invalid Credentials**
   - Enter wrong email/password
   - Expected: Error message displayed, no redirect

3. **Token Refresh**
   - Login successfully
   - Wait for token to expire (or manually expire it)
   - Make an API request
   - Expected: Token automatically refreshed, request succeeds

4. **Logout**
   - Click logout button
   - Expected: Tokens cleared, redirect to login page

5. **Protected Route Access**
   - Try to access `/users` without token
   - Expected: Redirect to login page

## 2. API Endpoint Testing

### Core Endpoints

#### Admin Users
- `GET /api/admin/users/` - List admin users
- `POST /api/admin/users/` - Create admin user
- `GET /api/admin/users/{id}/` - Get admin user details
- `PUT /api/admin/users/{id}/` - Update admin user

#### User Management
- `GET /api/admin/management/users/` - List all users
- `POST /api/admin/management/users/{id}/ban/` - Ban user
- `POST /api/admin/management/users/{id}/unban/` - Unban user
- `POST /api/admin/management/users/{id}/reset_password/` - Reset password

#### Orders
- `GET /api/orders/` - List orders
- `GET /api/orders/{id}/` - Get order details

#### Analytics
- `GET /api/analytics/analytics/dashboard/` - Get dashboard analytics

### Test Each Endpoint

1. **Without Authentication**
   - Expected: 401 Unauthorized

2. **With Valid Token**
   - Expected: 200 OK with data

3. **With Invalid Token**
   - Expected: 401 Unauthorized, token refresh attempted

4. **With Missing Permissions**
   - Expected: 403 Forbidden

## 3. Frontend Page Testing

### Dashboard Page (`/`)
- [ ] Page loads without errors
- [ ] Analytics data displays correctly
- [ ] Loading state shows while fetching
- [ ] Error message shows if API fails
- [ ] Currency displays as ₹ (INR)

### Users Page (`/users`)
- [ ] User list loads
- [ ] Search functionality works
- [ ] Filter by role works
- [ ] Ban/Unban actions work
- [ ] Bulk actions work
- [ ] CSV export works
- [ ] Error handling displays properly
- [ ] Loading state shows

### Orders Page (`/orders`)
- [ ] Order list loads
- [ ] Search functionality works
- [ ] Status filter works
- [ ] CSV export works
- [ ] Error handling displays properly
- [ ] Loading state shows

### Other Pages
Test each page for:
- [ ] Page loads without errors
- [ ] Data displays correctly
- [ ] Loading states work
- [ ] Error handling works
- [ ] Navigation works

## 4. Error Scenario Testing

### Network Errors
1. Stop backend server
2. Try to load any page
3. Expected: Error message displayed, no crash

### Invalid API Responses
1. Mock invalid API response
2. Expected: Error boundary catches error, displays fallback

### Invalid Query Parameters
1. Add invalid query params to URL (e.g., `?status=INVALID`)
2. Expected: Validation error or graceful handling

### Token Expiration
1. Manually expire token
2. Make API request
3. Expected: Token refresh attempted, or redirect to login

## 5. Query Parameter Validation Testing

### Test Valid Parameters
- `?is_active=true` - Should filter correctly
- `?is_active=false` - Should filter correctly
- `?status=ACTIVE` - Should filter correctly
- `?search=test` - Should search correctly

### Test Invalid Parameters
- `?is_active=invalid` - Should handle gracefully
- `?status=INVALID_STATUS` - Should handle gracefully
- `?min_value=-1` (if numeric) - Should validate range

## 6. Error Boundary Testing

1. **Trigger Error in Component**
   - Add `throw new Error('Test')` in a component
   - Expected: Error boundary catches it, displays fallback UI

2. **Recovery**
   - Click "Try Again" button
   - Expected: Component re-renders, error cleared

## 7. Serializer Testing

### Test Each ViewSet
1. Create operation - Should validate input
2. Update operation - Should validate input
3. List operation - Should return serialized data
4. Retrieve operation - Should return serialized data

### Test Missing Fields
1. Send request without required fields
2. Expected: Validation error with field names

## 8. Permission Testing

### Test Permission Checks
1. Login as non-admin user
2. Try to access admin endpoints
3. Expected: 403 Forbidden

### Test Role-Based Access
1. Create user with limited permissions
2. Test each permission
3. Expected: Only allowed actions succeed

## 9. Performance Testing

### Load Testing
1. Load dashboard with large dataset
2. Expected: Page loads within reasonable time (< 3 seconds)

### Query Optimization
1. Check database queries in Django debug toolbar
2. Expected: No N+1 queries, proper select_related/prefetch_related

## 10. Browser Compatibility

Test in:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

## Common Issues & Solutions

### Issue: 404 Error on Dashboard
**Solution**: Check that backend is running and analytics endpoint is accessible

### Issue: Token Refresh Fails
**Solution**: Check refresh token endpoint and localStorage

### Issue: Serializer Errors
**Solution**: Verify all ViewSets have serializer_class defined

### Issue: Permission Denied
**Solution**: Verify AdminUser exists and is_active=True

## Test Results Template

```
Date: [Date]
Tester: [Name]
Environment: [Development/Staging/Production]

Authentication: [PASS/FAIL]
API Endpoints: [PASS/FAIL]
Frontend Pages: [PASS/FAIL]
Error Handling: [PASS/FAIL]
Query Validation: [PASS/FAIL]
Error Boundary: [PASS/FAIL]
Permissions: [PASS/FAIL]

Notes:
[Any issues found or observations]
```

## Automated Testing (Future)

Consider adding:
- Unit tests for serializers
- Integration tests for ViewSets
- E2E tests for critical flows
- API contract tests

