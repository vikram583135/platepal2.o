<!-- 36769149-15e4-456d-a84e-dd6ca0921c72 db696a35-b6a3-4344-82ce-944a8044f261 -->
# Fix Checkout Flow Issues

## Overview

The checkout flow has multiple issues affecting address selection, payment method handling, order creation, API integrations, and data validation. This plan addresses all identified problems systematically.

## Issues Identified

1. **Address Selection & Validation**

- No default address auto-selection when addresses exist
- Missing validation for address selection before order placement
- Address API endpoint path verification needed

2. **Payment Method Handling**

- Payment details (card, UPI ID, wallet provider) collected but not sent to backend
- Payment method validation missing
- Saved card selection not properly integrated with payment flow

3. **Order Creation Flow**

- Payment method not included in order creation payload
- Payment intent creation happens after order creation (potential orphaned orders)
- Missing validation for required fields before submission

4. **API Endpoint Issues**

- Promotions endpoint: `/restaurants/promotions/available/` - needs verification
- Addresses endpoint: `/auth/addresses/` - needs verification  
- Payment methods endpoint: `/auth/payment-methods/` - needs verification
- Error handling for API failures

5. **Data Validation**

- Tip amount can be negative or extremely large
- Custom tip input lacks proper validation
- Order items structure validation

6. **User Experience**

- No loading states during API calls
- Error messages not user-friendly
- Missing success feedback

## Implementation Steps

### Step 1: Fix Address Selection & Auto-Selection

**File**: `frontend/apps/customer/src/pages/CheckoutPage.tsx`

- Auto-select first address if available and none selected
- Auto-select default address if exists
- Add validation to prevent order placement without address
- Verify API endpoint `/auth/addresses/` is correct

### Step 2: Fix Payment Method Integration

**Files**:

- `frontend/apps/customer/src/pages/CheckoutPage.tsx`
- `frontend/apps/customer/src/components/PaymentMethodSelector.tsx`
- Add payment details (card data, UPI ID, wallet provider) to state
- Pass payment details to payment intent creation
- Validate payment method selection before order placement
- Handle saved card selection properly

### Step 3: Fix Order Creation & Payment Flow

**File**: `frontend/apps/customer/src/pages/CheckoutPage.tsx`

- Include payment method in order creation if required by backend
- Improve error handling for order creation failures
- Handle payment intent creation errors gracefully
- Add proper loading states

### Step 4: Fix API Endpoint Integration

**Files**:

- `frontend/apps/customer/src/pages/CheckoutPage.tsx`
- Verify all API endpoints are correct:
- `/auth/addresses/` → Check accounts URLs
- `/auth/payment-methods/` → Check accounts URLs
- `/restaurants/promotions/available/` → Check restaurants URLs
- `/orders/orders/` → Check orders URLs
- `/payments/create_payment_intent/` → Check payments URLs
- `/payments/confirm_payment/` → Check payments URLs
- Add proper error handling for each API call
- Handle network errors and timeouts

### Step 5: Add Data Validation

**File**: `frontend/apps/customer/src/pages/CheckoutPage.tsx`

- Validate tip amount (non-negative, reasonable max)
- Validate payment method selection
- Validate address selection
- Validate cart is not empty
- Validate restaurant ID exists

### Step 6: Improve User Experience

**File**: `frontend/apps/customer/src/pages/CheckoutPage.tsx`

- Add loading spinners for async operations
- Improve error messages (user-friendly)
- Add success notifications
- Disable form during submission
- Show progress indicators

### Step 7: Backend Verification & Fixes

**Files**:

- `backend/apps/orders/serializers.py` - Verify order creation accepts all fields
- `backend/apps/payments/views.py` - Verify payment intent creation
- `backend/apps/restaurants/views.py` - Verify promotions endpoint
- `backend/apps/accounts/views.py` - Verify addresses and payment methods endpoints
- Fix any backend validation issues
- Add proper error responses

### Step 8: Test Complete Flow

- Test with no addresses → should prompt to add address
- Test with addresses → should auto-select default
- Test each payment method (CARD, UPI, WALLET, NET_BANKING, CASH)
- Test with saved cards
- Test with new card entry
- Test tip selection (preset and custom)
- Test contactless delivery toggle
- Test order creation success
- Test order creation failure scenarios
- Test payment processing success
- Test payment processing failure
- Test promotions loading
- Test error handling for all API failures

## Files to Modify

1. `frontend/apps/customer/src/pages/CheckoutPage.tsx` - Main fixes
2. `frontend/apps/customer/src/components/PaymentMethodSelector.tsx` - Payment details handling
3. `backend/apps/orders/serializers.py` - Order validation (if needed)
4. `backend/apps/payments/views.py` - Payment processing (if needed)
5. `backend/apps/restaurants/views.py` - Promotions endpoint (if needed)
6. `backend/apps/accounts/views.py` - Address/payment method endpoints (if needed)

## Success Criteria

- Address auto-selection works correctly
- All payment methods work end-to-end
- Order creation succeeds with proper validation
- Payment processing works for all methods
- All API endpoints return correct data
- Error handling provides clear feedback
- User experience is smooth with proper loading states
- All edge cases are handled gracefully

### To-dos

- [x] Set up test environment and create API endpoint mapping document
- [x] Verify and fix authentication flow (Login, Signup, OTP)
- [x] Verify and fix navigation components (Navbar, Footer, Layout)
- [x] Verify and fix restaurant discovery components (HomePage, RestaurantsPage, RestaurantDetailPage)
- [x] Verify and fix cart and checkout flow (CartPage, CheckoutPage, ItemDetailModal, PaymentMethodSelector)
- [x] Verify and fix order management (OrdersPage, OrderDetailPage, OrderTrackingPage)
- [x] Verify and fix profile and settings (ProfilePage, SettingsPage, AddressForm)
- [x] Verify and fix offers, wallet, and rewards pages
- [x] Verify and fix notifications and support pages
- [x] Verify and fix all shared components (LocationPicker, ChatWidget, etc.)
- [x] Implement and verify error handling across all components
- [x] Perform end-to-end testing of complete user flows
- [x] Fix all identified bugs and issues
- [x] Final verification and cross-browser testing