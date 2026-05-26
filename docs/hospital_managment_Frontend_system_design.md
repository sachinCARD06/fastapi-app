# Hospital Management System — Frontend Design

## Table of Contents

1. [Tech Stack](#1-tech-stack)
2. [Application Architecture](#2-application-architecture)
3. [Routing Structure](#3-routing-structure)
4. [Role-Based Navigation](#4-role-based-navigation)
5. [Design System & Components](#5-design-system--components)
6. [Screen Wireframes](#6-screen-wireframes)
   - 6.1 Login
   - 6.2 Dashboards (per role)
   - 6.3 Hospital & Ward Management
   - 6.4 Doctor Management & Availability
   - 6.5 Staff Management
   - 6.6 Patient Registration & Profile
   - 6.7 Appointment Booking & Calendar
   - 6.8 Consultation Room (Doctor)
   - 6.9 Bed Map & Admission
   - 6.10 Lab / Medical Tests
   - 6.11 Pharmacy & Prescriptions
   - 6.12 Discharge Workflow
   - 6.13 Billing & Payment
   - 6.14 Payment History
7. [Key UI Flows](#7-key-ui-flows)
   - 7.1 Auth Flow
   - 7.2 Patient Books Appointment
   - 7.3 Receptionist Walk-in Registration
   - 7.4 Doctor Consultation Flow
   - 7.5 Admit Patient → Assign Bed
   - 7.6 Lab Test Lifecycle
   - 7.7 Pharmacy Dispense Flow
   - 7.8 Discharge Flow
   - 7.9 Payment Flow (OPD)
   - 7.10 Inpatient Final Billing & Discharge Payment
8. [State Management](#8-state-management)
9. [API Integration Layer](#9-api-integration-layer)
10. [Notifications & Alerts](#10-notifications--alerts)
11. [Responsive & Accessibility Notes](#11-responsive--accessibility-notes)

---

## 1. Tech Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend Tech Stack                          │
├─────────────────────┬───────────────────────────────────────────┤
│ Framework           │ React 18 + TypeScript                     │
│ Build Tool          │ Vite                                      │
│ Routing             │ React Router v6 (file-based convention)   │
│ State Management    │ Zustand (global) + React Query (server)   │
│ UI Component Lib    │ shadcn/ui (Radix UI primitives + Tailwind)│
│ Styling             │ Tailwind CSS                              │
│ Forms               │ React Hook Form + Zod (validation)        │
│ HTTP Client         │ Axios (interceptors for JWT)              │
│ Date/Time           │ date-fns                                  │
│ Charts              │ Recharts                                  │
│ Icons               │ Lucide React                              │
│ Tables              │ TanStack Table v8                         │
│ Notifications       │ Sonner (toast)                            │
│ Testing             │ Vitest + React Testing Library            │
└─────────────────────┴───────────────────────────────────────────┘
```

---

## 2. Application Architecture

```
src/
├── main.tsx                    # App entry, QueryClient, Router provider
├── App.tsx                     # Root routes, AuthGuard wrapper
│
├── api/                        # Axios instance + per-resource API functions
│   ├── client.ts               # Axios config, JWT interceptor, refresh
│   ├── auth.ts
│   ├── hospitals.ts
│   ├── doctors.ts
│   ├── patients.ts
│   ├── appointments.ts
│   ├── admissions.ts
│   ├── tests.ts
│   ├── medicines.ts
│   ├── prescriptions.ts
│   ├── billing.ts
│   └── payments.ts
│
├── store/                      # Zustand slices
│   ├── auth.store.ts           # user, token, role, logout
│   ├── ui.store.ts             # sidebar open, active modal, loading flags
│   └── hospital.store.ts       # selected hospitalId (multi-tenant)
│
├── hooks/                      # React Query hooks (one file per resource)
│   ├── useAuth.ts
│   ├── useDoctors.ts
│   ├── usePatients.ts
│   ├── useAppointments.ts
│   ├── useBeds.ts
│   ├── useTests.ts
│   ├── useMedicines.ts
│   ├── useBilling.ts
│   └── usePayments.ts
│
├── components/
│   ├── layout/
│   │   ├── AppShell.tsx        # Sidebar + Topbar + main content slot
│   │   ├── Sidebar.tsx         # Role-filtered nav links
│   │   ├── Topbar.tsx          # Hospital selector, user menu, notifications
│   │   └── PageHeader.tsx      # Title + breadcrumb + action button slot
│   ├── ui/                     # shadcn generated components
│   └── shared/                 # Cross-domain reusable components
│       ├── StatusBadge.tsx
│       ├── DataTable.tsx
│       ├── ConfirmDialog.tsx
│       ├── EmptyState.tsx
│       └── PatientCard.tsx
│
├── pages/                      # One folder per domain
│   ├── auth/
│   ├── dashboard/
│   ├── hospitals/
│   ├── doctors/
│   ├── staff/
│   ├── patients/
│   ├── appointments/
│   ├── admissions/
│   ├── beds/
│   ├── tests/
│   ├── medicines/
│   ├── prescriptions/
│   ├── billing/
│   └── payments/
│
├── types/                      # TypeScript interfaces matching API schemas
└── utils/                      # formatDate, formatCurrency, role guards
```

---

## 3. Routing Structure

```
/                         → redirect based on role
/login                    → public

/dashboard                → role-specific dashboard redirect
  /dashboard/admin
  /dashboard/doctor
  /dashboard/staff
  /dashboard/receptionist
  /dashboard/patient

/hospitals                → list
/hospitals/:id            → detail (wards, bed summary)
/hospitals/:id/wards      → ward list
/hospitals/:id/wards/:wid → ward detail + bed map

/doctors                  → list + search/filter
/doctors/new              → registration form (admin only)
/doctors/:id              → profile
/doctors/:id/availability → schedule manager

/staff                    → list
/staff/new                → register form
/staff/:id                → profile

/patients                 → list + search
/patients/new             → registration wizard
/patients/:id             → full profile
  /patients/:id/appointments
  /patients/:id/admissions
  /patients/:id/tests
  /patients/:id/prescriptions

/appointments             → list / calendar toggle
/appointments/new         → booking form
/appointments/:id         → detail + status actions

/beds                     → live bed map
/admissions               → list
/admissions/new           → admit patient form
/admissions/:id           → admission detail
/admissions/:id/discharge → discharge form

/tests                    → lab queue list
/tests/:id                → test detail + result upload form

/medicines                → inventory list
/medicines/new            → add medicine
/medicines/:id            → detail + restock form
/prescriptions/:id        → prescription detail + dispense action

/billing                  → billing queue (staff/admin)
/billing/new              → create manual bill
/billing/:id              → bill detail + payment action
/billing/:id/pay          → payment modal / page

/payments                 → payment history (staff/admin)
/payments/my              → patient's own payment history
/payments/:id             → payment receipt detail
```

---

## 4. Role-Based Navigation

```
┌──────────────────────────────────────────────────────────────────┐
│                         Sidebar Nav Items                        │
├──────────────────────┬───────┬────────┬───────┬──────────┬───────┤
│ Page                 │ Admin │ Doctor │ Staff │ Recept.  │ Patnt │
├──────────────────────┼───────┼────────┼───────┼──────────┼───────┤
│ Dashboard            │   ✓   │   ✓    │   ✓   │    ✓     │   ✓   │
│ Hospitals            │   ✓   │        │       │          │       │
│ Wards & Beds         │   ✓   │        │   ✓   │          │       │
│ Doctors              │   ✓   │        │       │    ✓     │   ✓   │
│ Staff                │   ✓   │        │       │          │       │
│ Patients             │   ✓   │   ✓    │   ✓   │    ✓     │       │
│ My Profile (patient) │       │        │       │          │   ✓   │
│ Appointments         │   ✓   │   ✓    │   ✓   │    ✓     │   ✓   │
│ Bed Map              │   ✓   │        │   ✓   │          │       │
│ Admissions           │   ✓   │   ✓    │   ✓   │          │       │
│ Lab / Tests          │   ✓   │   ✓    │   ✓   │          │       │
│ Pharmacy             │   ✓   │        │   ✓   │          │       │
│ Medicines            │   ✓   │        │       │          │       │
│ Billing              │   ✓   │        │   ✓   │    ✓     │       │
│ My Bills             │       │        │       │          │   ✓   │
│ Payment History      │   ✓   │        │   ✓   │    ✓     │   ✓   │
│ Reports              │   ✓   │        │       │          │       │
└──────────────────────┴───────┴────────┴───────┴──────────┴───────┘
```

---

## 5. Design System & Components

### Color Palette

```
Primary Blue    #2563EB   → CTA buttons, links, active nav
Success Green   #16A34A   → AVAILABLE, COMPLETED, ACTIVE
Warning Amber   #D97706   → PENDING, IN_PROGRESS, LOW STOCK
Danger Red      #DC2626   → OCCUPIED (bed), CANCELLED, errors
Neutral Gray    #6B7280   → Secondary text, borders
Background      #F9FAFB   → Page background
Card            #FFFFFF   → Card surface
```

### Status Badge Colors

```
Appointment:
  PENDING       → amber
  CONFIRMED     → blue
  CHECKED_IN    → indigo
  IN_PROGRESS   → purple
  COMPLETED     → green
  CANCELLED     → red
  NO_SHOW       → gray

Bed:
  AVAILABLE     → green
  OCCUPIED      → red
  RESERVED      → amber
  MAINTENANCE   → gray

Test:
  ORDERED           → amber
  SAMPLE_COLLECTED  → blue
  IN_PROGRESS       → purple
  COMPLETED         → green
  CANCELLED         → red

Prescription:
  ACTIVE            → blue
  DISPENSED         → green
  PARTIALLY_DISPENSED → amber
  CANCELLED         → red

Bill:
  DRAFT             → gray
  PENDING           → amber
  PARTIALLY_PAID    → indigo
  PAID              → green
  OVERDUE           → red
  WAIVED            → purple

Payment:
  SUCCESS           → green
  PENDING           → amber
  FAILED            → red
  REFUNDED          → purple
```

### Shared Component Inventory

```
Layout:         AppShell, Sidebar, Topbar, PageHeader
Navigation:     NavItem, Breadcrumb, Tabs
Data Display:   DataTable, StatsCard, Badge, Avatar, Timeline
Forms:          Input, Select, DatePicker, TimePicker, Textarea,
                Checkbox, Switch, FileUpload, FormField
Feedback:       Toast, Alert, Spinner, Skeleton, EmptyState, ErrorBoundary
Overlay:        Dialog, Sheet (slide-over), Tooltip, Popover, DropdownMenu
Specialized:    PatientCard, DoctorCard, BedCell, AppointmentSlot,
                TestResultRow, PrescriptionItem,
                BillLineItem, PaymentMethodSelector, PaymentReceipt,
                InvoiceSummaryCard, InsuranceClaimBadge
```

---

## 6. Screen Wireframes

### 6.1 Login

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│              ┌───────────────────────────────────┐             │
│              │  🏥  Hospital Management System   │             │
│              └───────────────────────────────────┘             │
│                                                                │
│              ┌───────────────────────────────────┐             │
│              │            Sign In                │             │
│              │                                   │             │
│              │  Email                            │             │
│              │  ┌─────────────────────────────┐  │             │
│              │  │ doctor@hospital.com         │  │             │
│              │  └─────────────────────────────┘  │             │
│              │                                   │             │
│              │  Password                         │             │
│              │  ┌─────────────────────────────┐  │             │
│              │  │ ••••••••••••            👁  │  │             │
│              │  └─────────────────────────────┘  │             │
│              │                                   │             │
│              │  [ Forgot password? ]             │             │
│              │                                   │             │
│              │  ┌─────────────────────────────┐  │             │
│              │  │         Sign In             │  │             │
│              │  └─────────────────────────────┘  │             │
│              │                                   │             │
│              └───────────────────────────────────┘             │
│                                                                │
│                  Error:  ⚠ Invalid credentials                 │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 6.2 Dashboards

#### Admin Dashboard

```
┌────────────────────────────────────────────────────────────────────┐
│ 🏥 City Hospital    ▼         [ 🔔 3 ]  [ Sachin Admin  ▼ ]        │
├──────────┬─────────────────────────────────────────────────────────┤
│          │                                                         │
│ Dashboard│  Good morning, Sachin                    2026-05-26     │
│ Hospitals│                                                         │
│ Doctors  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│ Staff    │  │  Doctors │ │ Patients │ │  Beds    │ │  Tests   │    │
│ Patients │  │    42    │ │   318    │ │ 87/120   │ │  12 Pend │    │
│ Appts    │  │  active  │ │registered│ │ occupied │ │  ing     │    │
│ Beds     │  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │
│ Admissions                                                         │
│ Lab      │  ┌────────────────────────────┐ ┌────────────────────┐  │
│ Pharmacy │  │  Today's Appointments      │ │  Bed Availability  │  │
│ Medicines│  │  ─────────────────────     │ │  ─────────────── ─ │  │
│          │  │  09:00  Dr. Mehta  P-0042  │ │  Ward A (General)  │  │
│          │  │  09:30  Dr. Shah   P-0087  │ │  ████░░░░  12/20   │  │
│          │  │  10:00  Dr. Mehta  P-0011  │ │                    │  │
│          │  │  10:30  Dr. Roy    P-0055  │ │  Ward B (ICU)      │  │
│          │  │  [ View All → ]            │ │  ████████  8/8     │  │
│          │  └────────────────────────────┘ │                    │  │
│          │                                 │  Ward C (Private)  │  │
│          │  ┌────────────────────────────┐ │  ██░░░░░░  4/16    │  │
│          │  │  Low Stock Alerts  ⚠       │ │  [ View Bed Map ]  │  │
│          │  │  Amoxicillin  12 units left│ └────────────────────┘  │
│          │  │  Paracetamol  8 units left │                         │
│          │  │  [ Go to Pharmacy → ]      │                         │
│          │  └────────────────────────────┘                         │
│          │                                                         │
└──────────┴─────────────────────────────────────────────────────────┘
```

#### Doctor Dashboard

```
┌─────────────────────────────────────────────────────────────────────┐
│ 🏥 City Hospital             [ 🔔 ]  [ Dr. Anil Mehta  ▼ ]          │
├──────────┬──────────────────────────────────────────────────────────┤
│ Dashboard│                                                          │
│ My Appts │  Today's Queue                          Mon, 26 May 2026 │
│ Patients │                                                          │
│ Tests    │  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌──────────┐    │
│ Admissions  │ Pending  │ │Checked In│ │In Progress│ │Completed │    │
│          │  │    4     │ │    1     │ │     1     │ │    6     │    │
│          │  └──────────┘ └──────────┘ └───────────┘ └──────────┘    │
│          │                                                          │
│          │  ┌────────────────────────────────────────────────────┐  │
│          │  │  Current Patient                                   │  │
│          │  │  ┌──────────────────────────────────────────────┐  │  │
│          │  │  │  P-0042  Rahul Sharma  ●  IN PROGRESS        │  │  │
│          │  │  │  27 yrs, Male, B+  │  Reason: Fever, 3 days  │  │  │
│          │  │  │  [ View Full Profile ] [ Order Test ] [Rx]   │  │  │
│          │  │  └──────────────────────────────────────────────┘  │  │
│          │  └────────────────────────────────────────────────────┘  │
│          │                                                          │
│          │  ┌───────────────────────────────────────────────────┐   │
│          │  │  Upcoming Queue                                   │   │
│          │  │  10:00  P-0087  Priya Nair     CHECKED IN         │   │
│          │  │  10:30  P-0011  Vikram Singh   CONFIRMED          │   │
│          │  │  11:00  P-0055  Asha Patel     CONFIRMED          │   │
│          │  └───────────────────────────────────────────────────┘   │
│          │                                                          │
│          │  ┌───────────────────────────────────────────────────┐   │
│          │  │  Pending Test Results  (3)                        │   │
│          │  │  P-0042  CBC         Ordered    2026-05-25        │   │
│          │  │  P-0011  X-Ray Chest Completed  ⚠ ABNORMAL        │   │
│          │  └───────────────────────────────────────────────────┘   │
└──────────┴──────────────────────────────────────────────────────────┘
```

#### Receptionist Dashboard

```
┌──────────────────────────────────────────────────────────────────────┐
│ 🏥 City Hospital             [ 🔔 ]  [ Reception Desk  ▼ ]           │
├──────────┬───────────────────────────────────────────────────────────┤
│ Dashboard│                                                           │
│ Patients │  ┌─────────────────────────────────────────────────────┐  │
│ Appts    │  │  Quick Actions                                      │  │
│ Doctors  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐   │  │
│          │  │  │ + New Patient│  │ + Book Appt  │  │ Check-In │   │  │
│          │  │  └──────────────┘  └──────────────┘  └──────────┘   │  │
│          │  └─────────────────────────────────────────────────────┘  │
│          │                                                           │
│          │  ┌───────────────────────────────────────────────────┐    │
│          │  │  Search Patient                                   │    │
│          │  │  ┌────────────────────────────────────────────┐   │    │
│          │  │  │ 🔍  Name / UID / Phone                     │   │    │
│          │  │  └────────────────────────────────────────────┘   │    │
│          │  └───────────────────────────────────────────────────┘    │
│          │                                                           │
│          │  Today's Appointments                                     │
│          │  ┌─────┬───────────┬───────────────┬──────────┬───────┐   │
│          │  │ Time│ Patient   │ Doctor        │ Status   │Action │   │
│          │  ├─────┼───────────┼───────────────┼──────────┼───────┤   │
│          │  │09:00│ P-0042    │ Dr. Mehta     │ PENDING  │[✓ In] │   │
│          │  │09:30│ P-0087    │ Dr. Shah      │CHECKED IN│ ----  │   │
│          │  │10:00│ P-0011    │ Dr. Mehta     │ PENDING  │[✓ In] │   │
│          │  │10:30│ P-0055    │ Dr. Roy       │ CONFIRMED│[✓ In] │   │
│          │  └─────┴───────────┴───────────────┴──────────┴───────┘   │
└──────────┴───────────────────────────────────────────────────────────┘
```

#### Patient Dashboard

```
┌──────────────────────────────────────────────────────────────────────┐
│ 🏥 City Hospital             [ 🔔 ]  [ Rahul Sharma  ▼ ]             │
├──────────┬───────────────────────────────────────────────────────────┤
│ Dashboard│                                                           │
│ My Appts │  Hello, Rahul                                             │
│ My Tests │  Patient ID: P-0042  │  Blood Group: B+  │  Age: 27       │
│ My Rx    │                                                           │
│          │  ┌────────────────────────────────────────────────────┐   │
│          │  │  Upcoming Appointment                              │   │
│          │  │  Dr. Anil Mehta  ·  Cardiology                     │   │
│          │  │  Tomorrow, 27 May 2026  at  10:30 AM               │   │
│          │  │  City Hospital  ·  CONFIRMED                       │   │
│          │  │           [ View Detail ]  [ Cancel ]              │   │
│          │  └────────────────────────────────────────────────────┘   │
│          │                                                           │
│          │  ┌──────────────────────┐  ┌──────────────────────────┐   │
│          │  │  Recent Tests        │  │  Active Prescriptions    │   │
│          │  │  CBC  ·  25 May      │  │  Amoxicillin 500mg 3x/d  │   │
│          │  │  COMPLETED  Normal   │  │  Paracetamol 650mg 2x/d  │   │
│          │  │                      │  │  Expires in 3 days       │   │
│          │  │  [ View All ]        │  │  [ View All ]            │   │
│          │  └──────────────────────┘  └──────────────────────────┘   │
│          │                                                           │
│          │  ┌────────────────────────────────────────────────────┐   │
│          │  │  [ + Book New Appointment ]                        │   │
│          │  └────────────────────────────────────────────────────┘   │
└──────────┴───────────────────────────────────────────────────────────┘
```

---

### 6.3 Hospital & Ward Management

#### Hospital List (Admin)

```
┌─────────────────────────────────────────────────────────────────────┐
│ Hospitals                                    [ + Add Hospital ]     │
│─────────────────────────────────────────────────────────────────────│
│  🔍 Search hospitals...          [ City ▼ ]  [ Status ▼ ]           │
│                                                                     │
│  ┌───────────┬────────────────┬────────┬──────────┬───────────┐     │
│  │ Name      │ Address        │ City   │ Status   │ Actions   │     │
│  ├───────────┼────────────────┼────────┼──────────┼───────────┤     │
│  │City Hosp  │ 12 MG Road     │ Mumbai │ ● Active │ Edit  Del │     │
│  │Apollo     │ 45 NH-48       │ Pune   │ ● Active │ Edit  Del │     │
│  │Lilavati   │ Bandra West    │ Mumbai │ ○ Inactive│ Edit  Del│     │
│  └───────────┴────────────────┴────────┴──────────┴───────────┘     │
│                                      Showing 3 of 3  [ < 1 > ]      │
└─────────────────────────────────────────────────────────────────────┘
```

#### Ward Detail + Bed Summary

```
┌──────────────────────────────────────────────────────────────────────┐
│ < Hospitals  /  City Hospital  /  Wards                              │
│──────────────────────────────────────────────────────────────────────│
│  City Hospital — Wards                     [ + Add Ward ]            │
│                                                                      │
│  ┌────────────┬─────────────┬─────────┬───────────┬───────────┐      │
│  │ Ward       │ Type        │ Beds    │ Available │ Actions   │      │
│  ├────────────┼─────────────┼─────────┼───────────┼───────────┤      │
│  │ Ward A     │ GENERAL     │  20     │    8      │ View Beds │      │
│  │ Ward B     │ ICU         │   8     │    0      │ View Beds │      │
│  │ Ward C     │ PRIVATE     │  16     │   12      │ View Beds │      │
│  │ Ward D     │ MATERNITY   │  12     │    5      │ View Beds │      │
│  └────────────┴─────────────┴─────────┴───────────┴───────────┘      │
└──────────────────────────────────────────────────────────────────────┘
```

---

### 6.4 Doctor Management & Availability

#### Doctor List

```
┌──────────────────────────────────────────────────────────────────────┐
│ Doctors                                         [ + Register Doctor ]│
│──────────────────────────────────────────────────────────────────────│
│  🔍 Search...   [ Specialization ▼ ]  [ Hospital ▼ ]  [ Status ▼ ]   │
│                                                                      │
│  ┌───────────────┬─────────────────┬──────────┬───────┬──────────┐   │
│  │ Doctor        │ Specialization  │ Exp      │ Fee   │ Status   │   │
│  ├───────────────┼─────────────────┼──────────┼───────┼──────────┤   │
│  │ Dr. A. Mehta  │ Cardiology      │ 15 yrs   │ ₹800  │ ● Active │   │
│  │ Dr. R. Shah   │ Orthopedics     │ 10 yrs   │ ₹600  │ ● Active │   │
│  │ Dr. P. Roy    │ General Med     │  8 yrs   │ ₹400  │ ● Active │   │
│  └───────────────┴─────────────────┴──────────┴───────┴──────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

#### Doctor Availability / Schedule Manager

```
┌──────────────────────────────────────────────────────────────────────┐
│ < Doctors  /  Dr. Anil Mehta  /  Availability                        │
│──────────────────────────────────────────────────────────────────────│
│  Schedule                                    [ + Add Schedule ]      │
│                                                                      │
│  ┌─────┬────────────┬────────────┬──────────┬───────┬────────────┐   │
│  │ Day │ Start      │ End        │ Slot     │ Slots │ Status     │   │
│  ├─────┼────────────┼────────────┼──────────┼───────┼────────────┤   │
│  │ MON │ 09:00 AM   │ 01:00 PM   │ 30 min   │   8   │ ● Active   │   │
│  │ WED │ 09:00 AM   │ 01:00 PM   │ 30 min   │   8   │ ● Active   │   │
│  │ FRI │ 02:00 PM   │ 06:00 PM   │ 30 min   │   8   │ ● Active   │   │
│  │ SAT │ 10:00 AM   │ 12:00 PM   │ 30 min   │   4   │ ○ Inactive │   │
│  └─────┴────────────┴────────────┴──────────┴───────┴────────────┘   │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐   │
│  │  Today's Slots — Monday 26 May 2026                           │   │
│  │                                                               │   │
│  │  09:00  [ ████ BOOKED ]   09:30  [ ████ BOOKED ]              │   │
│  │  10:00  [ ████ BOOKED ]   10:30  [  FREE  ]                   │   │
│  │  11:00  [  FREE  ]        11:30  [  FREE  ]                   │   │
│  │  12:00  [ ████ BOOKED ]   12:30  [  FREE  ]                   │   │
│  └───────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

### 6.5 Staff Management

```
┌──────────────────────────────────────────────────────────────────────┐
│ Staff                                         [ + Register Staff ]   │
│──────────────────────────────────────────────────────────────────────│
│  🔍 Search...      [ Role ▼ ]   [ Department ▼ ]   [ Shift ▼ ]       │
│                                                                      │
│  ┌──────────────┬─────────────────┬──────────────┬────────┬───────┐  │
│  │ Name         │ Role            │ Department   │ Shift  │ EmpID │  │
│  ├──────────────┼─────────────────┼──────────────┼────────┼───────┤  │
│  │ Anjali K.    │ NURSE           │ ICU          │ NIGHT  │ E-101 │  │
│  │ Ravi M.      │ LAB_TECHNICIAN  │ Pathology    │ MORNING│ E-102 │  │
│  │ Sunita P.    │ PHARMACIST      │ Pharmacy     │ MORNING│ E-103 │  │
│  │ Raj D.       │ RECEPTIONIST    │ OPD          │AFTERNOON E-104 │  │
│  └──────────────┴─────────────────┴──────────────┴────────┴───────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

---

### 6.6 Patient Registration & Profile

#### Registration Wizard (3 Steps)

```
Step 1 of 3 — Personal Info
┌──────────────────────────────────────────────────────────────────────┐
│ Register New Patient                                                 │
│  ①──────────②──────────③                                           │
│  Personal   Medical    Emergency                                     │
│──────────────────────────────────────────────────────────────────────│
│                                                                      │
│  ┌─────────────────────────┐  ┌─────────────────────────┐            │
│  │ Full Name *             │  │ Email                   │            │
│  │ Rahul Sharma            │  │ rahul@email.com         │            │
│  └─────────────────────────┘  └─────────────────────────┘            │
│                                                                      │
│  ┌─────────────────────────┐  ┌──────────┐  ┌─────────────────────┐  │
│  │ Date of Birth *         │  │ Gender * │  │ Blood Group         │  │
│  │ 1999-03-15     📅       │  │ Male   ▼ │  │ B+             ▼    │  │
│  └─────────────────────────┘  └──────────┘  └─────────────────────┘  │
│                                                                      │
│  ┌─────────────────────────┐  ┌─────────────────────────┐            │
│  │ Address                 │  │ City                    │            │
│  │ 42 Park Street          │  │ Mumbai                  │            │
│  └─────────────────────────┘  └─────────────────────────┘            │
│                                                                      │
│                                      [ Cancel ]  [ Next → ]          │
└──────────────────────────────────────────────────────────────────────┘

Step 2 of 3 — Medical Info
┌──────────────────────────────────────────────────────────────────────┐
│  Allergies (optional)             Chronic Conditions (optional)      │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐    │
│  │ Penicillin, Dust            │  │ Type 2 Diabetes             │    │
│  └─────────────────────────────┘  └─────────────────────────────┘    │
│                                      [ ← Back ]  [ Next → ]          │
└──────────────────────────────────────────────────────────────────────┘

Step 3 of 3 — Emergency Contact
┌──────────────────────────────────────────────────────────────────────┐
│  Emergency Contact Name           Emergency Contact Phone            │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐    │
│  │ Pooja Sharma                │  │ +91 98765 43210             │    │
│  └─────────────────────────────┘  └─────────────────────────────┘    │
│                                   [ ← Back ]  [ Register Patient ]   │
└──────────────────────────────────────────────────────────────────────┘
```

#### Patient Full Profile

```
┌──────────────────────────────────────────────────────────────────────┐
│ < Patients  /  Rahul Sharma                                          │
│──────────────────────────────────────────────────────────────────────│
│  ┌───────────────────────┐  ┌──────────────────────────────────────┐ │
│  │  👤  Rahul Sharma     │  │  Quick Actions                       │ │
│  │  P-0042               │  │  [ + Book Appointment ]              │ │
│  │  27 yrs • Male • B+   │  │  [ + Admit Patient ]                 │ │
│  │  ● Active             │  │  [ + Order Test ]                    │ │
│  │                       │  └──────────────────────────────────────┘ │
│  │  📞 +91 98765 00001   │                                           │
│  │  📧 rahul@email.com   │  ┌──────────────────────────────────────┐ │
│  │  📍 Mumbai            │  │  Allergies: Penicillin               │ │
│  │                       │  │  Conditions: Type 2 Diabetes         │ │
│  │  Emergency:           │  │  Emergency: Pooja +91 98765 43210    │ │
│  │  Pooja Sharma         │  └──────────────────────────────────────┘ │
│  └───────────────────────┘                                           │
│                                                                      │
│  [ Appointments ]  [ Admissions ]  [ Tests ]  [ Prescriptions ]      │
│  ─────────────────────────────────────────────────────────────────   │
│  (Tab content shown below)                                           │
└──────────────────────────────────────────────────────────────────────┘
```

---

### 6.7 Appointment Booking & Calendar

#### Available Slots Picker

```
┌──────────────────────────────────────────────────────────────────────┐
│ Book Appointment                                                     │
│──────────────────────────────────────────────────────────────────────│
│  Patient:  Rahul Sharma (P-0042)       Hospital: City Hospital       │
│                                                                      │
│  Doctor                              Type                            │
│  ┌──────────────────────────────┐    ┌───────────────────────┐       │
│  │ Dr. Anil Mehta — Cardiology ▼│    │ OUTPATIENT           ▼│       │
│  └──────────────────────────────┘    └───────────────────────┘       │
│                                                                      │
│  Select Date                                                         │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │   ◄  May 2026  ►                                            │     │
│  │   Mo  Tu  We  Th  Fr  Sa  Su                                │     │
│  │                    1   2   3                                │     │
│  │    4   5   6   7   8   9  10                                │     │
│  │   11  12  13  14  15  16  17                                │     │
│  │   18  19  20  21  22  23  24                                │     │
│  │   25 [26] 27  28  29  30  31   ← bold = has availability    │     │
│  └─────────────────────────────────────────────────────────────┘     │
│                                                                      │
│  Available Slots — Mon 26 May                                        │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐              │
│  │ 09:00  │ │ 09:30  │ │[10:30] │ │ 11:00  │ │ 11:30  │              │
│  │ BOOKED │ │ BOOKED │ │ FREE ✓ │ │ FREE   │ │ FREE   │              │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘              │
│                                                                      │
│  Reason / Chief Complaint                                            │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │ Chest pain and breathlessness since 2 days                  │     │
│  └─────────────────────────────────────────────────────────────┘     │
│                                                                      │
│                                  [ Cancel ]  [ Confirm Booking ]     │
└──────────────────────────────────────────────────────────────────────┘
```

#### Appointment List (Calendar / List Toggle)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Appointments                              [ 📅 Calendar ] [ ≡ List ] │
│  🔍  [ Doctor ▼ ] [ Status ▼ ] [ Date Range: 26 May – 26 May ]       │
│──────────────────────────────────────────────────────────────────────│
│  ┌──────┬─────────┬───────────────┬──────────────┬────────┬───────┐  │
│  │ Time │ Patient │ Doctor        │ Type         │ Status │ Action│  │
│  ├──────┼─────────┼───────────────┼──────────────┼────────┼───────┤  │
│  │09:00 │ P-0042  │ Dr. Mehta     │ OUTPATIENT   │CHECKED │[Start]│  │
│  │09:30 │ P-0087  │ Dr. Shah      │ FOLLOW_UP    │PENDING │[✓ In] │  │
│  │10:00 │ P-0011  │ Dr. Mehta     │ OUTPATIENT   │PENDING │[✓ In] │  │
│  │10:30 │ P-0055  │ Dr. Roy       │ OUTPATIENT   │CONFIRMED[✓ In] │  │
│  └──────┴─────────┴───────────────┴──────────────┴────────┴───────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

---

### 6.8 Consultation Room (Doctor View)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Consultation  —  Appointment #1042                  ● IN PROGRESS  │
│──────────────────────────────────────────────────────────────────────│
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │  👤  Rahul Sharma  (P-0042)   27 yrs  Male  B+              │     │
│  │  Chief Complaint: Chest pain and breathlessness since 2 days│     │
│  │  Allergies: Penicillin   Conditions: Type 2 Diabetes        │     │
│  └─────────────────────────────────────────────────────────────┘     │
│                                                                      │
│  Consultation Notes                                                  │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │ Patient presents with exertional chest pain. ECG ordered.   │     │
│  │ BP: 140/90 mmHg. Referred for echo.                         │     │
│  └─────────────────────────────────────────────────────────────┘     │
│                                                                      │
│  ┌──────────────────────────┐  ┌──────────────────────────────────┐  │
│  │  Order Tests             │  │  Prescriptions                   │  │ 
│  │  ──────────────────────  │  │  ───────────────────────────     │  │
│  │  ┌──────────────────┐    │  │  ┌───────────────────────────┐   │  │
│  │  │ Test  [ ECG   ▼] │    │  │  │ Medicine [Aspirin 75mg ▼] │   │  │
│  │  └──────────────────┘    │  │  │ Dose  [ 75mg ]            │   │  │
│  │  [ + Add Test ]          │  │  │ Freq  [ Once daily    ▼]  │   │  │
│  │                          │  │  │ Days  [ 30 ]              │   │  │
│  │  Ordered:                │  │  │ Notes [ After meals ]     │   │  │
│  │  • ECG  —  ORDERED       │  │  └───────────────────────────┘   │  │
│  │  • CBC  —  ORDERED       │  │  [ + Add Medicine ]              │  │
│  └──────────────────────────┘  │                                  │  │
│                                │  ┌───────────────────────────┐   │  │
│                                │  │ Aspirin 75mg  1x/d  30 d  │   │  │
│                                │  │ Metoprolol 25mg  1x/d  30d│   │  │
│                                │  └───────────────────────────┘   │  │
│                                └──────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Admit Patient?   [ Recommend Admission ] (opens admit form)   │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│                 [ Cancel Consultation ]   [ Complete Consultation ]  │
└──────────────────────────────────────────────────────────────────────┘
```

---

### 6.9 Bed Map & Admission

#### Live Bed Map

```
┌──────────────────────────────────────────────────────────────────────┐
│ Bed Map  —  City Hospital               [ Ward: All ▼ ]              │
│──────────────────────────────────────────────────────────────────────│
│  Legend:  ■ Available  ■ Occupied  ■ Reserved  ■ Maintenance         │
│  Total: 56   Available: 25   Occupied: 27   Reserved: 2   Maint: 2   │
│                                                                      │
│  Ward A  —  General (20 beds)                                        │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐      │
│  │ A-01 │ │ A-02 │ │ A-03 │ │ A-04 │ │ A-05 │ │ A-06 │ │ A-07 │      │
│  │  ██  │ │  ██  │ │  ██  │ │  ░░  │ │  ░░  │ │  ██  │ │  ██  │      │
│  │Occupy│ │Occupy│ │Occupy│ │ Free │ │ Free │ │Occupy│ │Reserv│      │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘      │
│  [ + more beds… ]                                                    │
│                                                                      │
│  Ward B  —  ICU (8 beds)                                             │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐               │
│  │ B-01 │ │ B-02 │ │ B-03 │ │ B-04 │ │ B-05 │ │ B-06 │               │
│  │  ██  │ │  ██  │ │  ██  │ │  ██  │ │  ██  │ │  ██  │               │
│  │Occupy│ │Occupy│ │Occupy│ │Occupy│ │Occupy│ │Occupy│               │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘               │
│  All ICU beds occupied                                               │
└──────────────────────────────────────────────────────────────────────┘

  Click on a Free bed → [ Assign to Patient ] slide-over appears
```

#### Admit Patient Form (Slide-over)

```
  ┌────────────────────────────────────────────────┐
  │  Admit Patient                            ✕    │
  │────────────────────────────────────────────────│
  │  Patient *                                     │
  │  ┌──────────────────────────────────────────┐  │
  │  │ 🔍 Search by name or UID                 │  │
  │  └──────────────────────────────────────────┘  │
  │  ┌──────────────────────────────────────────┐  │
  │  │ P-0042  Rahul Sharma  ✓                  │  │
  │  └──────────────────────────────────────────┘  │
  │                                                │
  │  Selected Bed                                  │
  │  Ward A  –  A-04  –  STANDARD  –  AVAILABLE    │
  │                                                │
  │  Admitting Doctor *                            │
  │  ┌──────────────────────────────────────────┐  │
  │  │ Dr. Anil Mehta — Cardiology             ▼│  │
  │  └──────────────────────────────────────────┘  │
  │                                                │
  │  Linked Appointment (optional)                 │
  │  ┌──────────────────────────────────────────┐  │
  │  │ #1042 — 26 May 09:00 — Dr. Mehta      ▼│  │
  │  └──────────────────────────────────────────┘  │
  │                                                │
  │  Preliminary Diagnosis                         │
  │  ┌──────────────────────────────────────────┐  │
  │  │ Chest pain under investigation           │  │
  │  └──────────────────────────────────────────┘  │
  │                                                │
  │       [ Cancel ]      [ Admit Patient ]        │
  └────────────────────────────────────────────────┘
```

---

### 6.10 Lab / Medical Tests

#### Lab Queue

```
┌──────────────────────────────────────────────────────────────────────┐
│ Lab Queue                                          [ + Order Test ]  │
│  [ Status ▼ ]  [ Category ▼ ]  [ Doctor ▼ ]  🔍 Patient UID/Name     │
│──────────────────────────────────────────────────────────────────────│
│  ┌────────┬───────┬──────────────┬───────────┬──────────┬─────────┐  │
│  │ Test   │ Cat   │ Patient      │ Ordered By│ Ordered  │ Status  │  │
│  ├────────┼───────┼──────────────┼───────────┼──────────┼─────────┤  │
│  │ CBC    │ LAB   │ P-0042 Rahul │ Dr. Mehta │ 09:15 AM │ ORDERED │  │
│  │ ECG    │ ECG   │ P-0042 Rahul │ Dr. Mehta │ 09:15 AM │ SAMPLE  │  │
│  │ X-Ray  │ RADIO │ P-0087 Priya │ Dr. Shah  │ 08:30 AM │IN PROG  │  │
│  │ LFT    │ LAB   │ P-0011 Vikram│ Dr. Mehta │ 08:00 AM │COMPLETE │  │
│  └────────┴───────┴──────────────┴───────────┴──────────┴─────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

#### Test Detail + Result Upload

```
┌──────────────────────────────────────────────────────────────────────┐
│ < Lab Queue  /  Test #T-0088  —  CBC                                 │
│──────────────────────────────────────────────────────────────────────│
│  Patient:  P-0042  Rahul Sharma         Status:  ● IN PROGRESS       │
│  Ordered by: Dr. Anil Mehta            Ordered: 26 May 09:15 AM      │
│  Conducted by: Ravi M. (Lab Tech)      Sample:  26 May 09:45 AM      │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐   │
│  │  Status Timeline                                              │   │
│  │  ●──────────●──────────●──────────○──────────○                │   │
│  │  ORDERED  SAMPLE    IN_PROG   COMPLETED  (abnormal flag)      │   │
│  │  09:15    09:45     10:00                                     │   │
│  └───────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  Upload Result                                                       │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Result Value                                                │    │
│  │  ┌────────────────────────────────────────────────────────┐  │    │
│  │  │  WBC: 11.2 g/dL  (Normal: 4.5–11.0)                    │  │    │
│  │  │  RBC: 4.5 M/μL   (Normal: 4.5–5.9)                     │  │    │
│  │  │  Platelets: 180 K/μL  (Normal: 150–400)                │  │    │
│  │  └────────────────────────────────────────────────────────┘  │    │
│  │                                                              │    │
│  │  Notes (optional)                                            │    │
│  │  ┌────────────────────────────────────────────────────────┐  │    │
│  │  │  WBC slightly elevated — recommend follow-up           │  │    │
│  │  └────────────────────────────────────────────────────────┘  │    │
│  │                                                              │    │
│  │  Abnormal Result?   ○ No   ● Yes                             │    │
│  │                                                              │    │
│  │                    [ Submit Result ]                         │    │
│  └──────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
```

---

### 6.11 Pharmacy & Prescriptions

#### Pharmacy Queue

```
┌──────────────────────────────────────────────────────────────────────┐
│ Pharmacy Queue                                                       │
│  [ Status ▼ ]  🔍 Patient name / prescription ID                     │
│──────────────────────────────────────────────────────────────────────│
│  ┌─────┬──────────┬──────────┬─────────────┬───────────┬──────────┐  │
│  │  #  │ Patient  │ Doctor   │ Items       │ Created   │ Status   │  │
│  ├─────┼──────────┼──────────┼─────────────┼───────────┼──────────┤  │
│  │ 201 │ P-0042   │ Dr.Mehta │ 2 items     │ 10:30 AM  │ ACTIVE   │  │
│  │ 202 │ P-0087   │ Dr.Shah  │ 3 items     │ 09:45 AM  │ PARTIAL  │  │
│  │ 200 │ P-0011   │ Dr.Mehta │ 1 item      │ 08:30 AM  │DISPENSED │  │
│  └─────┴──────────┴──────────┴─────────────┴───────────┴──────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

#### Dispense Prescription

```
┌──────────────────────────────────────────────────────────────────────┐
│ Prescription #201  —  P-0042 Rahul Sharma           ● ACTIVE       │
│ Doctor: Dr. Anil Mehta  │  Date: 26 May 2026 10:30                   │
│──────────────────────────────────────────────────────────────────────│
│  Notes: Take after food. Avoid driving after Metoprolol.             │
│                                                                      │
│  ┌──────────────────┬───────────┬──────┬──────────┬────────────────┐ │
│  │ Medicine         │ Dose/Freq │ Days │ Qty      │ Dispense       │ │
│  ├──────────────────┼───────────┼──────┼──────────┼────────────────┤ │
│  │ Aspirin 75mg     │ 1x daily  │  30  │ 30 units │ ☑ Dispensed    │ │
│  │ Metoprolol 25mg  │ 1x daily  │  30  │ 30 units │ ☐ [ Dispense ] │ │
│  └──────────────────┴───────────┴──────┴──────────┴────────────────┘ │
│                                                                      │
│  Stock:  Aspirin 75mg — 245 units  ✓                                 │
│          Metoprolol 25mg — 8 units  ⚠ Low Stock                      │
│                                                                      │
│                              [ Dispense Selected Items ]             │
└──────────────────────────────────────────────────────────────────────┘
```

---

### 6.12 Discharge Workflow

```
┌──────────────────────────────────────────────────────────────────────┐
│ Discharge Patient  —  Admission #A-0055                              │
│──────────────────────────────────────────────────────────────────────│
│  Patient: P-0042 Rahul Sharma    Bed: Ward A — A-04                  │
│  Admitted: 24 May 2026 14:00     Doctor: Dr. Anil Mehta              │
│  Duration: 2 days 6 hours                                            │
│──────────────────────────────────────────────────────────────────────│
│                                                                      │
│  ⚠ Warnings (non-blocking):                                          │
│  • 1 test still IN_PROGRESS (CBC)                                    │
│  • Prescription #201 PARTIALLY_DISPENSED                           │
│                                                                      │
│  Final Diagnosis  *                                                  │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ Hypertensive heart disease — stable. Follow-up in 2 weeks.     │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  Discharge Notes                                                     │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ Patient advised low-sodium diet. Echo scheduled 10 June.       │  │
│  │ Continue current medications. Avoid strenuous activity.        │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  [ Cancel ]                              [ Confirm Discharge ]       │
│  Bed A-04 will be released automatically on confirm.                 │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 7. Key UI Flows

### 7.1 Auth Flow

```
User visits /any-protected-route
        │
        ▼
AuthGuard checks auth.store (token present + not expired?)
        │
   No token ──────────────────────► /login
        │                              │
   Token present                       │
        │                           User enters email + password
        ▼                              │
  API: GET /users/me                POST /auth/login
  (rehydrate on refresh)               │
        │                           JWT returned
        │                              │
        ▼                           Store in zustand + localStorage
  Redirect to role dashboard           │
                                    Redirect to /dashboard/{role}
```

### 7.2 Patient Books Appointment

```
Patient: /appointments/new
        │
        ├─ Select Hospital (if multi-hospital)
        ├─ Select Doctor (with specialization filter)
        ├─ Select Date  →  GET /doctors/{id}/slots?date=...
        │                  (show booked gray, free clickable)
        ├─ Click slot  →  slot highlighted
        ├─ Enter reason
        └─ Submit  →  POST /appointments
                      │
                      ├─ 409  →  Toast "Slot no longer available"
                      │         refresh slots
                      │
                      └─ 201  →  Toast "Appointment booked"
                                 Redirect /appointments/{id}
```

### 7.3 Receptionist Walk-in Registration

```
Receptionist Dashboard  →  [ + New Patient ]
        │
        ▼
Patient Registration Wizard (3 steps)
        │
  Step 1: Personal info  →  Next
  Step 2: Medical info   →  Next
  Step 3: Emergency      →  [ Register Patient ]
        │
        └─  POST /patients
                │
                ├─ 400 Email exists  →  highlight field error
                │
                └─ 201  →  Patient created (P-XXXX generated)
                           Dialog: "Register now?" 
                           [ Book Appointment ]  [ Go to Profile ]
```

### 7.4 Doctor Consultation Flow

```
Doctor Dashboard  →  Click [ Start ] on IN_PROGRESS appointment
        │
        ▼
POST /appointments/{id}/check-in  (if not already CHECKED_IN)
        │
Consultation Room opens
        │
  ┌─────────────────────────────────────────┐
  │  Doctor can:                            │
  │  1. Write consultation notes            │
  │  2. Order tests  →  POST /tests         │
  │  3. Add prescription items              │
  │  4. Recommend admission                 │
  └─────────────────────────────────────────┘
        │
  [ Complete Consultation ]
        │
        ├─  POST /prescriptions  (if items exist)
        │
        └─  POST /appointments/{id}/complete
                │
                └─ Redirect to Doctor Dashboard
                   next patient auto-highlighted
```

### 7.5 Admit Patient → Assign Bed

```
Staff / Doctor: Bed Map  →  Click a FREE bed cell
        │
        ▼
Slide-over: Admit Patient Form
        │
  ├─ Search patient (GET /patients?search=...)
  ├─ Select doctor
  ├─ Optional: link appointment
  ├─ Enter preliminary diagnosis
  └─ [ Admit Patient ]
        │
        └─ POST /admissions
                │
                ├─ 409 Bed now occupied  →  Toast + close slide-over
                │                           Bed map refreshes
                │
                └─ 201  →  Bed cell turns RED "Occupied"
                           Toast "Patient admitted — Bed A-04"
```

### 7.6 Lab Test Lifecycle

```
Lab Tech: /tests  (Lab Queue)
        │
  Sees test in ORDERED state
        │
  [ Collect Sample ]  →  POST /tests/{id}/collect-sample
        │                Status: ORDERED → SAMPLE_COLLECTED
        │
  Runs analysis...
        │
  [ Enter Result ]  →  Opens result upload form
        │
     Submits  →  POST /tests/{id}/result
        │        { result_value, result_notes, is_abnormal }
        │        Status: → COMPLETED
        │
  If is_abnormal = true:
  └─  🔴 Notification sent to ordering doctor
      Red badge on Doctor Dashboard "Tests"
```

### 7.7 Pharmacy Dispense Flow

```
Pharmacist: /prescriptions  (Pharmacy Queue)
        │
  Sees ACTIVE prescription
        │
  Opens Prescription Detail
        │
  For each item:
  ├─ Check stock (shown inline, red if low)
  ├─ Tick items to dispense
  └─ [ Dispense Selected ]
        │
        └─ POST /prescriptions/{id}/dispense
                │
                ├─ 400 Insufficient stock  →  field error + stock count
                │
                └─ 200  →  Dispensed items checked off
                           Status updates:
                           all done    → DISPENSED  (green)
                           some done   → PARTIALLY_DISPENSED (amber)
```

### 7.8 Discharge Flow

```
Staff / Doctor: /admissions/{id}
        │
  [ Discharge Patient ]
        │
        ▼
Discharge Form (page or full-screen modal)
        │
  Shows:
  ├─ Warnings (pending tests, partial rx) — non-blocking
  ├─ Final diagnosis field (required)
  └─ Discharge notes field
        │
  [ Confirm Discharge ]
        │
        └─ POST /admissions/{id}/discharge
                │
                └─ 200  →  Admission status → DISCHARGED
                           Bed status → AVAILABLE (auto)
                           Bed Map cell turns GREEN
                           Redirect to /admissions (list)
                           Toast "Patient discharged — Bed A-04 now available"
```

---

## 8. State Management

```
┌────────────────────────────────────────────────────────────────────┐
│                      State Layers                                  │
├─────────────────────────────┬──────────────────────────────────────┤
│  Zustand (global client)    │  React Query (server cache)          │
├─────────────────────────────┼──────────────────────────────────────┤
│  auth.store                 │  useQuery("appointments")            │
│  ├─ token: string           │  useQuery("patients")                │ 
│  ├─ user: UserMe            │  useQuery(["doctor-slots", id, date])│
│  └─ logout()                │  useQuery(["bed-map", hospitalId])   │
│                             │  useMutation("book-appointment")     │
│  ui.store                   │  useMutation("admit-patient")        │
│  ├─ sidebarOpen: bool       │  useMutation("discharge")            │
│  └─ activeHospitalId: int   │  useMutation("dispense")             │
└─────────────────────────────┴──────────────────────────────────────┘

React Query config:
  staleTime:  30s  (most resources)
  staleTime:  5s   (bed-map — near real-time)
  refetchInterval: 30s (bed-map while on /beds page)
  retry:      2 (then show error state)
```

---

## 9. API Integration Layer

```
// src/api/client.ts
const client = axios.create({ baseURL: "/api/v1" });

client.interceptors.request.use(config => {
  const token = useAuthStore.getState().token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

client.interceptors.response.use(
  res => res,
  async err => {
    if (err.response?.status === 401) {
      // attempt token refresh, else logout → /login
    }
    if (err.response?.status === 422) {
      // extract pydantic errors → map to form fields
    }
    return Promise.reject(err);
  }
);
```

### API Function Pattern

```
// src/api/appointments.ts
export const bookAppointment = (data: BookAppointmentPayload) =>
  client.post<AppointmentResponse>("/appointments", data).then(r => r.data);

export const getAvailableSlots = (doctorId: number, date: string) =>
  client.get<SlotResponse[]>(`/doctors/${doctorId}/slots?date=${date}`)
        .then(r => r.data);

// src/hooks/useAppointments.ts
export const useBookAppointment = () =>
  useMutation({
    mutationFn: bookAppointment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["appointments"] });
      toast.success("Appointment booked successfully");
    },
    onError: (err: AxiosError) => {
      if (err.response?.status === 409)
        toast.error("Slot no longer available — please pick another");
    },
  });
```

---

## 10. Notifications & Alerts

```
┌─────────────────────────────────────────────────────────────────────┐
│  Notification Types                                                 │
├──────────────────────┬──────────────────────────────────────────────┤
│ Toast (ephemeral)    │ Success/error on every mutation              │
│                      │ e.g. "Appointment booked", "Patient admitted"│
├──────────────────────┼──────────────────────────────────────────────┤
│ Alert banner         │ Low stock medicines on pharmacy pages        │
│                      │ Abnormal test results on doctor dashboard    │
├──────────────────────┼──────────────────────────────────────────────┤
│ Bell (topbar badge)  │ Count of: abnormal tests + pending actions   │
│                      │ Dropdown shows last 10 items                 │
├──────────────────────┼──────────────────────────────────────────────┤
│ Inline warnings      │ On discharge form — pending tests, partial   │
│                      │ prescriptions (amber, non-blocking)          │
├──────────────────────┼──────────────────────────────────────────────┤
│ Confirm dialog       │ Before cancel appointment, delete, discharge │
└──────────────────────┴──────────────────────────────────────────────┘
```

---

## 11. Responsive & Accessibility Notes

```
Breakpoints (Tailwind):
  sm  640px   mobile landscape / small tablet
  md  768px   tablet portrait
  lg  1024px  desktop (primary target for HMS staff)
  xl  1280px  wide desktop

Layout behaviour:
  < md  →  sidebar collapses to bottom nav (5 key icons)
  ≥ lg  →  sidebar always visible, 240px wide
  Bed map  →  horizontal scroll on small screens, grid reflows

Accessibility:
  All interactive elements have aria-labels
  Status badges include screen-reader text (not color-only)
  Form errors announced via aria-live region
  Keyboard navigation: tab order follows visual order
  Focus trap in modals and slide-overs
  Color contrast: all text ≥ 4.5:1 against background
```

---

### 6.13 Billing & Payment

#### Billing Queue (Staff / Receptionist)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Billing                                         [ + Create Bill ]    │
│  [ Status ▼ ]  [ Type ▼ ]  🔍 Patient name / Bill ID                 │
│──────────────────────────────────────────────────────────────────────│
│  ┌────────┬──────────┬────────────────┬──────────┬────────┬───────┐  │
│  │ Bill # │ Patient  │ Type           │ Amount   │ Status │Action │  │
│  ├────────┼──────────┼────────────────┼──────────┼────────┼───────┤  │
│  │ B-1042 │ P-0042   │ OPD Visit      │ ₹ 800    │PENDING │[ Pay ]│  │
│  │ B-1041 │ P-0087   │ Lab Tests      │ ₹ 1,200  │PENDING │[ Pay ]│  │
│  │ B-1040 │ P-0011   │ Inpatient Stay │ ₹18,500  │PARTIAL │[ Pay ]│  │
│  │ B-1039 │ P-0055   │ OPD Visit      │ ₹ 400    │  PAID  │[View] │  │
│  └────────┴──────────┴────────────────┴──────────┴────────┴───────┘  │
│                                        Showing 4 of 42  [ < 1 > ]    │
└──────────────────────────────────────────────────────────────────────┘
```

#### Bill Detail — Invoice Summary

```
┌──────────────────────────────────────────────────────────────────────┐
│ < Billing  /  Bill #B-1042                         ● PENDING         │
│──────────────────────────────────────────────────────────────────────│
│  Patient: P-0042  Rahul Sharma          Date: 26 May 2026 11:00      │
│  Hospital: City Hospital                Type: OPD Visit              │
│──────────────────────────────────────────────────────────────────────│
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Bill Line Items                                               │  │
│  │  ──────────────────────────────────────────────────────────    │  │
│  │  Description               Category       Qty    Amount        │  │
│  │  ─────────────────────────────────────────────────────────     │  │
│  │  Consultation — Dr. Mehta  CONSULTATION    1     ₹  800        │  │
│  │  CBC Blood Test            LAB_TEST        1     ₹  350        │  │
│  │  ECG                       LAB_TEST        1     ₹  250        │  │
│  │  Aspirin 75mg × 30         MEDICINE        30    ₹   90        │  │
│  │  Metoprolol 25mg × 30      MEDICINE        30    ₹  210        │  │
│  │  ─────────────────────────────────────────────────────────     │  │
│  │  Subtotal                                        ₹ 1,700       │  │
│  │  Discount (Senior Citizen 10%)                  − ₹  170       │  │
│  │  Tax (GST 5% on services)                       + ₹   53       │  │
│  │  ─────────────────────────────────────────────────────────     │  │
│  │  Total                                           ₹ 1,583       │  │
│  │                                                                │  │
│  │  Amount Paid                                     ₹     0       │  │
│  │  Balance Due                                     ₹ 1,583       │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  Insurance                                                           │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  No insurance claim linked.   [ + Add Insurance Claim ]        │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  [ Download Invoice PDF ]          [ Proceed to Payment → ]          │
└──────────────────────────────────────────────────────────────────────┘
```

#### Payment Modal — Choose Payment Method

```
┌────────────────────────────────────────────────────────────┐
│  Pay Bill #B-1042                                    ✕     │
│  Patient: Rahul Sharma   Balance Due: ₹ 1,583              │
│────────────────────────────────────────────────────────────│
│                                                            │
│  Amount to Pay                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ₹  1,583                                            │  │
│  └──────────────────────────────────────────────────────┘  │
│  (Partial payment allowed — enter any amount ≤ balance)    │
│                                                            │
│  Payment Method                                            │
│  ┌───────────────────┐ ┌────────────────┐ ┌────────────┐   │
│  │  💵  Cash         │ │ 💳  Card       │ │ 📱  UPI    │   │
│  │  [ Select ]       │ │ [ Select ]     │ │[●Selected] │   │
│  └───────────────────┘ └────────────────┘ └────────────┘   │
│  ┌───────────────────┐ ┌────────────────┐                  │
│  │  🏦  Net Banking  │ │ 🛡 Insurance  │                   │
│  │  [ Select ]       │ │ [ Select ]     │                  │
│  └───────────────────┘ └────────────────┘                  │
│                                                            │
│  ── UPI Details ─────────────────────────────────────────  │
│  UPI ID / Phone Number                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  rahul@upi                                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Generate QR Code  (patient scans on their phone)    │  │
│  │  ┌────────────────────────────┐                      │  │
│  │  │  ▓▓▓░░░▓▓░▓░░▓▓            │  ← QR placeholder    │  │
│  │  │  ░▓░▓▓░░░▓░▓▓░░            │                      │  │
│  │  │  ▓░░░▓▓░░░▓░░▓▓            │                      │  │
│  │  └────────────────────────────┘                      │  │
│  │  Scan or enter UPI ID to pay  ₹ 1,583                │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  Transaction Reference (auto-filled on success)            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  TXN-2026052600442                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  Notes (optional)                                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Patient paid via PhonePe                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│          [ Cancel ]          [ Confirm Payment ]           │
└────────────────────────────────────────────────────────────┘
```

#### Card Payment Sub-form

```
┌──────────────────────────────────────────────────────────┐
│  ── Card Details ─────────────────────────────────────── │
│  Card Number                                             │
│  ┌──────────────────────────────────────────────────┐    │
│  │  4111  1111  1111  1111                          │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  ┌───────────────────────┐  ┌──────────────────────┐     │
│  │ Expiry     MM / YY    │  │ CVV      •••         │     │
│  │ 12 / 28               │  │                      │     │
│  └───────────────────────┘  └──────────────────────┘     │
│  ┌──────────────────────────────────────────────────┐    │
│  │ Cardholder Name:  RAHUL SHARMA                   │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

#### Insurance Claim Sub-form

```
┌──────────────────────────────────────────────────────────┐
│  ── Insurance Claim ──────────────────────────────────── │
│  Insurance Provider                                      │
│  ┌──────────────────────────────────────────────────┐    │
│  │ Star Health Insurance                       ▼    │    │
│  └──────────────────────────────────────────────────┘    │
│  Policy Number                   Member ID               │
│  ┌──────────────────────┐  ┌──────────────────────┐      │
│  │ POL-2024-00871        │  │ MEM-00142            │     │
│  └──────────────────────┘  └──────────────────────┘      │
│  Pre-Authorization Code (if available)                   │
│  ┌──────────────────────────────────────────────────┐    │
│  │ AUTH-8821-XZ                                     │    │
│  └──────────────────────────────────────────────────┘    │
│  Claimed Amount     Patient Co-pay                       │
│  ┌──────────────┐   ┌──────────────┐                     │
│  │  ₹ 1,200     │   │  ₹   383     │                     │
│  └──────────────┘   └──────────────┘                     │
│  [ Submit Claim & Record Co-pay ]                        │
└──────────────────────────────────────────────────────────┘
```

#### Payment Success Receipt

```
┌────────────────────────────────────────────────────────────┐
│                     ✓  Payment Successful                  │
│────────────────────────────────────────────────────────────│
│                                                            │
│  Receipt No:   REC-2026052600442                           │
│  Date & Time:  26 May 2026  11:45 AM                       │
│  Patient:      P-0042  Rahul Sharma                        │
│  Bill:         B-1042  —  OPD Visit                        │
│                                                            │
│  Amount Paid:  ₹ 1,583                                     │
│  Method:       UPI  (rahul@upi)                            │
│  Transaction:  TXN-2026052600442                           │
│                                                            │
│  Balance:      ₹ 0  (FULLY PAID)                           │
│                                                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │  [ Download Receipt PDF ]  [ Send to Email/SMS ]   │    │
│  └────────────────────────────────────────────────────┘    │
│                                                            │
│                [ Back to Billing Queue ]                   │
└────────────────────────────────────────────────────────────┘
```

---

### 6.14 Payment History

#### Staff / Admin View

```
┌──────────────────────────────────────────────────────────────────────┐
│ Payment History                              [ Export CSV ]          │
│  🔍 Patient / TXN ID   [ Method ▼ ] [ Status ▼ ] [ Date Range ▼ ]    │
│──────────────────────────────────────────────────────────────────────│
│  ┌───────────┬──────────┬────────┬──────────┬──────────┬──────────┐  │
│  │ Receipt   │ Patient  │ Method │ Amount   │ Date     │ Status   │  │
│  ├───────────┼──────────┼────────┼──────────┼──────────┼──────────┤  │
│  │ REC-0442  │ P-0042   │ UPI    │ ₹ 1,583  │ 26 May   │ SUCCESS  │  │
│  │ REC-0441  │ P-0087   │ Card   │ ₹ 2,400  │ 26 May   │ SUCCESS  │  │
│  │ REC-0440  │ P-0011   │ Cash   │ ₹ 5,000  │ 25 May   │ SUCCESS  │  │
│  │ REC-0439  │ P-0055   │ UPI    │ ₹   800  │ 25 May   │ REFUNDED │  │
│  │ REC-0438  │ P-0012   │ Card   │ ₹ 1,200  │ 25 May   │ FAILED   │  │
│  └───────────┴──────────┴────────┴──────────┴──────────┴──────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Summary — Last 30 Days                                      │    │
│  │  Total Collected: ₹ 4,12,800   │  Refunds: ₹ 800             │    │
│  │  UPI: 42%  Card: 31%  Cash: 27%                              │    │
│  └──────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
```

#### Patient View — My Bills & Payments

```
┌──────────────────────────────────────────────────────────────────────┐
│ My Bills & Payments                                                  │
│──────────────────────────────────────────────────────────────────────│
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Outstanding Balance                                           │  │
│  │  ┌──────────────────────────────┐                              │  │
│  │  │  Bill #B-1044   ₹ 350 PENDING│  [ Pay Now ]                 │  │
│  │  │  Lab Tests — 26 May 2026     │                              │  │
│  │  └──────────────────────────────┘                              │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  Payment History                                                     │
│  ┌────────────┬──────────────────┬────────┬───────────┬──────────┐   │
│  │ Date       │ Description      │ Method │ Amount    │ Receipt  │   │
│  ├────────────┼──────────────────┼────────┼───────────┼──────────┤   │
│  │ 26 May '26 │ OPD Visit #B1042 │ UPI    │ ₹ 1,583   │ [📄 View]│   │
│  │ 24 May '26 │ Lab Tests #B1038 │ Card   │ ₹   600   │ [📄 View]│   │
│  │ 10 May '26 │ OPD Visit #B1021 │ Cash   │ ₹   400   │ [📄 View]│   │
│  └────────────┴──────────────────┴────────┴───────────┴──────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 7.9 Payment Flow (OPD)

```
After consultation completes:
        │
        ▼
System auto-generates Bill  (DRAFT → PENDING)
  Items pulled from:
  ├─ appointment.consultation_fee  (doctor)
  ├─ medical_tests ordered during appointment
  └─ prescription_items dispensed

Receptionist / Patient:  /billing/B-1042
        │
  Reviews invoice line items
        │
  [ Proceed to Payment ]
        │
        ▼
Payment Modal opens
  ├─ Amount pre-filled (full balance)
  ├─ Partial amount allowed (edit field)
  │
  ├─ Select Method:
  │   ├─ Cash      → Enter amount received → [ Confirm ]
  │   ├─ Card      → Enter card details → [ Charge ]
  │   ├─ UPI       → Enter UPI ID → QR shown → await confirmation
  │   ├─ Net Bank  → Redirect to bank gateway (external)
  │   └─ Insurance → Enter policy + claim amount + co-pay
  │
  └─ POST /payments
          │
          ├─ FAILED  →  Toast "Payment failed — please retry"
          │             method form remains open
          │
          └─ SUCCESS →  Bill status:
                          full amount  → PAID   (green)
                          partial      → PARTIALLY_PAID (indigo)
                        Receipt page shown
                        Toast "Payment of ₹1,583 received"
                        Option: [ Send SMS receipt ] [ Download PDF ]
```

---

## 7.10 Inpatient Final Billing & Discharge Payment

```
Staff initiates discharge:
  /admissions/{id}/discharge  →  Discharge form
        │
        │  (alongside diagnosis + notes)
        ▼
  [ Generate Final Bill ]  button  (or auto-generated)
        │
        ▼
BillingService.generate_inpatient_bill(admission_id)
  Aggregates all charges:
  ├─ Room charges:  bed_type × nights_admitted
  ├─ Doctor visits: all appointments linked to admission
  ├─ Lab tests:     all tests ordered during admission
  ├─ Medicines:     all prescription items dispensed
  └─ Procedures:    any additional charges added by staff
        │
        ▼
Bill Detail page  /billing/B-1045
  ┌──────────────────────────────────────────────────────────┐
  │  Room (Ward A Standard)  2 days × ₹ 2,000  = ₹  4,000    │
  │  Doctor Consultation     2 visits × ₹ 800  = ₹  1,600    │
  │  CBC + ECG + X-Ray                          = ₹  1,200   │
  │  Aspirin + Metoprolol (30 days)             = ₹    300   │
  │  ─────────────────────────────────────────────────────   │
  │  Subtotal                                   = ₹  7,100   │
  │  Insurance claim deduction (Star Health)    − ₹  5,000   │
  │  Patient co-pay                             = ₹  2,100   │
  └──────────────────────────────────────────────────────────┘
        │
  Patient / Family pays co-pay at desk
        │
  POST /payments  { amount: 2100, method: "CASH", bill_id }
        │
        └─ 200 SUCCESS
               Bill → PAID
               Discharge completes  (beds freed, summary emailed)
```

---

## Payment Data Model (Frontend Types)

```typescript
// Bill — groups all charges for a visit or admission
interface Bill {
  id: number;
  bill_number: string;          // "B-1042"
  patient_id: number;
  patient: PatientBrief;
  appointment_id?: number;
  admission_id?: number;
  bill_type: "OPD" | "INPATIENT" | "LAB" | "PHARMACY";
  status: "DRAFT" | "PENDING" | "PARTIALLY_PAID" | "PAID" | "OVERDUE" | "WAIVED";
  items: BillLineItem[];
  subtotal: number;
  discount: number;
  tax: number;
  total: number;
  amount_paid: number;
  balance_due: number;
  insurance_claim?: InsuranceClaim;
  created_at: string;
  updated_at: string;
}

interface BillLineItem {
  id: number;
  description: string;
  category: "CONSULTATION" | "LAB_TEST" | "MEDICINE" | "ROOM_CHARGE" | "PROCEDURE" | "OTHER";
  quantity: number;
  unit_price: number;
  total_price: number;
  reference_id?: number;        // appointment_id, test_id, prescription_item_id
}

// Payment — one transaction against a bill
interface Payment {
  id: number;
  receipt_number: string;       // "REC-0442"
  bill_id: number;
  patient_id: number;
  amount: number;
  method: "CASH" | "CARD" | "UPI" | "NET_BANKING" | "INSURANCE";
  status: "SUCCESS" | "PENDING" | "FAILED" | "REFUNDED";
  transaction_ref?: string;     // UPI txn ID, card auth code
  notes?: string;
  collected_by: number;         // staff user_id
  paid_at: string;
}

interface InsuranceClaim {
  id: number;
  bill_id: number;
  provider_name: string;
  policy_number: string;
  member_id: string;
  pre_auth_code?: string;
  claimed_amount: number;
  approved_amount?: number;
  patient_copay: number;
  status: "SUBMITTED" | "APPROVED" | "REJECTED" | "PARTIALLY_APPROVED";
}
```

---

## Payment API Hooks

```typescript
// src/hooks/useBilling.ts
export const useBill = (billId: number) =>
  useQuery({ queryKey: ["bill", billId], queryFn: () => getBill(billId) });

export const usePatientBills = (patientId: number) =>
  useQuery({ queryKey: ["bills", "patient", patientId],
             queryFn: () => getPatientBills(patientId) });

export const useCreatePayment = () =>
  useMutation({
    mutationFn: (data: CreatePaymentPayload) => createPayment(data),
    onSuccess: (payment, vars) => {
      queryClient.invalidateQueries({ queryKey: ["bill", vars.bill_id] });
      queryClient.invalidateQueries({ queryKey: ["payments"] });
      toast.success(`Payment of ₹${payment.amount} received`);
      navigate(`/payments/${payment.id}`);   // receipt page
    },
    onError: (err: AxiosError) => {
      if (err.response?.status === 400)
        toast.error("Payment failed — " + err.response.data.detail);
    },
  });

export const useRefundPayment = () =>
  useMutation({
    mutationFn: (paymentId: number) => refundPayment(paymentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["payments"] });
      toast.success("Refund processed successfully");
    },
  });

// src/hooks/usePayments.ts
export const usePaymentHistory = (filters?: PaymentFilters) =>
  useQuery({ queryKey: ["payments", filters],
             queryFn: () => getPayments(filters) });

export const useMyPayments = () =>
  useQuery({ queryKey: ["payments", "mine"],
             queryFn: () => getMyPayments() });
```

---

## Payment State (Zustand)

```typescript
// Added to ui.store.ts
interface UIStore {
  // ... existing fields
  activePaymentBillId: number | null;
  setActivePaymentBillId: (id: number | null) => void;
  paymentStep: "method_select" | "details" | "processing" | "receipt";
  setPaymentStep: (step: UIStore["paymentStep"]) => void;
}
```

---

## Payment Notification Rules

```
┌──────────────────────────┬───────────────────────────────────────────┐
│ Event                    │ Notification                              │
├──────────────────────────┼───────────────────────────────────────────┤
│ Bill generated (PENDING) │ Bell badge +1 for receptionist / patient  │
│ Payment SUCCESS          │ Toast ✓ + SMS/email receipt (optional)    │
│ Payment FAILED           │ Toast ⚠ "Payment failed — try again"      │
│ Bill OVERDUE (> 7 days)  │ Alert banner on billing page (red)        │
│ Insurance claim REJECTED │ Alert banner + bell badge for admin       │
│ Refund processed         │ Toast ✓ + updated receipt                 │
│ Partial payment          │ Amber banner "Balance ₹X still pending"   │
└──────────────────────────┴───────────────────────────────────────────┘
```
