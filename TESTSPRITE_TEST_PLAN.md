# TestSprite Test Plan for PlatePal

This document outlines the test plan for testing the PlatePal food delivery platform using TestSprite.

## Project Overview

**PlatePal** is a full-stack food ordering platform with:
- **Backend**: Django REST Framework (port 8000)
- **Frontend Apps**:
  - Customer App: http://localhost:3020
  - Restaurant App: http://localhost:3021
  - Delivery App: http://localhost:3022
  - Admin App: http://localhost:3023

## Prerequisites

✅ **Backend Server**: Running on http://localhost:8000
✅ **Test Accounts**: Available (see below)
✅ **TestSprite MCP**: Installed and configured

## Test Accounts

### Customer Account
- **Email**: customer@platepal.com
- **Password**: customer123
- **App URL**: http://localhost:3020

### Restaurant Account
- **Email**: restaurant@platepal.com
- **Password**: restaurant123
- **App URL**: http://localhost:3021

### Admin Account
- **Email**: admin@platepal.com
- **Password**: admin123
- **App URL**: http://localhost:3023

### Delivery Rider Account
- **Email**: rider@platepal.com
- **Password**: rider123
- **App URL**: http://localhost:3022

## Test Scenarios

### 1. Customer Authentication Flow

**Objective**: Verify customer login and registration functionality

**Steps**:
1. Navigate to http://localhost:3020
2. Test login with valid credentials (customer@platepal.com / customer123)
3. Verify successful login redirects to home page
4. Test login with invalid credentials
5. Verify error messages are displayed
6. Test registration flow (if available)
7. Verify session persistence after page refresh

**Expected Results**:
- ✅ Login succeeds with valid credentials
- ✅ Redirect to home page after login
- ✅ Error messages shown for invalid credentials
- ✅ Session maintained after refresh

---

### 2. Restaurant Browsing and Search

**Objective**: Test restaurant discovery and search functionality

**Steps**:
1. Login as customer
2. Browse restaurant listings on home page
3. Test search functionality (search by name, cuisine)
4. Test filters (cuisine type, rating, price range)
5. Click on a restaurant card
6. Verify restaurant detail page loads
7. Verify menu items are displayed

**Expected Results**:
- ✅ Restaurant cards display correctly
- ✅ Search returns relevant results
- ✅ Filters work correctly
- ✅ Restaurant detail page loads with menu

---

### 3. Order Placement Flow

**Objective**: Test complete order placement from cart to confirmation

**Steps**:
1. Login as customer
2. Select a restaurant
3. Add multiple items to cart
4. View cart and verify items
5. Proceed to checkout
6. Enter/select delivery address
7. Select payment method
8. Place order
9. Verify order confirmation page

**Expected Results**:
- ✅ Items added to cart successfully
- ✅ Cart displays correct items and totals
- ✅ Checkout flow completes
- ✅ Order confirmation shows correct details
- ✅ Order appears in orders list

---

### 4. Restaurant Dashboard - Order Management

**Objective**: Test restaurant owner's ability to manage orders

**Steps**:
1. Login as restaurant owner (restaurant@platepal.com)
2. Navigate to orders dashboard
3. View pending orders
4. Accept an order
5. Update order status (Preparing → Ready → Out for Delivery)
6. Verify status updates reflect in real-time

**Expected Results**:
- ✅ Orders list displays correctly
- ✅ Can accept/reject orders
- ✅ Order status updates work
- ✅ Real-time updates via WebSocket

---

### 5. Order Tracking

**Objective**: Test real-time order tracking functionality

**Steps**:
1. Login as customer
2. Place an order (or use existing order)
3. Navigate to order tracking page
4. Verify order status timeline
5. Test WebSocket connection for real-time updates
6. Verify map integration (if available)
7. Test contact buttons (Call Restaurant, Call Rider)

**Expected Results**:
- ✅ Order tracking page loads
- ✅ Status updates in real-time
- ✅ WebSocket connection stable
- ✅ Timeline shows correct progress

---

### 6. Admin Panel Functionality

**Objective**: Test admin interface features

**Steps**:
1. Login as admin (admin@platepal.com)
2. View analytics dashboard
3. Navigate to user management
4. View orders list
5. Test restaurant management
6. Verify permissions and access control

**Expected Results**:
- ✅ Dashboard displays analytics
- ✅ User management works
- ✅ Orders can be viewed and managed
- ✅ Proper access control enforced

---

### 7. Payment Processing

**Objective**: Test payment flow with different payment methods

**Steps**:
1. Login as customer
2. Add items to cart
3. Proceed to checkout
4. Test different payment methods:
   - Credit Card
   - UPI
   - Wallet
   - Cash on Delivery
5. Complete payment
6. Verify payment confirmation

**Expected Results**:
- ✅ All payment methods available
- ✅ Payment forms validate correctly
- ✅ Payment processing completes
- ✅ Confirmation displayed

---

### 8. API Endpoint Testing

**Objective**: Test backend API endpoints

**Endpoints to Test**:
- `POST /api/accounts/login/` - Authentication
- `GET /api/restaurants/` - List restaurants
- `GET /api/restaurants/{id}/` - Restaurant details
- `GET /api/restaurants/{id}/menu/` - Menu items
- `POST /api/orders/` - Create order
- `GET /api/orders/` - List orders
- `GET /api/orders/{id}/` - Order details
- `GET /api/orders/{id}/track/` - Order tracking

**Expected Results**:
- ✅ All endpoints return correct status codes
- ✅ Authentication required for protected endpoints
- ✅ Data returned in correct format
- ✅ Error handling works correctly

---

### 9. Responsive Design Testing

**Objective**: Verify application works on different screen sizes

**Devices to Test**:
- Desktop (1920x1080, 1366x768)
- Tablet (768x1024)
- Mobile (375x667, 414x896)

**Expected Results**:
- ✅ Layout adapts to screen size
- ✅ Touch targets are appropriate
- ✅ No horizontal scrolling
- ✅ Text is readable

---

### 10. WebSocket/Real-time Features

**Objective**: Test real-time communication features

**Features to Test**:
- Order status updates
- Chat functionality (if available)
- Notification delivery
- Connection stability
- Reconnection after disconnect

**Expected Results**:
- ✅ Real-time updates work
- ✅ WebSocket connection stable
- ✅ Reconnection works automatically
- ✅ Notifications delivered promptly

---

## Test Execution Instructions

### Using TestSprite MCP

1. **Start TestSprite Session**:
   - In Cursor, ask: "Can you test this project with TestSprite?"
   - TestSprite will guide you through the setup

2. **Configure Test Parameters**:
   - Select testing type: Frontend + Backend
   - Enter application URLs:
     - Customer App: http://localhost:3020
     - Backend API: http://localhost:8000/api
   - Provide test account credentials

3. **Run Tests**:
   - TestSprite will execute automated tests
   - Review test results and reports
   - Document any bugs found

### Manual Testing Checklist

If TestSprite MCP is not available, use the manual testing checklist in `docs/CUSTOMER_WEB_TESTING_GUIDE.md`.

---

## Bug Reporting Template

When bugs are found during testing:

```markdown
**Bug ID**: [Unique identifier]

**Title**: [Brief description]

**Severity**: [Critical / High / Medium / Low]

**Component**: [Page/Feature name]

**Steps to Reproduce**:
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior**: [What should happen]

**Actual Behavior**: [What actually happens]

**Screenshots**: [If available]

**Console Errors**: [Any JavaScript errors]

**Browser/Device**: [Browser and version]
```

---

## Test Coverage Goals

- **Authentication**: 100%
- **Order Flow**: 100%
- **Restaurant Management**: 80%
- **Payment Processing**: 90%
- **Real-time Features**: 85%
- **API Endpoints**: 90%
- **Responsive Design**: 75%

---

## Next Steps

1. ✅ TestSprite MCP installed and configured
2. ✅ Test configuration file created (`testsprite-config.json`)
3. ⏳ Start TestSprite testing session
4. ⏳ Execute test scenarios
5. ⏳ Document results and bugs
6. ⏳ Generate test report

---

## Additional Resources

- **API Documentation**: http://localhost:8000/api/docs/
- **Testing Guide**: `docs/CUSTOMER_WEB_TESTING_GUIDE.md`
- **TestSprite Config**: `testsprite-config.json`
- **Restaurant Credentials**: `docs/RESTAURANT_CREDENTIALS.md`

---

**Last Updated**: $(Get-Date -Format "yyyy-MM-dd")
**Test Plan Version**: 1.0

