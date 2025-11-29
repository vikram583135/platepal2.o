# API Endpoint Mapping Document

This document maps all frontend components to their corresponding backend API endpoints.

## Base Configuration
- **API Base URL**: `http://localhost:8000/api` (configurable via `VITE_API_BASE_URL`)
- **WebSocket URL**: `ws://localhost:8000/ws` (configurable via `VITE_WS_URL`)

---

## Authentication Endpoints (`/api/auth/`)

### Login & Registration
- **POST** `/api/auth/token/` - Login (obtain JWT tokens)
- **POST** `/api/auth/token/refresh/` - Refresh access token
- **POST** `/api/auth/users/` - User registration
- **PATCH** `/api/auth/users/{id}/` - Update user profile
- **POST** `/api/auth/users/upload_profile_photo/` - Upload profile photo
- **POST** `/api/auth/users/change_password/` - Change password
- **GET** `/api/auth/users/export-data/` - Export user data
- **POST** `/api/auth/users/delete_account/` - Delete account
- **PATCH** `/api/auth/users/preferences/` - Update user preferences

### OTP
- **POST** `/api/auth/otp/send/` - Send OTP (email/phone verification)
- **POST** `/api/auth/otp/verify/` - Verify OTP

### OAuth
- **GET/POST** `/api/auth/oauth/google/` - Google OAuth
- **GET/POST** `/api/auth/oauth/apple/` - Apple OAuth
- **GET/POST** `/api/auth/oauth/facebook/` - Facebook OAuth

### Addresses
- **GET** `/api/auth/addresses/` - List user addresses
- **POST** `/api/auth/addresses/` - Create address
- **PATCH** `/api/auth/addresses/{id}/` - Update address
- **DELETE** `/api/auth/addresses/{id}/` - Delete address

### Payment Methods
- **GET** `/api/auth/payment-methods/` - List saved payment methods
- **POST** `/api/auth/payment-methods/` - Add payment method
- **DELETE** `/api/auth/payment-methods/{id}/` - Remove payment method

### Devices & Security
- **GET** `/api/auth/devices/` - List trusted devices
- **POST** `/api/auth/devices/{id}/revoke/` - Revoke device
- **DELETE** `/api/auth/devices/{id}/` - Delete device
- **GET** `/api/auth/two-factor-auth/` - Get 2FA status
- **PATCH** `/api/auth/two-factor-auth/` - Update 2FA settings
- **POST** `/api/auth/two-factor-auth/generate-backup-codes/` - Generate backup codes

### Saved Locations
- **GET** `/api/auth/saved-locations/` - List saved locations
- **POST** `/api/auth/saved-locations/` - Save location
- **DELETE** `/api/auth/saved-locations/{id}/` - Delete saved location

---

## Restaurant Endpoints (`/api/restaurants/`)

### Restaurants
- **GET** `/api/restaurants/restaurants/` - List restaurants (with filters)
- **GET** `/api/restaurants/restaurants/{id}/` - Get restaurant details
- **GET** `/api/restaurants/restaurants/{id}/menu/` - Get restaurant menu
- **GET** `/api/restaurants/restaurants/{id}/bestsellers/` - Get bestsellers
- **GET** `/api/restaurants/restaurants/{id}/recommendations/` - Get recommendations
- **GET** `/api/restaurants/restaurants/{id}/menu_search/` - Search menu items

### Location & Search
- **POST** `/api/restaurants/location/detect/` - Detect location from coordinates
- **GET** `/api/restaurants/search/suggestions/` - Get search suggestions
- **GET** `/api/restaurants/search/popular/` - Get popular searches
- **GET** `/api/restaurants/search/recent/` - Get recent searches
- **POST** `/api/restaurants/search/save/` - Save search query
- **GET** `/api/restaurants/search/trending/` - Get trending dishes

### Promotions
- **GET** `/api/restaurants/promotions/available/` - Get available promotions
- **POST** `/api/restaurants/promotions/validate/` - Validate coupon code

---

## Order Endpoints (`/api/orders/`)

### Orders
- **GET** `/api/orders/orders/` - List user orders
- **POST** `/api/orders/orders/` - Create new order
- **GET** `/api/orders/orders/{id}/` - Get order details
- **POST** `/api/orders/orders/{id}/cancel/` - Cancel order
- **POST** `/api/orders/orders/{id}/repeat/` - Repeat order
- **GET** `/api/orders/orders/{id}/invoice/` - Get order invoice
- **GET** `/api/orders/orders/{id}/transaction/` - Get transaction details
- **GET** `/api/orders/orders/{id}/courier/` - Get courier details
- **GET** `/api/orders/orders/{id}/eta/` - Get estimated delivery time
- **GET** `/api/orders/orders/{id}/timeline/` - Get order timeline
- **POST** `/api/orders/orders/{id}/generate_delivery_otp/` - Generate delivery OTP
- **POST** `/api/orders/orders/{id}/verify_delivery_otp/` - Verify delivery OTP

### Reviews
- **GET** `/api/orders/reviews/` - List reviews (with filters)
- **POST** `/api/orders/reviews/` - Create review
- **POST** `/api/orders/reviews/{id}/upload_images/` - Upload review images

---

## Payment Endpoints (`/api/payments/`)

### Payments
- **POST** `/api/payments/create_payment_intent/` - Create payment intent
- **POST** `/api/payments/confirm_payment/` - Confirm payment
- **GET** `/api/payments/payments/` - List payments
- **GET** `/api/payments/payments/{id}/` - Get payment details

### Wallet
- **GET** `/api/payments/wallet/balance/` - Get wallet balance
- **GET** `/api/payments/wallet/history/` - Get wallet transaction history
- **POST** `/api/payments/wallet/add_money/` - Add money to wallet

### Refunds
- **GET** `/api/payments/refunds/{id}/` - Get refund details
- **GET** `/api/payments/refunds/{id}/timeline/` - Get refund timeline

---

## Notification Endpoints (`/api/notifications/`)

### Notifications
- **GET** `/api/notifications/notifications/recent/` - Get recent notifications
- **GET** `/api/notifications/notifications/unread_count/` - Get unread count
- **POST** `/api/notifications/notifications/{id}/mark_read/` - Mark notification as read
- **POST** `/api/notifications/notifications/mark_all_read/` - Mark all as read
- **DELETE** `/api/notifications/notifications/clear_all/` - Clear all read notifications

### Preferences
- **GET** `/api/notifications/notification-preferences/` - Get notification preferences
- **POST** `/api/notifications/notification-preferences/` - Create preferences
- **PATCH** `/api/notifications/notification-preferences/{id}/` - Update preferences

---

## Support Endpoints (`/api/support/`)

### Tickets
- **GET** `/api/support/tickets/` - List support tickets
- **POST** `/api/support/tickets/` - Create support ticket
- **GET** `/api/support/tickets/{id}/` - Get ticket details
- **POST** `/api/support/tickets/{id}/add_message/` - Add message to ticket
- **POST** `/api/support/tickets/{id}/close/` - Close ticket

### Chatbot
- **POST** `/api/support/chatbot/message/` - Send chatbot message
- **GET** `/api/support/chatbot/history/` - Get chatbot history

---

## Subscription Endpoints (`/api/subscriptions/`)

### Plans
- **GET** `/api/subscriptions/plans/` - List membership plans
- **GET** `/api/subscriptions/subscriptions/current/` - Get current subscription
- **POST** `/api/subscriptions/subscriptions/subscribe/` - Subscribe to plan
- **POST** `/api/subscriptions/subscriptions/{id}/cancel/` - Cancel subscription

---

## Rewards Endpoints (`/api/rewards/`)

### Loyalty
- **GET** `/api/rewards/loyalty/balance/` - Get loyalty points balance
- **GET** `/api/rewards/loyalty/history/` - Get points history
- **GET** `/api/rewards/tiers/` - List loyalty tiers
- **POST** `/api/rewards/redemptions/redeem/` - Redeem points

---

## Chat Endpoints (`/api/chat/`)

### Chat Rooms
- **POST** `/api/chat/rooms/create_or_get/` - Create or get chat room
- **GET** `/api/chat/rooms/{id}/` - Get chat room details
- **GET** `/api/chat/messages/` - List messages (with room filter)

---

## WebSocket Connections (`ws://localhost:8000/ws/`)

- **Customer**: `/ws/customer/{customer_id}/` - Customer notifications
- **Restaurant**: `/ws/orders/{restaurant_id}/` - Restaurant order updates
- **Delivery**: `/ws/delivery/{rider_id}/` - Delivery updates
- **Chat**: `/ws/chat/{room_id}/` - Chat messages

---

## Frontend Component → API Mapping

### Authentication Flow
- **LoginPage**: `/api/auth/token/`, `/api/auth/oauth/*`
- **SignupPage**: `/api/auth/users/`, `/api/auth/otp/send/`
- **OTPVerificationPage**: `/api/auth/otp/verify/`

### Navigation
- **Navbar**: `/api/notifications/notifications/unread_count/`

### Restaurant Discovery
- **HomePage**: 
  - `/api/restaurants/location/detect/`
  - `/api/restaurants/search/trending/`
  - `/api/restaurants/search/suggestions/`
  - `/api/auth/saved-locations/`
- **RestaurantsPage**: `/api/restaurants/restaurants/`
- **RestaurantDetailPage**: 
  - `/api/restaurants/restaurants/{id}/`
  - `/api/restaurants/restaurants/{id}/menu/`
  - `/api/restaurants/restaurants/{id}/bestsellers/`
  - `/api/restaurants/restaurants/{id}/recommendations/`
  - `/api/orders/reviews/?restaurant_id={id}`
- **MenuSearch**: `/api/restaurants/restaurants/{id}/menu_search/`
- **SearchSuggestions**: 
  - `/api/restaurants/search/suggestions/`
  - `/api/restaurants/search/recent/`
  - `/api/restaurants/search/popular/`

### Cart & Checkout
- **CartPage**: `/api/restaurants/promotions/validate/`
- **CheckoutPage**: 
  - `/api/auth/addresses/`
  - `/api/auth/payment-methods/`
  - `/api/restaurants/promotions/available/`
  - `/api/orders/orders/`
  - `/api/payments/create_payment_intent/`
  - `/api/payments/confirm_payment/`

### Order Management
- **OrdersPage**: `/api/orders/orders/`
- **OrderDetailPage**: 
  - `/api/orders/orders/{id}/`
  - `/api/orders/orders/{id}/invoice/`
  - `/api/orders/orders/{id}/transaction/`
  - `/api/orders/orders/{id}/repeat/`
  - `/api/orders/orders/{id}/cancel/`
  - `/api/orders/reviews/?order_id={id}`
- **OrderTrackingPage**: 
  - `/api/orders/orders/{id}/`
  - `/api/orders/orders/{id}/courier/`
  - `/api/orders/orders/{id}/eta/`
  - `/api/orders/orders/{id}/timeline/`
  - `/api/orders/orders/{id}/generate_delivery_otp/`
  - `/api/orders/orders/{id}/verify_delivery_otp/`
  - `/api/chat/rooms/create_or_get/`
  - WebSocket: `/ws/chat/{room_id}/`

### Profile & Settings
- **ProfilePage**: 
  - `/api/auth/users/{id}/`
  - `/api/auth/users/upload_profile_photo/`
  - `/api/auth/users/change_password/`
  - `/api/auth/users/export-data/`
  - `/api/auth/users/delete_account/`
  - `/api/auth/addresses/`
  - `/api/auth/devices/`
  - `/api/auth/two-factor-auth/`
- **SettingsPage**: 
  - `/api/notifications/notification-preferences/`
  - `/api/auth/users/preferences/`
- **AddressForm**: `/api/restaurants/location/detect/`

### Offers, Wallet, Rewards
- **OffersPage**: `/api/restaurants/promotions/available/`
- **WalletPage**: 
  - `/api/payments/wallet/balance/`
  - `/api/payments/wallet/history/`
  - `/api/payments/wallet/add_money/`
- **RewardsPage**: 
  - `/api/rewards/loyalty/balance/`
  - `/api/rewards/loyalty/history/`
  - `/api/rewards/tiers/`
  - `/api/rewards/redemptions/redeem/`

### Membership & Subscriptions
- **MembershipPage**: 
  - `/api/subscriptions/plans/`
  - `/api/subscriptions/subscriptions/current/`
  - `/api/subscriptions/subscriptions/subscribe/`
  - `/api/subscriptions/subscriptions/{id}/cancel/`
- **SubscriptionPage**: Same as MembershipPage

### Notifications & Support
- **NotificationsPage**: 
  - `/api/notifications/notifications/recent/`
  - `/api/notifications/notifications/unread_count/`
  - `/api/notifications/notifications/{id}/mark_read/`
  - `/api/notifications/notifications/mark_all_read/`
  - `/api/notifications/notifications/clear_all/`
- **SupportPage**: 
  - `/api/support/tickets/`
  - `/api/support/chatbot/message/`
  - `/api/support/chatbot/history/`
- **TicketDetailPage**: 
  - `/api/support/tickets/{id}/`
  - `/api/support/tickets/{id}/add_message/`
  - `/api/support/tickets/{id}/close/`

### Reviews
- **ReviewModal**: `/api/orders/reviews/`, `/api/orders/reviews/{id}/upload_images/`

---

## Expected Response Formats

### Authentication
- **Login Response**: `{ access: string, refresh: string, user: UserObject }`
- **User Object**: `{ id, email, first_name, last_name, phone, profile_photo_url, is_email_verified }`

### Restaurant
- **Restaurant List**: `{ results: Restaurant[], count, next, previous }`
- **Restaurant Object**: `{ id, name, description, rating, delivery_time_minutes, delivery_fee, ... }`

### Order
- **Order Object**: `{ id, order_number, status, items: [], subtotal, tax_amount, delivery_fee, total_amount, ... }`

### Error Responses
- **400 Bad Request**: `{ error: string, field_errors: {} }`
- **401 Unauthorized**: `{ detail: string }`
- **404 Not Found**: `{ detail: string }`
- **500 Server Error**: `{ error: string }`

---

## Testing Checklist

- [ ] All endpoints return expected status codes
- [ ] Authentication tokens are properly included in requests
- [ ] Error responses are handled correctly
- [ ] Loading states are shown during API calls
- [ ] Empty states are displayed when no data
- [ ] Form validations work correctly
- [ ] WebSocket connections establish successfully
- [ ] Real-time updates work via WebSocket

