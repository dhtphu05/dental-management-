# Dental Project

A modular dental clinic management system built with Django 6. The project covers user management, patient records, appointment scheduling, clinical treatment workflows, billing, and a modern Tailwind-based UI.

## Features

- Custom user model with roles:
  - `Admin`
  - `Doctor`
  - `Receptionist`
  - `Patient`
- Full CRUD for:
  - Patients
  - Appointments
  - Services
  - Invoices
- Multi-step booking experience:
  - Progress bar
  - Doctor/day-based time slot availability
  - Mobile-first time slot grid
- Doctor dashboard:
  - Collapsible sidebar
  - Stats cards
  - Modern appointments table
  - Line chart powered by Chart.js
- Interactive odontogram for doctors:
  - 32 teeth displayed in 4 quadrants
  - Tooth status modal
  - Color-coded tooth states
- Automated business rules:
  - Prevents doctor schedule conflicts
  - Auto-creates a default odontogram for new patients
  - Updates tooth status when treatment is completed
  - Auto-generates invoice totals from selected services
- Design system built with Tailwind CSS
- Lucide Icons used across the project UI

## Project Structure

```text
.
├── core/                 # Django settings, urls, wsgi, asgi
├── apps/
│   ├── accounts/         # Users, roles, dashboards
│   ├── patients/         # Patient records
│   ├── scheduling/       # Appointments and booking flow
│   ├── clinical/         # Odontogram, treatment plans, services
│   └── billing/          # Invoices
├── templates/            # HTML templates
├── static/               # Static assets
├── manage.py
└── README.md
```

## Tech Stack

- Python 3.14
- Django 6.0.3
- PostgreSQL
- Tailwind CSS Browser CDN
- Chart.js
- Lucide Icons

## Local Setup

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start PostgreSQL with Docker

This project includes a local PostgreSQL setup via Docker Compose.

```bash
docker compose up -d
```

The default local database settings are stored in `.env.local`:

```bash
POSTGRES_DB=dental_project
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5433
```

Django loads `.env.local` automatically at startup.

### 4. Apply migrations

```bash
python manage.py migrate
```

### 5. Create an admin user

```bash
python manage.py createsuperuser
```

### 6. Seed Vietnamese doctor accounts

```bash
python manage.py seed_vietnamese_doctors
```

Default doctor password:

```text
Dental@123
```

If you want to reset all seeded doctor passwords back to the default:

```bash
python manage.py seed_vietnamese_doctors --reset-passwords
```

### 7. Seed full demo data

```bash
python manage.py seed_demo_data
```

This command creates:

- Admin and receptionist accounts
- Vietnamese doctor accounts
- Demo patient records
- Services
- Appointments in multiple statuses
- Treatment plans
- Invoices

### 8. Run the development server

```bash
python manage.py runserver
```

Open:

- App: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`

## Running Tests

```bash
python manage.py test
```

## Core Business Logic

### Appointment Validation

- A doctor cannot have two appointments at the same date and time
- Validation is enforced in the `Appointment` model

### Odontogram Automation

- A newly created patient automatically gets a full 32-tooth odontogram
- Completing a treatment plan updates the related tooth statuses

### Invoice Automation

- Invoices are created from treatment plans
- Invoice totals are calculated from the selected services

## UI Highlights

- Doctor dashboard with collapsible sidebar
- Multi-step booking page with progress tracking
- Interactive odontogram with modal-based tooth state editing
- Consistent CRUD pages built on the project design system

## Git Setup

The repository has been initialized locally.

Suggested first commit:

```bash
git add .
git commit -m "Initial commit"
```

Current default branch:

```bash
main
```

If you want to work on a separate branch:

```bash
git checkout -b codex/setup-project
```

## Notes

- PostgreSQL is now the default database backend
- `db.sqlite3` is still ignored in `.gitignore` but is no longer used by default
- Docker stores PostgreSQL data in `.pgdata/`
- `.venv/` and Python cache files are ignored
- The current setup is optimized for local development
- Tailwind CSS, Lucide Icons, and Chart.js are loaded via CDN, so an internet connection is required for full UI rendering
