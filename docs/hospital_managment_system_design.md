# Hospital Management System — Full Design

## Table of Contents

1. [System Overview](#1-system-overview)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Domain Modules](#3-domain-modules)
4. [Entity Relationship Diagram](#4-entity-relationship-diagram)
5. [Database Schemas](#5-database-schemas)
   - 5.1 Users & Roles
   - 5.2 Hospitals & Wards
   - 5.3 Doctors
   - 5.4 Staff
   - 5.5 Patients
   - 5.6 Beds
   - 5.7 Appointments
   - 5.8 Admissions
   - 5.9 Doctor Availability / Schedules
   - 5.10 Medical Tests (Checkings)
   - 5.11 Prescriptions & Medicines
   - 5.12 Billing & Payments
6. [API Endpoints](#6-api-endpoints)
7. [Key Flow Diagrams](#7-key-flow-diagrams)
   - 7.1 Patient Registration
   - 7.2 Book an Appointment
   - 7.3 Appointment → Consultation → Prescription
   - 7.4 Admit Patient & Bed Allocation
   - 7.5 Order a Medical Test
   - 7.6 Medicine Dispensing
   - 7.7 Discharge Patient
   - 7.8 OPD Billing & Payment
   - 7.9 Inpatient Final Bill & Discharge Payment
8. [Status State Machines](#8-status-state-machines)
9. [Role & Permission Matrix](#9-role--permission-matrix)
10. [Error Catalogue](#10-error-catalogue)
11. [Layer Architecture](#11-layer-architecture)

---

## 1. System Overview

The Hospital Management System (HMS) is a multi-tenant REST API built on the existing FastAPI + PostgreSQL stack. It digitalises the full patient lifecycle — from first registration and appointment booking, through consultation, diagnostics, pharmacy dispensing, and inpatient bed management, to final discharge.

**Core actors:**
| Actor        | Description                                              |
|--------------|----------------------------------------------------------|
| Admin        | Hospital superuser — manages doctors, staff, beds, drugs |
| Doctor       | Books schedules, consults patients, orders tests/meds    |
| Staff/Nurse  | Manages bed allocation, administers medicines, test runs |
| Patient      | Books appointments, views own records                    |
| Receptionist | Registers patients, books appointments on their behalf   |

---

## 2. High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                         Client Applications                            │
│          Web App  │  Mobile App  │  Reception Kiosk  │  Lab Terminal   │
└──────────┬─────────────┬──────────────────┬─────────────────┬──────────┘
           │             │                  │                 │
           └─────────────┴──────────┬───────┴─────────────────┘
                                    │  HTTPS / REST JSON
                                    ▼
┌───────────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                            │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  Middleware: RequestLogging, CORS, RateLimiting                 │  │
│  └──────────────────────────┬──────────────────────────────────────┘  │
│                             │                                         │
│  ┌──────────────────────────▼──────────────────────────────────────┐  │
│  │  API Router  /api/v1                                            │  │
│  │                                                                 │  │
│  │  /auth        /users       /hospitals    /doctors               │  │
│  │  /patients    /staff       /beds         /wards                 │  │
│  │  /appointments             /admissions                          │  │
│  │  /availability             /tests        /test-results          │  │
│  │  /prescriptions            /medicines    /pharmacy              │  │
│  └──────────────────────────┬──────────────────────────────────────┘  │
│                             │                                         │
│  ┌───────────┐  ┌───────────▼────────┐  ┌───────────────────────────┐ │
│  │  FastAPI  │  │  Services Layer    │  │  Dependencies             │ │
│  │  Deps     │  │  (business logic)  │  │  get_db / get_current_user│ │
│  └───────────┘  └───────────┬────────┘  └───────────────────────────┘ │
│                             │                                         │
│  ┌──────────────────────────▼──────────────────────────────────────┐  │
│  │  Repository Layer  (SQLAlchemy ORM)                             │  │
│  │  BaseRepository[T] → DoctorRepository, PatientRepository, ...   │  │
│  └──────────────────────────┬──────────────────────────────────────┘  │
│                             │                                         │
│  ┌──────────────────────────▼──────────────────────────────────────┐  │
│  │  ORM Models  (SQLAlchemy 2.x declarative)                       │  │
│  └──────────────────────────┬──────────────────────────────────────┘  │
└────────────────────────────-│─────────────────────────────────────────┘
                              │
            ┌─────────────────┴──────────────────┐
            │                                    │
            ▼                                    ▼
  ┌──────────────────────┐           ┌───────────────────────┐
  │   PostgreSQL  DB     │           │   Redis (optional)    │
  │   Primary store      │           │   Session cache       │
  │   Alembic migrations │           │   Rate-limit counters │
  └──────────────────────┘           └───────────────────────┘
```

---

## 3. Domain Modules

```
┌─────────────────────────────────────────────────────────────────────┐
│                        HMS Domain Modules                           │
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────────┐ │
│  │   Auth /     │   │  Hospital /  │   │     Doctor Module        │ │
│  │   Users      │   │  Ward / Bed  │   │  Profile, Specialization │ │
│  │              │   │              │   │  Schedule, Availability  │ │
│  └──────────────┘   └──────────────┘   └──────────────────────────┘ │
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────────┐ │
│  │  Patient     │   │ Appointment  │   │   Admission / Discharge  │ │
│  │  Registration│   │  Booking     │   │   Bed Assignment         │ │
│  │  Medical Hx  │   │  Consultation│   │                          │ │
│  └──────────────┘   └──────────────┘   └──────────────────────────┘ │
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌─────────────────────────┐  │
│  │  Medical     │   │  Pharmacy /  │   │  Staff                  │  │
│  │  Tests       │   │  Medicine    │   │  Nurses, Lab Tech,      │  │
│  │  Lab Results │   │  Prescription│   │  Receptionist           │  │
│  └──────────────┘   └──────────────┘   └─────────────────────────┘  │
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐                                │
│  │  Billing     │   │  Payments &  │                                │
│  │  Invoice Gen │   │  Insurance   │                                │
│  │  Line Items  │   │  Claims      │                                │
│  └──────────────┘   └──────────────┘                                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Entity Relationship Diagram

```
                           ┌─────────────┐
                           │   Hospital  │
                           │─────────────│
                           │ id          │
                           │ name        │
                           │ address     │
                           │ city        │
                           │ mobile      │
                           │ is_active   │
                           └──────┬──────┘
                                  │  1
                    ┌────────────┼──────────────┐
                   M│           M│             M│
            ┌───────▼──────┐ ┌───▼───────┐ ┌────▼──────┐
            │    Ward      │ │  Doctor   │ │   Staff   │
            │──────────────│ │───────────│ │───────────│
            │ id           │ │ id        │ │ id        │
            │ hospital_id  │ │hospital_id│ │hospital_id│
            │ name         │ │user_id    │ │user_id    │
            │ ward_type    │ │license_no │ │role       │
            │ total_beds   │ │speciality │ │department │
            └──────┬───────┘ └─────┬─────┘ └───────────┘
                  1│               │1
                  M│               │M
            ┌──────▼───────┐ ┌─────▼───────────────┐
            │     Bed      │ │  DoctorAvailability │
            │──────────────│ │────────────────────-│
            │ id           │ │ id                  │
            │ ward_id      │ │ doctor_id           │
            │ bed_number   │ │ day_of_week         │
            │ bed_type     │ │ start_time          │
            │ status       │ │ end_time            │
            └──────┬───────┘ │ slot_duration_mins  │
                  1│         │ max_slots           │
                  M│         │ is_active           │
            ┌──────▼───────┐ └─────────────────────┘
            │  Admission   │
            │──────────────│         ┌──────────────┐
            │ id           │         │   Patient    │
            │ bed_id  ─────┼──────── │──────────────│
            │ patient_id ──┼──────►  │ id           │
            │ doctor_id    │         │ user_id      │
            │ admitted_at  │         │ dob          │
            │ discharged_at│         │ blood_group  │
            │ status       │         │ gender       │
            └──────────────┘         │ emergency_no │
                                     └──────┬───────┘
                                           1│
                    ┌───────────────────────┼─────────────────────┐
                   M│                      M│                    M│
            ┌───────▼──────┐     ┌──────────▼────────┐  ┌────────▼──────┐
            │ Appointment  │     │  MedicalTest      │  │  Prescription │
            │──────────────│     │───────────────────│  │───────────────│
            │ id           │     │ id                │  │ id            │
            │ patient_id   │     │ patient_id        │  │ patient_id    │
            │ doctor_id    │     │ appointment_id    │  │ appointment_id│
            │ hospital_id  │     │ doctor_id         │  │ doctor_id     │
            │ scheduled_at │     │ test_type         │  │ notes         │
            │ status       │     │ ordered_at        │  │ created_at    │
            │ reason       │     │ result_at         │  └──────┬────────┘
            │ notes        │     │ result_value      │        1│
            └──────────────┘     │ status            │        M│
                                 └───────────────────┘  ┌──────▼──────────────┐
                                                        │  PrescriptionItem   │
                                                        │─────────────────────│
                                                        │ id                  │
                                                        │ prescription_id     │
                                                        │ medicine_id         │
                                                        │ dosage              │
                                                        │ frequency           │
                                                        │ duration_days       │
                                                        └─────────────────────┘
                                                                    │
                                                                   M│ medicine_id
                                                            ┌───────▼──────┐
                                                            │   Medicine   │
                                                            │──────────────│
                                                            │ id           │
                                                            │ name         │
                                                            │ category     │
                                                            │ unit         │
                                                            │ stock_qty    │
                                                            │ min_stock    │
                                                            │ is_active    │
                                                            └──────────────┘

Patient (1) ──────────────────────────────────────────── M
        │
        ▼
┌───────────────┐    1        M   ┌──────────────────┐
│     Bill      │───────────────► │   BillLineItem   │
│───────────────│                 │──────────────────│
│ id            │                 │ id               │
│ patient_id    │                 │ bill_id          │
│ appointment_id│                 │ description      │
│ admission_id  │                 │ category         │
│ bill_type     │                 │ quantity         │
│ status        │                 │ unit_price       │
│ subtotal      │                 │ total_price      │
│ discount      │                 │ reference_id     │
│ tax           │                 └──────────────────┘
│ total         │
│ amount_paid   │   1        M   ┌──────────────────┐
│ balance_due   │──────────────► │    Payment       │
└───────────────┘                │──────────────────│
        │                        │ id               │
        │ 0..1                   │ bill_id          │
        ▼                        │ amount           │
┌────────────────┐               │ method           │
│ InsuranceClaim │               │ status           │
│────────────────│               │ transaction_ref  │
│ id             │               │ collected_by     │
│ bill_id        │               │ paid_at          │
│ provider_name  │               └──────────────────┘
│ policy_number  │
│ member_id      │
│ claimed_amount │
│ approved_amount│
│ patient_copay  │
│ status         │
└────────────────┘
```

---

## 5. Database Schemas

### 5.1 Users & Roles

```
┌──────────────────────────────────────────────────────────────┐
│                           users                              │
├────────────────┬──────────────────┬──────────────────────────┤
│ id             │ INTEGER          │ PK                       │
│ email          │ VARCHAR          │ UNIQUE, NOT NULL         │
│ hashed_password│ VARCHAR          │ NOT NULL                 │
│ full_name      │ VARCHAR          │ nullable                 │
│ is_active      │ BOOLEAN          │ default TRUE             │
│ is_superuser   │ BOOLEAN          │ default FALSE            │
│ created_at     │ TIMESTAMPTZ      │ default NOW()            │
│ updated_at     │ TIMESTAMPTZ      │ default NOW()            │
└────────────────┴──────────────────┴──────────────────────────┘

Role is determined by which profile table has a FK to this user:
  users.id ← doctors.user_id       → role = DOCTOR
  users.id ← staff.user_id         → role = STAFF
  users.id ← patients.user_id      → role = PATIENT
  users.is_superuser = true         → role = ADMIN
```

### 5.2 Hospitals & Wards

```
┌──────────────────────────────────────────────────────────────┐
│                         hospitals                            │
├────────────────┬──────────────────┬──────────────────────────┤
│ id             │ INTEGER          │ PK                       │
│ name           │ VARCHAR          │ UNIQUE, NOT NULL         │
│ address        │ VARCHAR          │ NOT NULL                 │
│ city           │ VARCHAR          │ NOT NULL                 │
│ mobile_number  │ VARCHAR          │ NOT NULL                 │
│ is_active      │ BOOLEAN          │ default TRUE             │
│ created_by     │ INTEGER          │ FK → users.id            │
│ updated_by     │ INTEGER          │ FK → users.id            │
│ created_at     │ TIMESTAMPTZ      │                          │
│ updated_at     │ TIMESTAMPTZ      │                          │
└────────────────┴──────────────────┴──────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                           wards                              │
├────────────────┬──────────────────┬──────────────────────────┤
│ id             │ INTEGER          │ PK                       │
│ hospital_id    │ INTEGER          │ FK → hospitals.id        │
│ name           │ VARCHAR          │ NOT NULL                 │
│ ward_type      │ ENUM             │ GENERAL, ICU, EMERGENCY, │
│                │                  │ MATERNITY, PEDIATRIC,    │
│                │                  │ SURGICAL, PRIVATE        │
│ floor          │ INTEGER          │ nullable                 │
│ total_beds     │ INTEGER          │ computed / managed       │
│ is_active      │ BOOLEAN          │ default TRUE             │
│ created_at     │ TIMESTAMPTZ      │                          │
└────────────────┴──────────────────┴──────────────────────────┘
```

### 5.3 Doctors

```
┌──────────────────────────────────────────────────────────────┐
│                          doctors                             │
├────────────────┬──────────────────┬──────────────────────────┤
│ id             │ INTEGER          │ PK                       │
│ user_id        │ INTEGER          │ FK → users.id, UNIQUE    │
│ hospital_id    │ INTEGER          │ FK → hospitals.id        │
│ license_number │ VARCHAR          │ UNIQUE, NOT NULL         │
│ specialization │ VARCHAR          │ NOT NULL                 │
│ department     │ VARCHAR          │ nullable                 │
│ qualification  │ VARCHAR          │ NOT NULL                 │
│ experience_yrs │ INTEGER          │ default 0                │
│ consultation_fee│ NUMERIC(10,2)   │ NOT NULL                 │
│ is_active      │ BOOLEAN          │ default TRUE             │
│ created_at     │ TIMESTAMPTZ      │                          │
│ updated_at     │ TIMESTAMPTZ      │                          │
└────────────────┴──────────────────┴──────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    doctor_availability                       │
├────────────────┬──────────────────┬──────────────────────────┤
│ id             │ INTEGER          │ PK                       │
│ doctor_id      │ INTEGER          │ FK → doctors.id          │
│ day_of_week    │ ENUM             │ MON,TUE,WED,THU,FRI,     │
│                │                  │ SAT,SUN                  │
│ start_time     │ TIME             │ e.g. 09:00               │
│ end_time       │ TIME             │ e.g. 17:00               │
│ slot_duration  │ INTEGER          │ minutes, default 30      │
│ max_slots      │ INTEGER          │ computed from window     │
│ is_active      │ BOOLEAN          │ default TRUE             │
│ valid_from     │ DATE             │ schedule start date      │
│ valid_until    │ DATE             │ nullable — ongoing       │
└────────────────┴──────────────────┴──────────────────────────┘
```

### 5.4 Staff

```
┌───────────────────────────────────────────────────────────────┐
│                           staff                               │
├────────────────┬──────────────────┬───────────────────────────┤
│ id             │ INTEGER          │ PK                        │
│ user_id        │ INTEGER          │ FK → users.id, UNIQUE     │
│ hospital_id    │ INTEGER          │ FK → hospitals.id         │
│ role           │ ENUM             │ NURSE, RECEPTIONIST,      │
│                │                  │ LAB_TECHNICIAN, PHARMACIST│
│                │                  │ ADMIN_STAFF               │
│ department     │ VARCHAR          │ nullable                  │
│ employee_id    │ VARCHAR          │ UNIQUE per hospital       │
│ shift          │ ENUM             │ MORNING, AFTERNOON, NIGHT │
│ is_active      │ BOOLEAN          │ default TRUE              │
│ joined_at      │ DATE             │                           │
└────────────────┴──────────────────┴───────────────────────────┘
```

### 5.5 Patients

```
┌───────────────────────────────────────────────────────────────┐
│                         patients                              │
├────────────────┬──────────────────┬───────────────────────────┤
│ id             │ INTEGER          │ PK                        │
│ user_id        │ INTEGER          │ FK → users.id, UNIQUE     │
│ patient_uid    │ VARCHAR          │ UNIQUE, generated (P-XXXX)│
│ dob            │ DATE             │ NOT NULL                  │
│ gender         │ ENUM             │ MALE, FEMALE, OTHER       │
│ blood_group    │ ENUM             │ A+,A-,B+,B-,AB+,AB-,O+,O- │
│ address        │ VARCHAR          │ nullable                  │
│ city           │ VARCHAR          │ nullable                  │
│ emergency_name │ VARCHAR          │ next-of-kin name          │
│ emergency_phone│ VARCHAR          │ next-of-kin phone         │
│ allergies      │ TEXT             │ nullable, freetext        │
│ chronic_cond.  │ TEXT             │ nullable, freetext        │
│ registered_at  │ TIMESTAMPTZ      │ default NOW()             │
│ registered_by  │ INTEGER          │ FK → users.id (staff)     │
└────────────────┴──────────────────┴───────────────────────────┘
```

### 5.6 Beds

```
┌───────────────────────────────────────────────────────────────┐
│                           beds                                │
├────────────────┬──────────────────┬───────────────────────────┤
│ id             │ INTEGER          │ PK                        │
│ ward_id        │ INTEGER          │ FK → wards.id             │
│ bed_number     │ VARCHAR          │ unique within ward        │
│ bed_type       │ ENUM             │ STANDARD, ICU, PREMIUM,   │
│                │                  │ ISOLATION                 │
│ status         │ ENUM             │ AVAILABLE, OCCUPIED,      │
│                │                  │ MAINTENANCE, RESERVED     │
│ is_active      │ BOOLEAN          │ default TRUE              │
│ created_at     │ TIMESTAMPTZ      │                           │
│ updated_at     │ TIMESTAMPTZ      │                           │
└────────────────┴──────────────────┴───────────────────────────┘

Bed status transitions:
  AVAILABLE  →  RESERVED   (on appointment/pre-admission)
  RESERVED   →  OCCUPIED   (on admission)
  OCCUPIED   →  AVAILABLE  (on discharge)
  AVAILABLE  →  MAINTENANCE
  MAINTENANCE→  AVAILABLE
```

### 5.7 Appointments

```
┌───────────────────────────────────────────────────────────────┐
│                       appointments                            │
├────────────────┬──────────────────┬───────────────────────────┤
│ id             │ INTEGER          │ PK                        │
│ patient_id     │ INTEGER          │ FK → patients.id          │
│ doctor_id      │ INTEGER          │ FK → doctors.id           │
│ hospital_id    │ INTEGER          │ FK → hospitals.id         │
│ scheduled_at   │ TIMESTAMPTZ      │ NOT NULL                  │
│ slot_end_at    │ TIMESTAMPTZ      │ computed from duration    │
│ type           │ ENUM             │ OUTPATIENT, FOLLOW_UP,    │
│                │                  │ EMERGENCY, TELECONSULT    │
│ status         │ ENUM             │ PENDING, CONFIRMED,       │
│                │                  │ CHECKED_IN, IN_PROGRESS,  │
│                │                  │ COMPLETED, CANCELLED,     │
│                │                  │ NO_SHOW                   │
│ reason         │ TEXT             │ chief complaint           │
│ notes          │ TEXT             │ doctor notes post-consult │
│ booked_by      │ INTEGER          │ FK → users.id             │
│ created_at     │ TIMESTAMPTZ      │                           │
│ updated_at     │ TIMESTAMPTZ      │                           │
└────────────────┴──────────────────┴───────────────────────────┘
```

### 5.8 Admissions

```
┌───────────────────────────────────────────────────────────────┐
│                        admissions                             │
├────────────────┬──────────────────┬───────────────────────────┤
│ id             │ INTEGER          │ PK                        │
│ patient_id     │ INTEGER          │ FK → patients.id          │
│ hospital_id    │ INTEGER          │ FK → hospitals.id         │
│ bed_id         │ INTEGER          │ FK → beds.id              │
│ doctor_id      │ INTEGER          │ FK → doctors.id           │
│ appointment_id │ INTEGER          │ FK → appointments.id      │
│ admitted_at    │ TIMESTAMPTZ      │ NOT NULL                  │
│ discharged_at  │ TIMESTAMPTZ      │ nullable                  │
│ status         │ ENUM             │ ADMITTED, DISCHARGED,     │
│                │                  │ TRANSFERRED               │
│ diagnosis      │ TEXT             │ final diagnosis           │
│ discharge_notes│ TEXT             │ nullable                  │
│ admitted_by    │ INTEGER          │ FK → users.id (staff)     │
│ discharged_by  │ INTEGER          │ FK → users.id (staff)     │
└────────────────┴──────────────────┴───────────────────────────┘
```

### 5.9 Medical Tests (Checkings)

```
┌───────────────────────────────────────────────────────────────┐
│                       test_catalog                            │
├────────────────┬──────────────────┬───────────────────────────┤
│ id             │ INTEGER          │ PK                        │
│ hospital_id    │ INTEGER          │ FK → hospitals.id         │
│ name           │ VARCHAR          │ e.g. "CBC", "X-Ray Chest" │
│ category       │ ENUM             │ LAB, RADIOLOGY, ECG,      │
│                │                  │ PATHOLOGY, MICROBIOLOGY   │
│ normal_range   │ VARCHAR          │ nullable, e.g. "4-11 g/dL"│
│ unit           │ VARCHAR          │ nullable                  │
│ price          │ NUMERIC(10,2)    │                           │
│ is_active      │ BOOLEAN          │ default TRUE              │
└────────────────┴──────────────────┴───────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│                       medical_tests                           │
├────────────────┬──────────────────┬───────────────────────────┤
│ id             │ INTEGER          │ PK                        │
│ patient_id     │ INTEGER          │ FK → patients.id          │
│ appointment_id │ INTEGER          │ FK → appointments.id      │
│ admission_id   │ INTEGER          │ FK → admissions.id        │
│ catalog_id     │ INTEGER          │ FK → test_catalog.id      │
│ ordered_by     │ INTEGER          │ FK → doctors.id           │
│ ordered_at     │ TIMESTAMPTZ      │ default NOW()             │
│ conducted_by   │ INTEGER          │ FK → staff.id (lab tech)  │
│ conducted_at   │ TIMESTAMPTZ      │ nullable                  │
│ result_value   │ TEXT             │ nullable                  │
│ result_notes   │ TEXT             │ nullable                  │
│ is_abnormal    │ BOOLEAN          │ nullable                  │
│ status         │ ENUM             │ ORDERED, SAMPLE_COLLECTED,│
│                │                  │ IN_PROGRESS, COMPLETED,   │
│                │                  │ CANCELLED                 │
│ result_at      │ TIMESTAMPTZ      │ nullable                  │
└────────────────┴──────────────────┴───────────────────────────┘
```

### 5.10 Prescriptions & Medicines

```
┌───────────────────────────────────────────────────────────────┐
│                        medicines                              │
├────────────────┬──────────────────┬───────────────────────────┤
│ id             │ INTEGER          │ PK                        │
│ hospital_id    │ INTEGER          │ FK → hospitals.id         │
│ name           │ VARCHAR          │ generic name              │
│ brand_name     │ VARCHAR          │ nullable                  │
│ category       │ ENUM             │ ANTIBIOTIC, ANALGESIC,    │
│                │                  │ ANTIVIRAL, ANTIFUNGAL,    │
│                │                  │ VITAMIN, OTHER            │
│ form           │ ENUM             │ TABLET, CAPSULE, SYRUP,   │
│                │                  │ INJECTION, OINTMENT       │
│ unit           │ VARCHAR          │ mg, ml, IU                │
│ stock_qty      │ INTEGER          │ current stock             │
│ min_stock_qty  │ INTEGER          │ reorder trigger           │
│ price_per_unit │ NUMERIC(10,2)    │                           │
│ expiry_date    │ DATE             │ nullable                  │
│ is_active      │ BOOLEAN          │ default TRUE              │
└────────────────┴──────────────────┴───────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│                      prescriptions                            │
├────────────────┬──────────────────┬───────────────────────────┤
│ id             │ INTEGER          │ PK                        │
│ patient_id     │ INTEGER          │ FK → patients.id          │
│ doctor_id      │ INTEGER          │ FK → doctors.id           │
│ appointment_id │ INTEGER          │ FK → appointments.id      │
│ notes          │ TEXT             │ doctor notes              │
│ status         │ ENUM             │ ACTIVE, DISPENSED,        │
│                │                  │ PARTIALLY_DISPENSED,      │
│                │                  │ CANCELLED                 │
│ created_at     │ TIMESTAMPTZ      │                           │
└────────────────┴──────────────────┴───────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│                   prescription_items                          │
├────────────────┬──────────────────┬───────────────────────────┤
│ id             │ INTEGER          │ PK                        │
│ prescription_id│ INTEGER          │ FK → prescriptions.id     │
│ medicine_id    │ INTEGER          │ FK → medicines.id         │
│ dosage         │ VARCHAR          │ e.g. "500mg"              │
│ frequency      │ VARCHAR          │ e.g. "3 times/day"        │
│ duration_days  │ INTEGER          │                           │
│ quantity       │ INTEGER          │ total units to dispense   │
│ instructions   │ TEXT             │ e.g. "after meals"        │
│ is_dispensed   │ BOOLEAN          │ default FALSE             │
│ dispensed_at   │ TIMESTAMPTZ      │ nullable                  │
│ dispensed_by   │ INTEGER          │ FK → staff.id (pharmacist)│
└────────────────┴──────────────────┴───────────────────────────┘
```

### 5.12 Billing & Payments

```
┌──────────────────────────────────────────────────────────────────────┐
│                             bills                                    │
├────────────────┬──────────────────┬──────────────────────────────────┤
│ id             │ INTEGER          │ PK                               │
│ bill_number    │ VARCHAR          │ UNIQUE, generated (B-XXXX)       │
│ patient_id     │ INTEGER          │ FK → patients.id                 │
│ hospital_id    │ INTEGER          │ FK → hospitals.id                │
│ appointment_id │ INTEGER          │ FK → appointments.id, nullable   │
│ admission_id   │ INTEGER          │ FK → admissions.id, nullable     │
│ bill_type      │ ENUM             │ OPD, INPATIENT, LAB, PHARMACY    │
│ status         │ ENUM             │ DRAFT, PENDING,                  │
│                │                  │ PARTIALLY_PAID, PAID,            │
│                │                  │ OVERDUE, WAIVED                  │
│ subtotal       │ NUMERIC(12,2)    │ sum of line items                │
│ discount       │ NUMERIC(12,2)    │ default 0                        │
│ discount_reason│ VARCHAR          │ nullable                         │
│ tax            │ NUMERIC(12,2)    │ GST / applicable tax             │
│ total          │ NUMERIC(12,2)    │ subtotal − discount + tax        │
│ amount_paid    │ NUMERIC(12,2)    │ default 0                        │
│ balance_due    │ NUMERIC(12,2)    │ computed: total − amount_paid    │
│ due_date       │ DATE             │ nullable, triggers OVERDUE       │
│ created_by     │ INTEGER          │ FK → users.id                    │
│ created_at     │ TIMESTAMPTZ      │ default NOW()                    │
│ updated_at     │ TIMESTAMPTZ      │ default NOW()                    │
└────────────────┴──────────────────┴──────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                           bill_line_items                            │
├────────────────┬──────────────────┬──────────────────────────────────┤
│ id             │ INTEGER          │ PK                               │
│ bill_id        │ INTEGER          │ FK → bills.id                    │
│ description    │ VARCHAR          │ NOT NULL  e.g. "CBC Blood Test"  │
│ category       │ ENUM             │ CONSULTATION, LAB_TEST,          │
│                │                  │ MEDICINE, ROOM_CHARGE,           │
│                │                  │ PROCEDURE, OTHER                 │
│ quantity       │ INTEGER          │ default 1                        │
│ unit_price     │ NUMERIC(10,2)    │ NOT NULL                         │
│ total_price    │ NUMERIC(10,2)    │ quantity × unit_price            │
│ reference_id   │ INTEGER          │ nullable (appointment/test/rx id)│
│ reference_type │ VARCHAR          │ nullable ("appointment","test"…) │
└────────────────┴──────────────────┴──────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                            payments                                  │
├────────────────┬──────────────────┬──────────────────────────────────┤
│ id             │ INTEGER          │ PK                               │
│ receipt_number │ VARCHAR          │ UNIQUE, generated (REC-XXXX)     │
│ bill_id        │ INTEGER          │ FK → bills.id                    │
│ patient_id     │ INTEGER          │ FK → patients.id                 │
│ amount         │ NUMERIC(12,2)    │ NOT NULL  (partial allowed)      │
│ method         │ ENUM             │ CASH, CARD, UPI,                 │
│                │                  │ NET_BANKING, INSURANCE           │
│ status         │ ENUM             │ SUCCESS, PENDING, FAILED,        │
│                │                  │ REFUNDED                         │
│ transaction_ref│ VARCHAR          │ nullable (UPI txn ID, card auth) │
│ gateway_ref    │ VARCHAR          │ nullable (payment gateway ref)   │
│ notes          │ TEXT             │ nullable                         │
│ collected_by   │ INTEGER          │ FK → users.id (staff/receptionist│
│ paid_at        │ TIMESTAMPTZ      │ default NOW()                    │
└────────────────┴──────────────────┴──────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                         insurance_claims                             │
├────────────────┬──────────────────┬──────────────────────────────────┤
│ id             │ INTEGER          │ PK                               │
│ bill_id        │ INTEGER          │ FK → bills.id, UNIQUE            │
│ patient_id     │ INTEGER          │ FK → patients.id                 │
│ provider_name  │ VARCHAR          │ NOT NULL                         │
│ policy_number  │ VARCHAR          │ NOT NULL                         │
│ member_id      │ VARCHAR          │ NOT NULL                         │
│ pre_auth_code  │ VARCHAR          │ nullable                         │
│ claimed_amount │ NUMERIC(12,2)    │ NOT NULL                         │
│ approved_amount│ NUMERIC(12,2)    │ nullable (set on approval)       │
│ patient_copay  │ NUMERIC(12,2)    │ NOT NULL                         │
│ status         │ ENUM             │ SUBMITTED, APPROVED,             │
│                │                  │ REJECTED, PARTIALLY_APPROVED     │
│ rejection_reason│ TEXT            │ nullable                         │
│ submitted_at   │ TIMESTAMPTZ      │ default NOW()                    │
│ resolved_at    │ TIMESTAMPTZ      │ nullable                         │
└────────────────┴──────────────────┴──────────────────────────────────┘

Bill status transitions:
  DRAFT          →  PENDING           (on bill finalisation)
  PENDING        →  PARTIALLY_PAID    (on partial payment)
  PENDING        →  PAID              (on full payment)
  PARTIALLY_PAID →  PAID              (on remaining balance paid)
  PENDING        →  OVERDUE           (due_date passed, unpaid)
  OVERDUE        →  PAID              (late payment accepted)
  PENDING        →  WAIVED            (admin write-off)

Payment status transitions:
  PENDING   →  SUCCESS   (confirmed by gateway / staff)
  PENDING   →  FAILED    (gateway rejection)
  SUCCESS   →  REFUNDED  (admin-initiated refund)

Insurance claim status transitions:
  SUBMITTED  →  APPROVED / PARTIALLY_APPROVED / REJECTED
```

---

## 6. API Endpoints

### Auth
| Method | Path                  | Description              |
|--------|-----------------------|--------------------------|
| POST   | /api/v1/auth/login    | Login → JWT token        |
| POST   | /api/v1/auth/logout   | Invalidate token         |
| POST   | /api/v1/auth/refresh  | Refresh access token     |

### Hospitals & Wards
| Method | Path                           | Auth       | Description           |
|--------|--------------------------------|------------|-----------------------|
| GET    | /hospitals                     | active     | List hospitals        |
| POST   | /hospitals                     | superuser  | Create hospital       |
| GET    | /hospitals/{id}                | active     | Get hospital          |
| PATCH  | /hospitals/{id}                | superuser  | Update hospital       |
| DELETE | /hospitals/{id}                | superuser  | Delete hospital       |
| GET    | /hospitals/{id}/wards          | active     | List wards            |
| POST   | /hospitals/{id}/wards          | superuser  | Create ward           |
| GET    | /wards/{id}/beds               | active     | List beds in ward     |
| GET    | /wards/{id}/beds/available     | staff      | Available beds only   |

### Doctors
| Method | Path                                    | Auth       | Description           |
|--------|-----------------------------------------|------------|-----------------------|
| GET    | /doctors                                | active     | List doctors          |
| POST   | /doctors                                | admin      | Register doctor       |
| GET    | /doctors/{id}                           | active     | Get doctor profile    |
| PATCH  | /doctors/{id}                           | admin      | Update doctor         |
| GET    | /doctors/{id}/availability              | active     | Get schedule          |
| POST   | /doctors/{id}/availability              | admin      | Set schedule          |
| GET    | /doctors/{id}/slots?date=YYYY-MM-DD     | active     | Available slots       |
| GET    | /doctors/{id}/appointments              | doctor     | Doctor's appointments |

### Staff
| Method | Path              | Auth       | Description       |
|--------|-------------------|------------|-------------------|
| GET    | /staff            | admin      | List staff        |
| POST   | /staff            | admin      | Register staff    |
| GET    | /staff/{id}       | admin      | Get staff profile |
| PATCH  | /staff/{id}       | admin      | Update staff      |

### Patients
| Method | Path                          | Auth          | Description            |
|--------|-------------------------------|---------------|------------------------|
| GET    | /patients                     | staff/doctor  | List patients          |
| POST   | /patients                     | staff         | Register patient       |
| GET    | /patients/{id}                | staff/doctor  | Get patient profile    |
| PATCH  | /patients/{id}                | staff         | Update patient info    |
| GET    | /patients/{id}/appointments   | staff/doctor  | Patient's appointments |
| GET    | /patients/{id}/admissions     | staff/doctor  | Admission history      |
| GET    | /patients/{id}/tests          | staff/doctor  | All tests              |
| GET    | /patients/{id}/prescriptions  | staff/doctor  | All prescriptions      |

### Appointments
| Method | Path                          | Auth          | Description              |
|--------|-------------------------------|---------------|--------------------------|
| GET    | /appointments                 | staff/doctor  | List appointments        |
| POST   | /appointments                 | staff/patient | Book appointment         |
| GET    | /appointments/{id}            | active        | Get appointment detail   |
| PATCH  | /appointments/{id}            | staff/doctor  | Update appointment       |
| POST   | /appointments/{id}/check-in   | staff         | Patient checked in       |
| POST   | /appointments/{id}/complete   | doctor        | Mark completed           |
| POST   | /appointments/{id}/cancel     | staff/patient | Cancel appointment       |

### Beds & Admissions
| Method | Path                           | Auth   | Description              |
|--------|--------------------------------|--------|--------------------------|
| GET    | /beds                          | staff  | List all beds            |
| POST   | /beds                          | admin  | Add bed                  |
| PATCH  | /beds/{id}                     | admin  | Update bed               |
| POST   | /admissions                    | staff  | Admit patient            |
| GET    | /admissions/{id}               | staff  | Get admission            |
| POST   | /admissions/{id}/discharge     | doctor | Discharge patient        |
| PATCH  | /admissions/{id}               | staff  | Update admission notes   |

### Medical Tests
| Method | Path                           | Auth        | Description            |
|--------|--------------------------------|-------------|------------------------|
| GET    | /test-catalog                  | active      | List available tests   |
| POST   | /test-catalog                  | admin       | Add test to catalog    |
| POST   | /tests                         | doctor      | Order a test           |
| GET    | /tests/{id}                    | staff/doctor| Get test detail        |
| POST   | /tests/{id}/collect-sample     | lab staff   | Mark sample collected  |
| POST   | /tests/{id}/result             | lab staff   | Upload result          |
| GET    | /patients/{id}/tests           | staff/doctor| All patient tests      |

### Medicines & Pharmacy
| Method | Path                          | Auth        | Description                  |
|--------|-------------------------------|-------------|------------------------------|
| GET    | /medicines                    | active      | List medicines               |
| POST   | /medicines                    | admin       | Add medicine                 |
| PATCH  | /medicines/{id}               | admin       | Update/restock medicine      |
| GET    | /medicines/low-stock          | admin       | Low-stock alerts             |
| POST   | /prescriptions                | doctor      | Create prescription          |
| GET    | /prescriptions/{id}           | active      | Get prescription             |
| POST   | /prescriptions/{id}/dispense  | pharmacist  | Dispense medicine            |

### Billing
| Method | Path                              | Auth           | Description                        |
|--------|-----------------------------------|----------------|------------------------------------|
| GET    | /bills                            | staff/admin    | List bills (filter by status/type) |
| POST   | /bills                            | staff          | Create bill manually               |
| GET    | /bills/{id}                       | staff/patient  | Get bill detail with line items    |
| PATCH  | /bills/{id}                       | staff          | Update discount / due date         |
| POST   | /bills/{id}/finalise              | staff          | Move DRAFT → PENDING               |
| POST   | /bills/{id}/waive                 | admin          | Write off bill (→ WAIVED)          |
| GET    | /bills/{id}/line-items            | staff/patient  | List line items for a bill         |
| POST   | /bills/{id}/line-items            | staff          | Add line item to bill              |
| DELETE | /bills/{id}/line-items/{item_id}  | staff          | Remove line item (DRAFT only)      |
| GET    | /patients/{id}/bills              | staff/patient  | All bills for a patient            |
| POST   | /appointments/{id}/generate-bill  | staff          | Auto-generate OPD bill             |
| POST   | /admissions/{id}/generate-bill    | staff          | Auto-generate inpatient bill       |

### Payments
| Method | Path                          | Auth           | Description                        |
|--------|-------------------------------|----------------|------------------------------------|
| GET    | /payments                     | staff/admin    | List all payments                  |
| POST   | /payments                     | staff          | Record a payment against a bill    |
| GET    | /payments/{id}                | staff/patient  | Get payment / receipt detail       |
| POST   | /payments/{id}/refund         | admin          | Refund a successful payment        |
| GET    | /payments/my                  | patient        | Patient's own payment history      |

### Insurance Claims
| Method | Path                          | Auth        | Description                        |
|--------|-------------------------------|-------------|------------------------------------|
| POST   | /insurance-claims             | staff       | Submit insurance claim for a bill  |
| GET    | /insurance-claims/{id}        | staff/admin | Get claim detail                   |
| PATCH  | /insurance-claims/{id}        | admin       | Update claim status / amounts      |

---

## 7. Key Flow Diagrams

### 7.1 Patient Registration

```
Receptionist / Staff
        │
        │  POST /api/v1/patients
        │  { full_name, email, dob, gender, blood_group,
        │    address, emergency_name, emergency_phone }
        ▼
PatientService.register()
        │
        ├─ Create user account (email + temp password)
        │        │
        │        └─ UserRepository.create({ email, hashed_pw })
        │
        ├─ Generate patient_uid  → "P-00042"
        │
        ├─ PatientRepository.create({
        │     user_id, patient_uid, dob, gender,
        │     blood_group, address, emergency_* })
        │
        └─ Return PatientResponse  ←  HTTP 201

Patient receives login credentials via email (optional step)
```

### 7.2 Book an Appointment

```
Patient / Receptionist
        │
        │  GET /doctors/{id}/slots?date=2026-05-26
        ▼
AppointmentService.get_available_slots(doctor_id, date)
        │
        ├─ Load DoctorAvailability for that day_of_week
        ├─ Generate all slots: start_time → end_time by slot_duration
        ├─ Subtract slots already booked in appointments table
        └─ Return list of free time slots  ←  HTTP 200

        │
        │  POST /appointments
        │  { patient_id, doctor_id, hospital_id,
        │    scheduled_at: "2026-05-26T10:00:00Z",
        │    type: "OUTPATIENT", reason: "Fever" }
        ▼
AppointmentService.book()
        │
        ├─ Validate doctor is active & works at that hospital
        ├─ Validate slot is within doctor's availability window
        ├─ Check no overlapping confirmed appointment for doctor
        │       └─ Overlap exists → HTTP 409 "Slot not available"
        ├─ Check no overlapping appointment for patient
        │
        ├─ AppointmentRepository.create({
        │     ..., status: PENDING, booked_by: current_user.id })
        │
        └─ Return AppointmentResponse  ←  HTTP 201
```

### 7.3 Appointment → Consultation → Prescription

```
Patient arrives at hospital
        │
        │  POST /appointments/{id}/check-in   (Receptionist)
        ▼
  status: PENDING → CHECKED_IN

        │
        │  Doctor calls patient
        ▼
  status: CHECKED_IN → IN_PROGRESS

        │
  Doctor examines patient, may order tests:
        │
        │  POST /tests
        │  { patient_id, appointment_id, catalog_id, ordered_by }
        ▼
  MedicalTestService.order()
        │
        ├─ Validate catalog_id exists and is active
        └─ TestRepository.create({ ..., status: ORDERED })
                ← HTTP 201

        │
  Doctor creates prescription:
        │
        │  POST /prescriptions
        │  { patient_id, doctor_id, appointment_id,
        │    items: [
        │      { medicine_id, dosage, frequency,
        │        duration_days, instructions }
        │    ] }
        ▼
  PrescriptionService.create()
        │
        ├─ Validate all medicine_ids exist and are active
        ├─ PrescriptionRepository.create()
        ├─ PrescriptionItemRepository.bulk_create(items)
        └─ Return PrescriptionResponse  ←  HTTP 201

        │
        │  POST /appointments/{id}/complete   (Doctor)
        ▼
  status: IN_PROGRESS → COMPLETED
  appointment.notes = "diagnosis / consultation notes"
```

### 7.4 Admit Patient & Bed Allocation

```
Doctor / Staff
        │
        │  GET /wards/{ward_id}/beds/available
        ▼
BedService.get_available(ward_id)
        │
        └─ SELECT beds WHERE status = AVAILABLE AND ward_id = ?
           ←  HTTP 200  list of available beds

        │
        │  POST /admissions
        │  { patient_id, hospital_id, bed_id,
        │    doctor_id, appointment_id, diagnosis_preliminary }
        ▼
AdmissionService.admit()
        │
        ├─ Validate patient exists
        ├─ Validate bed status == AVAILABLE
        │       └─ Not available → HTTP 409 "Bed is not available"
        ├─ Validate no active admission exists for patient
        │
        ├─ BEGIN TRANSACTION
        │   ├─ BedRepository.update(bed_id, status=OCCUPIED)
        │   ├─ AdmissionRepository.create({
        │   │    ..., admitted_at: now(), status: ADMITTED })
        │   └─ COMMIT
        │
        └─ Return AdmissionResponse  ←  HTTP 201
```

### 7.5 Order & Process a Medical Test

```
Doctor orders test (during consultation):
        │
        │  POST /tests
        │  { patient_id, appointment_id, catalog_id }
        ▼
  status: ORDERED

        │
Lab Technician collects sample:
        │
        │  POST /tests/{id}/collect-sample
        ▼
  status: ORDERED → SAMPLE_COLLECTED
  conducted_by = lab_tech_staff_id

        │
Lab processes:
        │
  status: SAMPLE_COLLECTED → IN_PROGRESS

        │
Result uploaded:
        │
        │  POST /tests/{id}/result
        │  { result_value, result_notes, is_abnormal }
        ▼
  status: IN_PROGRESS → COMPLETED
  result_at = now()

        │
  If is_abnormal == true → alert doctor (notification / flag)
        │
Doctor reviews via:
        │
        │  GET /patients/{id}/tests
        └─  GET /tests/{id}
```

### 7.6 Medicine Dispensing

```
Patient / Nurse brings prescription to pharmacy:
        │
        │  GET /prescriptions/{id}
        ▼
  Pharmacist sees items, quantities, instructions

        │
        │  POST /prescriptions/{id}/dispense
        │  { items: [ { prescription_item_id, quantity_dispensed } ] }
        ▼
PharmacyService.dispense()
        │
        ├─ Validate prescription status ≠ CANCELLED
        ├─ For each item:
        │   ├─ Validate medicine.stock_qty >= quantity_dispensed
        │   │       └─ Insufficient stock → HTTP 400
        │   ├─ MedicineRepository.decrement_stock(medicine_id, qty)
        │   └─ PrescriptionItem.is_dispensed = True
        │       dispensed_at = now(), dispensed_by = pharmacist_id
        │
        ├─ If ALL items dispensed → prescription.status = DISPENSED
        ├─ If SOME items dispensed → PARTIALLY_DISPENSED
        │
        └─ Return updated PrescriptionResponse  ←  HTTP 200

Stock alert trigger:
  If medicine.stock_qty < medicine.min_stock_qty
      → flag in GET /medicines/low-stock
```

### 7.7 Discharge Patient

```
Doctor / Staff
        │
        │  POST /admissions/{id}/discharge
        │  { diagnosis, discharge_notes }
        ▼
AdmissionService.discharge()
        │
        ├─ Validate admission.status == ADMITTED
        │       └─ Not active → HTTP 400 "Patient not currently admitted"
        │
        ├─ Check pending tests (status != COMPLETED)
        │       → warn (do not block)
        │
        ├─ Check prescriptions status ACTIVE / PARTIALLY_DISPENSED
        │       → warn (do not block)
        │
        ├─ BEGIN TRANSACTION
        │   ├─ AdmissionRepository.update({
        │   │    status: DISCHARGED,
        │   │    discharged_at: now(),
        │   │    discharged_by: current_user.id,
        │   │    diagnosis, discharge_notes })
        │   │
        │   └─ BedRepository.update(bed_id, status=AVAILABLE)
        └─ COMMIT
        │
        └─ Return AdmissionResponse  ←  HTTP 200
```

### 7.8 OPD Billing & Payment

```
Appointment completes  (status → COMPLETED)
        │
        │  POST /appointments/{id}/generate-bill   (Staff / auto-trigger)
        ▼
BillingService.generate_opd_bill(appointment_id)
        │
        ├─ Pull consultation_fee from Doctor record
        │         → BillLineItem: CONSULTATION
        │
        ├─ Pull all medical_tests linked to appointment
        │         → BillLineItem: LAB_TEST  (price from test_catalog)
        │
        ├─ Pull all prescription_items dispensed
        │         → BillLineItem: MEDICINE  (price_per_unit × quantity)
        │
        ├─ Calculate: subtotal, tax (5% on services), discount (if any)
        │
        ├─ BillRepository.create({ ..., status: PENDING, bill_type: OPD })
        └─ Return Bill  ←  HTTP 201

        │
Staff / Receptionist records payment:
        │
        │  POST /payments
        │  { bill_id, amount, method: "UPI",
        │    transaction_ref: "TXN-XXXXXXXX" }
        ▼
PaymentService.record()
        │
        ├─ Validate bill exists and status ≠ WAIVED
        ├─ Validate amount > 0 and ≤ bill.balance_due
        │
        ├─ PaymentRepository.create({
        │     receipt_number: "REC-XXXX",
        │     status: SUCCESS, paid_at: now(),
        │     collected_by: current_user.id })
        │
        ├─ BillRepository.increment_amount_paid(bill_id, amount)
        │
        ├─ If bill.amount_paid == bill.total → bill.status = PAID
        │   Else                             → bill.status = PARTIALLY_PAID
        │
        └─ Return PaymentResponse  ←  HTTP 201
```

### 7.9 Inpatient Final Bill & Discharge Payment

```
Staff initiates discharge:  POST /admissions/{id}/discharge
        │
        │  POST /admissions/{id}/generate-bill   (before or at discharge)
        ▼
BillingService.generate_inpatient_bill(admission_id)
        │
        ├─ Room charges:
        │     nights = ceil((discharged_at - admitted_at) / 86400)
        │     rate   = RATE_MAP[bed.bed_type]   (STANDARD/ICU/PREMIUM)
        │     → BillLineItem: ROOM_CHARGE
        │
        ├─ Doctor visits during admission
        │     → BillLineItem: CONSULTATION  per appointment
        │
        ├─ Lab tests ordered during admission
        │     → BillLineItem: LAB_TEST
        │
        ├─ Medicines dispensed during admission
        │     → BillLineItem: MEDICINE
        │
        ├─ Any additional procedures added by staff
        │     → BillLineItem: PROCEDURE
        │
        ├─ Compute subtotal / discount / tax / total
        └─ Bill created, status: PENDING

        │
Patient / family submits insurance claim (optional):
        │
        │  POST /insurance-claims
        │  { bill_id, provider_name, policy_number,
        │    member_id, pre_auth_code, claimed_amount }
        ▼
InsuranceClaimService.submit()
        │
        ├─ InsuranceClaimRepository.create({ status: SUBMITTED })
        └─ Return InsuranceClaim  ←  HTTP 201

        │
Admin updates claim outcome:
        │
        │  PATCH /insurance-claims/{id}
        │  { status: APPROVED, approved_amount: 5000,
        │    patient_copay: 2100 }
        ▼
        ├─ Update claim record
        ├─ Add BillLineItem: INSURANCE_DEDUCTION (− approved_amount)
        └─ Recalculate bill.balance_due  →  patient_copay

        │
Patient pays co-pay:
        │
        │  POST /payments
        │  { bill_id, amount: 2100, method: "CASH" }
        ▼
        ├─ PaymentService.record()  (same as 7.8)
        ├─ Bill status → PAID
        └─ Discharge proceeds (bed freed, summary available)
```

---

## 8. Status State Machines

### Appointment Status

```
                    ┌─────────┐
         book()     │ PENDING │
         ──────────►│         │
                    └────┬────┘
                         │ confirm / auto
                         ▼
                   ┌─────────────┐
                   │  CONFIRMED  │
                   └──────┬──────┘
                          │ patient arrives
                          ▼
                   ┌─────────────┐
                   │ CHECKED_IN  │
                   └──────┬──────┘
                          │ doctor calls
                          ▼
                   ┌─────────────┐
                   │ IN_PROGRESS │
                   └──────┬──────┘
                          │ doctor marks done
                          ▼
                   ┌─────────────┐
                   │  COMPLETED  │
                   └─────────────┘

  PENDING / CONFIRMED / CHECKED_IN ──cancel()──► CANCELLED
  PENDING / CONFIRMED ──────────────no show────► NO_SHOW
```

### Bed Status

```
  AVAILABLE ──assign──► OCCUPIED ──discharge──► AVAILABLE
  AVAILABLE ──maint───► MAINTENANCE ──fix──────► AVAILABLE
  AVAILABLE ──reserve─► RESERVED ──admit──────► OCCUPIED
```

### Medical Test Status

```
  ORDERED ──collect──► SAMPLE_COLLECTED ──process──► IN_PROGRESS ──result──► COMPLETED
  ORDERED / SAMPLE_COLLECTED ──cancel──► CANCELLED
```

### Prescription Status

```
  ACTIVE ──all dispensed───────► DISPENSED
  ACTIVE ──some dispensed──────► PARTIALLY_DISPENSED
  ACTIVE / PARTIALLY_DISPENSED ► DISPENSED  (on final dispense)
  ACTIVE ──doctor cancel───────► CANCELLED
```

### Bill Status

```
                ┌───────┐
   create()     │ DRAFT │
   ────────────►│       │
                └───┬───┘
                    │ finalise()
                    ▼
               ┌─────────┐
               │ PENDING │◄─────────────────── (re-opened on refund)
               └────┬────┘
                    │
        ┌───────────┼───────────────┐
        │           │               │
   partial       full pay       due_date
   payment       payment         passes
        │           │               │
        ▼           ▼               ▼
  ┌──────────┐  ┌──────┐      ┌─────────┐
  │PARTIALLY │  │ PAID │      │ OVERDUE │
  │  _PAID   │  └──────┘      └────┬────┘
  └────┬─────┘                     │ late payment
       │ final payment             ▼
       └──────────────────────► PAID

  PENDING / PARTIALLY_PAID / OVERDUE ──admin──► WAIVED
```

### Payment Status

```
  PENDING ──confirmed──► SUCCESS ──admin refund──► REFUNDED
  PENDING ──rejected───► FAILED
```

### Insurance Claim Status

```
  SUBMITTED ──approved────────────► APPROVED
  SUBMITTED ──partial approval────► PARTIALLY_APPROVED
  SUBMITTED ──rejected────────────► REJECTED
```

---

## 9. Role & Permission Matrix

```
Endpoint / Action              │ Admin │ Doctor │ Nurse/Staff │ Receptionist │ Patient │
───────────────────────────────┼───────┼────────┼─────────────┼──────────────┼─────────┤
Manage hospitals/wards/beds    │   ✓   │        │             │              │         │
Register doctor / staff        │   ✓   │        │             │              │         │
View doctors & slots           │   ✓   │   ✓    │      ✓      │      ✓       │    ✓    │
Register patient               │   ✓   │        │      ✓      │      ✓       │         │
View any patient record        │   ✓   │   ✓*   │      ✓      │      ✓       │         │
View own patient record        │       │        │             │              │    ✓    │
Book appointment               │   ✓   │        │      ✓      │      ✓       │    ✓    │
Check-in patient               │   ✓   │        │      ✓      │      ✓       │         │
Start / complete consultation  │       │   ✓    │             │              │         │
Admit / discharge patient      │   ✓   │   ✓    │      ✓      │              │         │
Order medical test             │       │   ✓    │             │              │         │
Record test results            │   ✓   │        │  ✓(lab tech)│              │         │
Create prescription            │       │   ✓    │             │              │         │
Dispense medicine              │   ✓   │        │ ✓(pharmacist│              │         │
Manage medicine inventory      │   ✓   │        │             │              │         │
Low stock alerts               │   ✓   │        │ ✓(pharmacist│              │         │
Generate bill (OPD/Inpatient)  │   ✓   │        │      ✓      │      ✓       │         │
View any bill                  │   ✓   │        │      ✓      │      ✓       │         │
View own bills                 │       │        │             │              │    ✓    │
Record payment (cash/card/UPI) │   ✓   │        │      ✓      │      ✓       │         │
Pay own bill (online)          │       │        │             │              │    ✓    │
Apply discount / waive bill    │   ✓   │        │             │              │         │
Submit insurance claim         │   ✓   │        │      ✓      │      ✓       │         │
Approve / reject insurance     │   ✓   │        │             │              │         │
Refund payment                 │   ✓   │        │             │              │         │
View payment history (all)     │   ✓   │        │      ✓      │      ✓       │         │
View own payment history       │       │        │             │              │    ✓    │
Export payment report          │   ✓   │        │             │              │         │

* Doctor can view records only for their own patients
```

---

## 10. Error Catalogue

| Code | Scenario                                   | HTTP  | Detail                                           |
|------|--------------------------------------------|-------|--------------------------------------------------|
| A001 | Missing / expired JWT                      | 401   | "Could not validate credentials"                 |
| A002 | Inactive user account                      | 403   | "Inactive user"                                  |
| A003 | Insufficient role                          | 403   | "The user doesn't have enough privileges"        |
| H001 | Hospital not found                         | 404   | "Hospital not found"                             |
| H002 | Duplicate hospital name                    | 400   | "Hospital with this name already exists"         |
| D001 | Doctor not found                           | 404   | "Doctor not found"                               |
| D002 | Doctor license already registered          | 400   | "License number already exists"                  |
| D003 | No availability schedule for requested day | 404   | "Doctor is not available on this day"            |
| P001 | Patient not found                          | 404   | "Patient not found"                              |
| P002 | Email already registered                   | 400   | "Email already in use"                           |
| AP01 | Appointment slot not available             | 409   | "Slot is not available"                          |
| AP02 | Appointment not found                      | 404   | "Appointment not found"                          |
| AP03 | Invalid status transition                  | 400   | "Cannot transition from X to Y"                  |
| B001 | Bed not available                          | 409   | "Bed is not available"                           |
| B002 | Patient already admitted                   | 409   | "Patient already has an active admission"        |
| B003 | Bed not found                              | 404   | "Bed not found"                                  |
| T001 | Test catalog item not found                | 404   | "Test not found in catalog"                      |
| T002 | Test order not found                       | 404   | "Medical test not found"                         |
| M001 | Medicine not found                         | 404   | "Medicine not found"                             |
| M002 | Insufficient medicine stock                | 400   | "Insufficient stock for medicine {name}"         |
| M003 | Prescription already dispensed             | 400   | "Prescription is already fully dispensed"        |
| BI01 | Bill not found                             | 404   | "Bill not found"                                 |
| BI02 | Bill already paid                          | 400   | "Bill is already fully paid"                     |
| BI03 | Bill is waived — cannot accept payment     | 400   | "Bill has been waived"                           |
| BI04 | Payment amount exceeds balance due         | 400   | "Payment amount exceeds outstanding balance"     |
| BI05 | Bill still in DRAFT — cannot pay           | 400   | "Bill must be finalised before payment"          |
| BI06 | Line item belongs to different bill        | 400   | "Line item does not belong to this bill"         |
| BI07 | Cannot modify line items on non-DRAFT bill | 400   | "Line items can only be edited on DRAFT bills"   |
| PA01 | Payment not found                          | 404   | "Payment not found"                              |
| PA02 | Payment already refunded                   | 400   | "Payment has already been refunded"              |
| PA03 | Only SUCCESS payments can be refunded      | 400   | "Only successful payments can be refunded"       |
| IC01 | Insurance claim not found                  | 404   | "Insurance claim not found"                      |
| IC02 | Bill already has an insurance claim        | 409   | "An insurance claim already exists for this bill"|
| V001 | Request body validation error              | 422   | Pydantic field errors                            |
| S001 | Unhandled server error                     | 500   | "Internal Server Error"                          |

---

## 11. Layer Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│ Layer              │ File Pattern                │ Responsibility     │
├───────────────────────────────────────────────────────────────────────┤
│ Endpoint           │ api/v1/endpoints/*.py       │ HTTP in/out,       │
│                    │                             │ status codes,      │
│                    │                             │ inject deps        │
├───────────────────────────────────────────────────────────────────────┤
│ Service            │ services/*_service.py       │ Business rules,    │
│                    │                             │ cross-entity logic,│
│                    │                             │ raises HTTPExc     │
├───────────────────────────────────────────────────────────────────────┤
│ Repository         │ repositories/*_repository.py│ DB queries,        │
│                    │ repositories/base.py        │ joins, pagination, │
│                    │                             │ transactions       │
├───────────────────────────────────────────────────────────────────────┤
│ Model              │ models/*.py                 │ ORM table mapping, │
│                    │                             │ FK relationships   │
├───────────────────────────────────────────────────────────────────────┤
│ Schema             │ schemas/*.py                │ Pydantic request / │
│                    │                             │ response shapes,   │
│                    │                             │ input validation   │
└───────────────────────────────────────────────────────────────────────┘
```

### Module Dependency Graph

```
endpoints
    └── depends on ──► services
                           └── depends on ──► repositories
                                                  └── depends on ──► models
                                                  └── depends on ──► schemas (write path)
endpoints
    └── returns ─────► schemas (Pydantic serialization)
```

### Alembic Migration Order

When implementing, create migrations in this dependency order to respect FK constraints:

```
1. users
2. hospitals
3. wards            (→ hospitals)
4. beds             (→ wards)
5. doctors          (→ users, hospitals)
6. staff            (→ users, hospitals)
7. doctor_availability (→ doctors)
8. patients         (→ users)
9. appointments     (→ patients, doctors, hospitals)
10. admissions      (→ patients, hospitals, beds, doctors, appointments)
11. test_catalog    (→ hospitals)
12. medical_tests   (→ patients, appointments, admissions, test_catalog, doctors, staff)
13. medicines       (→ hospitals)
14. prescriptions   (→ patients, doctors, appointments)
15. prescription_items (→ prescriptions, medicines)
16. bills           (→ patients, hospitals, appointments, admissions)
17. bill_line_items (→ bills)
18. payments        (→ bills, patients)
19. insurance_claims (→ bills, patients)
```