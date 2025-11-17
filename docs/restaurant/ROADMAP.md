# Restaurant Dashboard Feature Roadmap

## Current Implementation Status

### ✅ Backend - Already Implemented

#### 1. Onboarding & Profile Setup
- ✅ Restaurant signup with OTP verification (`RestaurantSignupView`)
- ✅ Restaurant model with profile metadata (cuisine multiselect, veg flags, FSSAI, GST, delivery radius, manager contacts, prep-time)
- ✅ `RestaurantBranch` model for multi-outlet support
- ✅ `ManagerProfile` model with roles and permissions
- ✅ `RestaurantSettings` model for operational configuration
- ✅ Onboarding wizard API (`RestaurantOnboardingViewSet`)

#### 2. Document/KYC Workflow
- ✅ `RestaurantDocument` model (PAN, GST, FSSAI, bank proofs)
- ✅ `DocumentReviewLog` for audit trail
- ✅ Document upload endpoints with status transitions
- ✅ Re-upload functionality

#### 3. Dashboard KPIs & Alerts
- ✅ `RestaurantDashboardView` with KPIs (orders, sales, ratings, inventory)
- ✅ `RestaurantAlert` model and viewset
- ✅ Alert generators (low stock, new reviews, SLA breach)
- ✅ Online/offline status toggle

#### 4. Live Orders & WebSockets
- ✅ Order queue endpoints grouped by status
- ✅ Order actions (accept/decline, start preparing, mark ready)
- ✅ WebSocket consumers for real-time updates
- ✅ SLA breach detection
- ✅ Order timers and metrics

#### 5. KDS & Kitchen Ops
- ✅ KDS board endpoint (`kds_board`)
- ✅ Order grouping by status
- ✅ Timer calculations

#### 6. Menu Management
- ✅ Menu, Category, Item models
- ✅ Item modifiers/add-ons
- ✅ Veg/non-veg tags, bestseller flag, availability windows
- ✅ Inventory toggle on items
- ✅ Diet/spice metadata

#### 7. Inventory Management
- ✅ `InventoryItem` model
- ✅ `StockMovement` tracking
- ✅ `RecipeItem` for ingredient consumption
- ✅ Low stock alerts
- ✅ Inventory APIs

#### 8. Reviews
- ✅ Review model with restaurant/food/delivery ratings
- ✅ Item-level reviews
- ✅ Restaurant reply functionality

#### 9. Promotions
- ✅ `Promotion` model with multiple discount types
- ✅ Platform/restaurant/bank/UPI offers
- ✅ Promotion validation endpoints

### ⚠️ Backend - Partially Implemented / Needs Enhancement

#### 1. Menu Variants & Add-ons
- ⚠️ Basic `ItemModifier` exists but needs variant groups
- ⚠️ Missing `MenuVariantGroup`, `MenuVariantOption`, `MenuAddonGroup`
- ⚠️ Missing combo offers model
- ⚠️ Missing CSV import/export endpoints

#### 2. Finance & Settlements
- ⚠️ Payment model exists but missing settlement cycle tracking
- ⚠️ Missing `SettlementCycle`, `Payout`, `ReconciliationReport` models
- ⚠️ Missing detailed finance reporting endpoints

#### 3. Operations Tools
- ⚠️ Missing `StaffAccount` model (separate from ManagerProfile)
- ⚠️ Missing `ShiftSchedule` model
- ⚠️ Missing `PackagingStock` model
- ⚠️ Missing `PrinterConfig` model
- ⚠️ Missing auto-close logic for no active shifts

#### 4. Security & Compliance
- ⚠️ Basic permissions exist but missing 2FA enforcement
- ⚠️ Missing device/session logging
- ⚠️ Missing suspicious login detection
- ⚠️ Missing GST/FSSAI renewal reminders

#### 5. KDS Enhancements
- ⚠️ Basic KDS endpoint exists but missing:
  - Rush indicators
  - Keyboard shortcut mappings
  - Print docket endpoints
  - Full-screen optimizations

#### 6. Communication
- ⚠️ Chat models exist but missing:
  - Predefined responses
  - Automated "order ready" messages
  - Call intent tracking

#### 7. Analytics & Reports
- ⚠️ Basic analytics exist but missing:
  - Menu insights (top sellers, low performers)
  - Customer insights (returning vs new, CLV)
  - Operational insights (avg prep time, peak hours)
  - PDF/CSV/Excel export functionality

### ❌ Backend - Not Implemented

#### 1. Advanced Features
- ❌ Predictive prep-time service
- ❌ Auto item tagging using AI
- ❌ Automated pricing suggestions
- ❌ AI review reply generator
- ❌ Multi-branch unified dashboard
- ❌ Dine-in QR ordering
- ❌ Kitchen robotics integration hooks

### ✅ Frontend - Already Implemented

- ✅ Basic restaurant app structure
- ✅ Login page
- ✅ Dashboard page (basic)
- ✅ Orders page (basic)
- ✅ Menu page (placeholder)

### ❌ Frontend - Not Implemented

#### 1. UI/UX
- ❌ Zomato-style red color palette
- ❌ Dark mode support
- ❌ Responsive design optimizations

#### 2. Onboarding
- ❌ Onboarding wizard UI
- ❌ Multi-step form with progress tracker
- ❌ Document upload interface

#### 3. Dashboard
- ❌ Enhanced KPI cards
- ❌ Alert center
- ❌ Real-time feed widget
- ❌ Online/offline toggle UI

#### 4. Orders Management
- ❌ Kanban-style order board
- ❌ Drag-and-drop between stages
- ❌ Order detail modals
- ❌ Cooking notes interface
- ❌ Combine orders feature
- ❌ Print docket UI

#### 5. KDS
- ❌ Full-screen KDS view
- ❌ Large-format tiles
- ❌ Keyboard shortcuts
- ❌ Audio alerts
- ❌ Offline mode

#### 6. Menu Management
- ❌ Full menu CRUD interface
- ❌ Category management
- ❌ Variant/add-on management
- ❌ CSV import/export UI
- ❌ Menu insights dashboard

#### 7. New Pages Needed
- ❌ Inventory page
- ❌ Reviews page
- ❌ Finance page
- ❌ Promotions page
- ❌ Staff management page
- ❌ Communication center
- ❌ Analytics page
- ❌ Settings page

#### 8. Communication
- ❌ Chat drawers (customer/rider)
- ❌ Call action buttons
- ❌ Predefined responses UI

#### 9. Reports
- ❌ Report generation UI
- ❌ Download triggers
- ❌ Report history

## Implementation Priority

### Phase 1: Core Functionality (Current Focus)
1. ✅ Backend models and APIs (mostly done)
2. 🔄 Frontend UI revamp with Zomato theme
3. 🔄 Complete menu management UI
4. 🔄 Enhanced orders management UI
5. 🔄 KDS interface

### Phase 2: Essential Features
1. Finance & settlements
2. Staff management
3. Inventory management UI
4. Reviews management UI
5. Analytics dashboard

### Phase 3: Advanced Features
1. Communication tools
2. Advanced reporting
3. Security enhancements
4. Optional AI features

## Notes

- Most backend infrastructure is in place
- Focus should be on frontend implementation and UX polish
- Some backend models need additional endpoints
- Seed data needs to be created for Bangalore restaurants
