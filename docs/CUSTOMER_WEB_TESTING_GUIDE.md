# Customer Web Application - Testing Guide

This testing guide helps you systematically test the customer web application and document bugs you encounter. Use the checkboxes to track your progress and the bug report section to document issues.

## Prerequisites

Before starting testing:
- [.] Backend server is running on `http://localhost:8000`
- [.] Frontend customer app is running (check the port from your terminal)
- [.] Redis is running (required for WebSocket connections)
- [.] PostgreSQL database is set up and migrated
- [.] Test data is seeded using `python manage.py seed_data`

### Test Accounts
- **Customer**: customer@platepal.com / customer123
- **Admin**: admin@platepal.com / admin123

---

## 1. Authentication & User Management

### 1.1 Login Page (`/login`)

#### Basic Login Flow
- [.] Page loads correctly
- [.] Email input field is visible and functional
- [.] Password input field is visible and functional (should be masked)
- [.] "Login" button is visible and clickable
- [.] "Sign up" or "Create account" link redirects to signup page

#### Login Functionality
- [.] Login with valid credentials (customer@platepal.com / customer123) works
- [.] After successful login, user is redirected to home page
- [.] User session is maintained after login
- [.] Login with invalid email shows appropriate error message
- [.] Login with wrong password shows appropriate error message
- [.] Login with empty email field shows validation error
- [.] Login with empty password field shows validation error
- [.] Login with invalid email format shows validation error

#### Social Login (if applicable)
- [.] Google login button is visible (if implemented)
- [.] Facebook login button is visible (if implemented)
- [.] Social login redirects work correctly

#### UI/UX
- [.] Form validation messages are clear and helpful
- [.] Loading state is shown during login request
- [.] Error messages are displayed prominently
- [.] Page is responsive on mobile devices

**Bugs Found:**
```
1. [.] Bug Description: 
   - Location: Login Page - [specific field/button]
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
   - Screenshot/Console Error: 
   
2. [.] Bug Description: 
   - Location: Login Page - [specific field/button]
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

---

### 1.2 Signup Page (`/signup`)

#### Basic Signup Flow
- [.] Page loads correctly
- [.] All required fields are visible (name, email, password, confirm password)
- [.] "Sign up" button is visible and clickable
- [.] "Already have an account? Login" link redirects to login page

#### Signup Functionality
- [.] Signup with valid information creates account successfully
- [.] After successful signup, user is redirected appropriately
- [.] Signup with existing email shows appropriate error
- [.] Password mismatch (password vs confirm password) shows validation error
- [.] Weak password shows validation error (if password strength check exists)
- [.] Empty required fields show validation errors
- [.] Invalid email format shows validation error

#### Form Validation
- [.] Real-time validation works for email field
- [.] Password strength indicator works (if implemented)
- [.] All validation messages are clear

**Bugs Found:**
```
1. [.] Bug Description: 
   - Location: Signup Page
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

---

### 1.3 OTP Verification (`/verify-otp`)

#### OTP Flow
- [.] OTP input fields are visible after signup
- [.] OTP can be entered correctly
- [.] Valid OTP verification works
- [.] Invalid OTP shows error message
- [.] Resend OTP button works
- [.] OTP expires after timeout (if implemented)
- [.] Auto-submit works when OTP is complete (if implemented)

**Bugs Found:**
```
1. [.] Bug Description: 
   - Location: OTP Verification Page
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

---

## 2. Home Page (`/`)

### 2.1 Page Load & Layout
- [.] Page loads without errors
- [.] Header/Navbar is visible and functional
- [.] Footer is visible
- [.] No console errors on page load
- [.] Loading skeletons appear while data is fetching
- [.] Page is responsive on different screen sizes

### 2.2 Location Features
- [.] Location picker is visible
- [.] Current location can be detected automatically
- [.] Manual location entry works
- [.] Saved locations dropdown works (if logged in)
- [.] Location change updates restaurant listings
- [.] Location permission request works correctly

**Bugs Found:**
```
1. [.] Bug Description: 
   - Location: Home Page - Location Picker
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 2.3 Search Functionality
- [ ] Search bar is visible and functional
- [ ] Search suggestions appear as you type
- [ ] Search works for restaurants
- [ ] Search works for dishes
- [ ] Search results are relevant
- [ ] "Clear search" or X button works
- [ ] Popular searches are displayed
- [ ] Recent searches are saved (if logged in)

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Home Page - Search
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 2.4 Trending Dishes Section
- [ ] Trending dishes section is visible
- [ ] Trending dishes load correctly
- [ ] Dish images load properly
- [ ] Dish names and prices are displayed correctly
- [ ] Clicking a trending dish works (opens modal or navigates)
- [ ] "View All" or similar link works (if present)
- [ ] Empty state is handled gracefully (if no trending dishes)

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Home Page - Trending Dishes
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 2.5 Restaurant Listings
- [ ] Restaurant cards are displayed
- [ ] Restaurant images load correctly
- [ ] Restaurant names, ratings, cuisines are displayed
- [ ] Restaurant cards are clickable and navigate correctly
- [ ] Filters work (if present)
- [ ] Sorting works (if present)
- [ ] Pagination or infinite scroll works
- [ ] Empty state is shown when no restaurants found

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Home Page - Restaurant Listings
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 2.6 Navigation & Links
- [ ] All navigation links work correctly
- [ ] Cart icon shows item count (if items in cart)
- [ ] Profile/Account menu works (if logged in)
- [ ] Logout works correctly

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Home Page - Navigation
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

---

## 3. Restaurants Page (`/restaurants`)

### 3.1 Page Load
- [ ] Page loads correctly
- [ ] All restaurants are listed
- [ ] No console errors

### 3.2 Restaurant Filters
- [ ] Filter by cuisine works
- [ ] Filter by rating works
- [ ] Filter by price range works
- [ ] Filter by delivery time works
- [ ] Filter by dietary preferences works (vegetarian, vegan, etc.)
- [ ] "Clear filters" button works
- [ ] Multiple filters can be applied simultaneously
- [ ] Filter state persists (if applicable)

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Restaurants Page - Filters
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 3.3 Restaurant Sorting
- [ ] Sort by rating works
- [ ] Sort by delivery time works
- [ ] Sort by price works
- [ ] Sort by distance works
- [ ] Default sort order is applied correctly

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Restaurants Page - Sorting
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 3.4 Restaurant Cards
- [ ] Restaurant information is accurate
- [ ] Images load correctly
- [ ] Ratings are displayed correctly
- [ ] Delivery time and fees are shown
- [ ] "Closed" or "Open" status is shown correctly
- [ ] Clicking a card navigates to restaurant detail page

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Restaurants Page - Restaurant Cards
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

---

## 4. Restaurant Detail Page (`/restaurants/:id`)

### 4.1 Page Load
- [ ] Page loads correctly with restaurant information
- [ ] Restaurant name, images, rating are displayed
- [ ] Address and contact information are shown
- [ ] Operating hours are displayed correctly
- [ ] No console errors

### 4.2 Menu Display
- [ ] Menu categories are listed
- [ ] Menu items are displayed correctly
- [ ] Item images load properly
- [ ] Item names, descriptions, and prices are shown
- [ ] Item availability status is shown (available/out of stock)
- [ ] Vegetarian/Non-vegetarian indicators work
- [ ] Spicy level indicators work (if present)
- [ ] Category tabs/sections work correctly

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Restaurant Detail - Menu Display
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 4.3 Adding Items to Cart
- [ ] Clicking "Add" button opens item detail modal
- [ ] Item detail modal shows all options/modifiers
- [ ] Modifiers can be selected (if applicable)
- [ ] Quantity can be increased/decreased
- [ ] "Add to Cart" button in modal works
- [ ] Item is added to cart successfully
- [ ] Cart count updates in header
- [ ] Success message/toast appears (if implemented)
- [ ] Adding same item with different modifiers creates separate cart items

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Restaurant Detail - Add to Cart
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 4.4 Item Detail Modal
- [ ] Modal opens when clicking an item
- [ ] Item image, name, description are shown
- [ ] Price is displayed correctly
- [ ] All modifiers/options are listed
- [ ] Required modifiers are enforced
- [ ] Optional modifiers can be selected
- [ ] Price updates when modifiers are selected
- [ ] Quantity selector works (+ and - buttons)
- [ ] "Add to Cart" button works
- [ ] Close button or clicking outside closes modal
- [ ] Modal is scrollable for long content

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Restaurant Detail - Item Detail Modal
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 4.5 Reviews & Ratings
- [ ] Reviews section is visible
- [ ] Reviews are displayed correctly
- [ ] Ratings breakdown is shown
- [ ] Can filter reviews by rating
- [ ] Can sort reviews (newest, highest, lowest)
- [ ] Review pagination works (if applicable)
- [ ] Can write a review (if logged in and ordered)
- [ ] Review submission works

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Restaurant Detail - Reviews
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 4.6 Other Features
- [ ] "Favorite" or "Save" restaurant works (if implemented)
- [ ] Share restaurant functionality works
- [ ] Directions/Map integration works
- [ ] Photos gallery works (if present)

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Restaurant Detail - [Feature Name]
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

---

## 5. Cart Page (`/cart`)

### 5.1 Cart Display
- [ ] All cart items are displayed correctly
- [ ] Item names, quantities, and prices are shown
- [ ] Item images are displayed
- [ ] Modifiers/options selected are shown
- [ ] Subtotal, taxes, delivery fees are calculated correctly
- [ ] Total amount is calculated correctly
- [ ] Empty cart message is shown when cart is empty
- [ ] "Continue Shopping" link works

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Cart Page - Display
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 5.2 Cart Management
- [ ] Quantity can be increased
- [ ] Quantity can be decreased
- [ ] Item is removed when quantity reaches 0
- [ ] "Remove" or delete button removes item from cart
- [ ] Cart persists after page refresh (if implemented)
- [ ] Cart is cleared after successful order (if applicable)
- [ ] Multiple items from different restaurants shows appropriate message (if not allowed)

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Cart Page - Cart Management
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 5.3 Proceed to Checkout
- [ ] "Proceed to Checkout" button is visible
- [ ] Button is disabled when cart is empty
- [ ] Button redirects to checkout page when clicked
- [ ] If not logged in, user is redirected to login first

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Cart Page - Checkout Button
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

---

## 6. Checkout Page (`/checkout`)

### 6.1 Page Access
- [ ] Page requires authentication
- [ ] Unauthenticated users are redirected to login
- [ ] Page loads with cart items

### 6.2 Delivery Address
- [ ] Saved addresses are displayed (if any)
- [ ] Can select a saved address
- [ ] Can add a new address
- [ ] Address form validation works
- [ ] Address can be edited
- [ ] Address can be deleted
- [ ] Location picker works for address
- [ ] Delivery instructions field works

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Checkout - Delivery Address
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 6.3 Order Summary
- [ ] All items are listed with correct quantities
- [ ] Prices are displayed correctly
- [ ] Subtotal is calculated correctly
- [ ] Delivery fee is shown correctly
- [ ] Taxes are calculated correctly
- [ ] Discount/promo code is applied correctly (if applicable)
- [ ] Total amount is correct

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Checkout - Order Summary
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 6.4 Payment Method
- [ ] Payment method selector is visible
- [ ] Can select payment method (Credit Card, UPI, Wallet, Cash on Delivery)
- [ ] Payment form appears for selected method
- [ ] Card details form validation works (if credit card)
- [ ] UPI ID validation works
- [ ] Wallet balance is shown correctly
- [ ] Insufficient wallet balance shows error

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Checkout - Payment Method
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 6.5 Promo Codes & Offers
- [ ] Promo code input field is visible
- [ ] Can enter a promo code
- [ ] Valid promo code applies discount
- [ ] Invalid promo code shows error
- [ ] Expired promo code shows error
- [ ] Discount is reflected in order summary
- [ ] "Remove" promo code works

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Checkout - Promo Codes
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 6.6 Place Order
- [ ] "Place Order" button is visible
- [ ] Button is disabled when required fields are missing
- [ ] Order placement works successfully
- [ ] Loading state is shown during order placement
- [ ] Success message appears
- [ ] Redirect to order confirmation/tracking works
- [ ] Order confirmation details are correct
- [ ] Error handling works for failed orders

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Checkout - Place Order
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

---

## 7. Orders Page (`/orders`)

### 7.1 Page Access
- [ ] Page requires authentication
- [ ] Page loads correctly

### 7.2 Orders Display
- [ ] All orders are listed
- [ ] Order status is displayed correctly (Pending, Confirmed, Preparing, Out for Delivery, Delivered, Cancelled)
- [ ] Order date and time are shown
- [ ] Restaurant name is displayed
- [ ] Order total is shown
- [ ] Order items summary is shown
- [ ] "View Details" or "Track Order" buttons work
- [ ] Empty state is shown when no orders
- [ ] Orders are sorted (newest first, typically)

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Orders Page - Display
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 7.3 Order Filtering/Sorting
- [ ] Can filter orders by status
- [ ] Can filter orders by date range (if implemented)
- [ ] Can sort orders (if implemented)
- [ ] Filter state persists

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Orders Page - Filtering
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 7.4 Order Actions
- [ ] Can cancel pending orders
- [ ] Cancellation confirmation works
- [ ] Can reorder from past orders
- [ ] Can contact support for an order

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Orders Page - Actions
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

---

## 8. Order Detail Page (`/orders/:id`)

### 8.1 Page Load
- [ ] Page loads with correct order details
- [ ] Order number/ID is displayed
- [ ] Order status is shown
- [ ] Order date and time are correct

### 8.2 Order Information
- [ ] Restaurant name and details are shown
- [ ] Delivery address is displayed correctly
- [ ] All order items are listed with correct quantities
- [ ] Item prices are correct
- [ ] Modifiers/options are shown
- [ ] Payment method is displayed
- [ ] Payment status is shown
- [ ] Subtotal, fees, taxes, total are displayed correctly

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Order Detail - Information
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 8.3 Order Actions
- [ ] "Track Order" button works
- [ ] "Cancel Order" button works (if order can be cancelled)
- [ ] "Reorder" button works
- [ ] "Rate & Review" button works (if order is delivered)
- [ ] "Contact Support" button works

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Order Detail - Actions
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

---

## 9. Order Tracking Page (`/orders/:id/track`)

### 9.1 Real-time Tracking
- [ ] Order status updates in real-time (via WebSocket)
- [ ] Status timeline/progress bar is displayed
- [ ] Current status is highlighted
- [ ] Estimated delivery time is shown
- [ ] Rider information is displayed (when assigned)

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Order Tracking - Real-time Updates
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 9.2 Map Integration
- [ ] Map is displayed (if implemented)
- [ ] Restaurant location is marked
- [ ] Delivery address is marked
- [ ] Rider location updates in real-time (if available)
- [ ] Route is displayed (if applicable)

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Order Tracking - Map
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 9.3 Contact Features
- [ ] "Call Restaurant" button works
- [ ] "Call Rider" button works (when assigned)
- [ ] "Contact Support" button works

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Order Tracking - Contact
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

---

## 10. Profile Page (`/profile`)

### 10.1 Profile Information
- [ ] Name, email, phone are displayed
- [ ] Profile picture is shown (if present)
- [ ] Can edit profile information
- [ ] Profile update works
- [ ] Validation works for email, phone

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Profile Page - Information
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 10.2 Saved Addresses
- [ ] Saved addresses are listed
- [ ] Can add new address
- [ ] Can edit existing address
- [ ] Can delete address
- [ ] Can set default address
- [ ] Address validation works

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Profile Page - Saved Addresses
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

---

## 11. Settings Page (`/settings`)

### 11.1 Account Settings
- [ ] Can change password
- [ ] Password change validation works
- [ ] Can update email
- [ ] Email verification works (if required)

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Settings Page - Account Settings
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 11.2 Notification Settings
- [ ] Notification preferences are displayed
- [ ] Can toggle email notifications
- [ ] Can toggle push notifications
- [ ] Can toggle SMS notifications
- [ ] Settings are saved correctly

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Settings Page - Notifications
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 11.3 Privacy & Security
- [ ] Privacy settings are accessible
- [ ] Can manage data sharing preferences
- [ ] Can delete account (if implemented)

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Settings Page - Privacy
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

---

## 12. Offers Page (`/offers`)

### 12.1 Offers Display
- [ ] All available offers are displayed
- [ ] Offer details (discount, validity, terms) are shown
- [ ] Valid offers are shown
- [ ] Expired offers are marked or hidden
- [ ] "Apply" or "Copy Code" button works

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Offers Page
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

---

## 13. Wallet Page (`/wallet`)

### 13.1 Wallet Balance
- [ ] Current wallet balance is displayed
- [ ] Transaction history is shown
- [ ] Transactions are sorted (newest first)
- [ ] Transaction details are accurate

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Wallet Page - Balance
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 13.2 Add Money
- [ ] "Add Money" button/feature works
- [ ] Payment gateway integration works
- [ ] Money is added to wallet after successful payment
- [ ] Transaction is recorded

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Wallet Page - Add Money
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

---

## 14. Notifications Page (`/notifications`)

### 14.1 Notifications Display
- [ ] All notifications are listed
- [ ] Notifications are sorted (newest first)
- [ ] Unread notifications are marked
- [ ] Notification content is displayed correctly
- [ ] Timestamps are shown correctly

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Notifications Page
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 14.2 Notification Actions
- [ ] Can mark notification as read
- [ ] Can mark all as read
- [ ] Can delete notification
- [ ] Clicking notification navigates to relevant page
- [ ] Real-time notifications appear (via WebSocket)

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Notifications Page - Actions
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

---

## 15. Support Page (`/support`)

### 15.1 Support Tickets
- [ ] Support tickets are listed
- [ ] Ticket status is displayed
- [ ] Can create new ticket
- [ ] Ticket form validation works
- [ ] Ticket submission works

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Support Page
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 15.2 Chat/Help
- [ ] Chat widget is accessible
- [ ] Can send messages
- [ ] Can receive messages
- [ ] Chat history is maintained

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Support Page - Chat
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

---

## 16. Membership Page (`/membership`)

### 16.1 Membership Plans
- [ ] Available membership plans are displayed
- [ ] Plan benefits are listed
- [ ] Pricing is shown correctly
- [ ] Can subscribe to a plan
- [ ] Payment processing works
- [ ] Current membership status is shown (if subscribed)

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Membership Page
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

---

## 17. Rewards Page (`/rewards`)

### 17.1 Rewards Display
- [ ] Points balance is shown
- [ ] Rewards history is displayed
- [ ] Available rewards are listed
- [ ] Can redeem rewards
- [ ] Points are deducted after redemption

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Rewards Page
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

---

## 18. Common Features & Components

### 18.1 Navigation (Navbar/Header)
- [ ] Logo/home link works
- [ ] All menu items are clickable
- [ ] Cart icon shows correct item count
- [ ] User menu dropdown works
- [ ] Logout works correctly
- [ ] Responsive menu works on mobile

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Navigation
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 18.2 Footer
- [ ] Footer links work
- [ ] Social media links work (if present)
- [ ] Contact information is correct
- [ ] Footer is responsive

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Footer
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 18.3 Offline Functionality
- [ ] Offline banner appears when internet is disconnected
- [ ] Appropriate message is shown
- [ ] Cached content is accessible
- [ ] Connection status updates when back online

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Offline Functionality
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 18.4 Loading States
- [ ] Loading spinners appear during API calls
- [ ] Skeleton loaders are displayed (if implemented)
- [ ] Loading states don't block UI unnecessarily

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Loading States
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 18.5 Error Handling
- [ ] Network errors are handled gracefully
- [ ] 404 errors show appropriate page
- [ ] 500 errors show error message
- [ ] API errors show user-friendly messages
- [ ] Error messages are actionable

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Error Handling
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

---

## 19. Performance & Usability

### 19.1 Performance
- [ ] Pages load within reasonable time (< 3 seconds)
- [ ] Images are optimized and load quickly
- [ ] No unnecessary API calls
- [ ] Smooth scrolling and animations
- [ ] No lag when interacting with UI

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Performance
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 19.2 Responsive Design
- [ ] Works on desktop (1920x1080, 1366x768)
- [ ] Works on tablet (768x1024)
- [ ] Works on mobile (375x667, 414x896)
- [ ] Landscape orientation works
- [ ] No horizontal scrolling
- [ ] Text is readable on all screen sizes
- [ ] Touch targets are large enough on mobile

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Responsive Design - [Device/Size]
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 19.3 Accessibility
- [ ] Keyboard navigation works
- [ ] Focus indicators are visible
- [ ] Screen reader compatible (if tested)
- [ ] Color contrast is sufficient
- [ ] Alt text for images (if applicable)

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Accessibility
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 19.4 Browser Compatibility
- [ ] Works on Chrome (latest)
- [ ] Works on Firefox (latest)
- [ ] Works on Safari (latest)
- [ ] Works on Edge (latest)
- [ ] Works on mobile browsers (Chrome, Safari)

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Browser Compatibility - [Browser Name]
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

---

## 20. WebSocket/Real-time Features

### 20.1 Order Updates
- [ ] Order status updates in real-time
- [ ] Notification appears when order status changes
- [ ] Connection is stable
- [ ] Reconnection works if connection drops

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: WebSocket - Order Updates
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 20.2 Chat
- [ ] Messages are sent in real-time
- [ ] Messages are received in real-time
- [ ] Connection status is shown
- [ ] Message history loads correctly

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: WebSocket - Chat
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

---

## 21. Security & Data Validation

### 21.1 Authentication Security
- [ ] Session expires after timeout
- [ ] JWT tokens are handled correctly
- [ ] Logout clears session
- [ ] Protected routes require authentication
- [ ] Can't access other users' data

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Security - Authentication
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

### 21.2 Input Validation
- [ ] XSS attacks are prevented
- [ ] SQL injection is prevented (client-side validation)
- [ ] Form inputs are sanitized
- [ ] File uploads are validated (if applicable)

**Bugs Found:**
```
1. [ ] Bug Description: 
   - Location: Security - Input Validation
   - Steps to Reproduce: 
   - Expected: 
   - Actual: 
```

---

## Summary

### Testing Completed On:
- Date: _______________
- Tester Name: _______________
- Browser: _______________
- Device: _______________

### Overall Status:
- Total Test Cases: ______
- Passed: ______
- Failed: ______
- Not Tested: ______

### Critical Bugs Found:
1. _______________________________
2. _______________________________
3. _______________________________

### Priority Bugs Found:
1. _______________________________
2. _______________________________
3. _______________________________

### Notes:
_____________________________________________
_____________________________________________
_____________________________________________

---

## Bug Report Template

For each bug found, please use this template:

```
**Bug ID:** [Unique identifier or ticket number]

**Title:** [Brief description of the bug]

**Severity:** [Critical / High / Medium / Low]

**Priority:** [P0 / P1 / P2 / P3]

**Component:** [Page/Component name]

**Steps to Reproduce:**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happens]

**Screenshots/Videos:**
[Attach screenshots or videos if available]

**Console Errors:**
[Any JavaScript console errors]

**Network Errors:**
[Any API call failures or network errors]

**Browser/Device:**
[Browser name and version, device details]

**Environment:**
[Development / Staging / Production]

**Additional Notes:**
[Any other relevant information]
```

---

## Testing Tips

1. **Test with different user roles:** Make sure to test as a new user, returning user, and user with various order histories.

2. **Test edge cases:** Empty states, error states, network failures, slow connections.

3. **Test on different devices:** Desktop, tablet, mobile.

4. **Clear cache and cookies:** Test fresh user experience.

5. **Test with slow network:** Use browser DevTools to throttle network speed.

6. **Check console:** Always check browser console for errors.

7. **Test in incognito mode:** To avoid cached data or extensions interfering.

8. **Document everything:** Screenshots, videos, console logs help developers fix bugs faster.

9. **Test payment flows carefully:** Even if using mock payment, test all payment method options.

10. **Test real-time features:** Make sure WebSocket connections work and update properly.

---

**End of Testing Guide**

