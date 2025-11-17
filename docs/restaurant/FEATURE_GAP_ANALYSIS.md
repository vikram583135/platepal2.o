<!-- Auto-generated coverage report for restaurant platform requirements -->

# Restaurant Feature Coverage vs Requirements

This document cross-references the 15 requirement clusters from the latest product brief with the current PlatePal implementation. Status categories:

- ✅ **Done** – feature exists end-to-end (backend + UI) in current code
- ⚠️ **Partial** – some backend/UI scaffolding exists but gaps remain
- ❌ **Missing** – functionality not yet started

References cite representative files rather than exhaustive listings.

| # | Area | Status | Current Coverage | Gaps / Follow-up |
|---|------|--------|-----------------|------------------|
| 1 | Onboarding & Setup | ✅ | Multi-step wizard in `OnboardingPage.tsx` now includes OTP/email/phone verification, password reset, cuisine multi-select, veg toggle, Leaflet location picker, kitchen vs billing addresses, branch manager, document upload cards and manager invite modal backed by `RestaurantOnboardingViewSet`. | Add automated document validation rules/notifications and final reviewer dashboard for compliance team. |
| 2 | Dashboard & Alerts | ⚠️ | KPI cards, alerts pane, online toggle in `DashboardPage.tsx`; metrics from `RestaurantDashboardView`. | Add SLA timers, average value trends, actionable alerts (inventory/refund/payout), live feed widget streaming `/ws/restaurants/<id>/`. |
| 3 | Live Orders Mgmt | ⚠️ | Orders Kanban, actions (accept/start/ready), order detail modal with payment info. | Missing modify prep time, combine orders, rider/chat controls, cooking notes, print docket, SLA breach alerts, WebSocket sync for timers. |
| 4 | Kitchen Display (KDS) | ⚠️ | Full screen toggle, keyboard shortcuts, rush badge, audio alert, large tiles. | Need drag-to-reorder, item-level progress, offline cache, printer integration, multiple board layouts, network fallback heartbeat. |
| 5 | Menu Management | ⚠️ | Menu CRUD APIs + UI, category/item forms, inventory toggles. | Absent variant/add-on groups, combos, bulk CSV import/export, schedule availability UI, spice/diet badges, menu insights dashboard. |
| 6 | Inventory Management | ⚠️ | Backend models (`InventoryItem`, `StockMovement`), low-stock alerts. | No dedicated UI page, ingredient-level tracking, auto-out-of-stock toggle, reorder predictions, wastage report views. |
| 7 | Reviews & Ratings | ⚠️ | Backend review model with replies; API hooks available. | Missing reviews UI dashboard, rating trends, photo reviews surfacing, highlight controls, insights by item/time. |
| 8 | Finance & Settlements | ⚠️ | Models for settlement cycle, payouts, reconciliation added; finance page skeleton exists. | Need front-end timelines, GST breakdowns, settlement downloads, refund analytics, backend aggregation endpoints. |
| 9 | Promotions & Marketing | ⚠️ | Promotion model supports multiple discount types; promotions page placeholder. | Need campaign join flow, sponsored boosts, B1G1 combos, happy-hour scheduling UI, promo effectiveness analytics. |
|10 | Operations Tools | ⚠️ | Manager profiles, restaurant settings, staff page placeholder. | Lacking StaffAccount model, shift schedules, packaging stock, printer config, auto-close logic, activity logs UI. |
|11 | Communication Tools | ⚠️ | Chat backend app exists; communications page skeleton. | No predefined responses, rider/customer chat UI, call logging, “order ready” automation, templated apology/comp flows. |
|12 | Analytics & Reports | ⚠️ | Basic analytics endpoints + placeholder page. | Need configurable filters, sales/customer/operational insights, downloadable PDF/CSV/XLS exports, async report jobs. |
|13 | Security & Compliance | ⚠️ | Role-based access via `ManagerProfile`, audit logs for docs. | Missing 2FA enforcement, device/session logging, suspicious login detection, GST/FSSAI renewal reminders, permission-driven UI. |
|14 | Advanced/Future | ❌ | None of AI/multi-branch/dine-in/pickup/robotics features implemented. | Requires new services (`backend/apps/ai/`), branch-aware dashboards, dine-in QR flows, robotics hooks. |
|15 | Interface & UX Enhancements | ⚠️ | Zomato theme, responsive cards, KDS fullscreen, keyboard shortcuts. | Need dark mode toggle, tablet large font mode, drag-drop ordering, WebSocket fallback (SSE/polling), offline mode, diff-based order patching. |

## Key Observations

1. Backend foundations already exist for most core entities; missing areas cluster around finance analytics, staff/shift tooling, AI services, and enhanced menu constructs.
2. Frontend work is the largest gap: onboarding wizard, finance, promotions, inventory, communications, analytics all need fully fleshed-out experiences.
3. Realtime + offline requirements (sections 2, 3, 4, 15) require coordinated changes across WebSocket consumers (`backend/websockets/consumers.py`), React Query polling, and service worker caching.
4. Compliance/security upgrades imply cross-cutting updates to `apps/accounts`, `apps/notifications`, and possibly a new audit log UI module.

This document should be updated as each phase in `restaurant-53c3ce.plan.md` lands.

