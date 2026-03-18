# System X — Rhapsody's Phakalane Management Platform

A professional Django web application for digital management checklists, form submissions, reporting, and access control.

---

## 🚀 Quick Start

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run migrations + seed data
python manage.py makemigrations
python manage.py migrate
python manage.py seed_rhapsodys

# 4. Start the server
python manage.py runserver

# 5. Open http://127.0.0.1:8000
```

**Default login credentials:**

| Role      | Username | Password    |
|-----------|----------|-------------|
| Admin     | admin    | admin123    |
| Manager   | akim     | manager123  |
| Viewer    | viewer   | viewer123   |

> ⚠️ Change all passwords immediately in production!

---

## 📁 Project Structure

```
systemx/
├── systemx/            # Django project config (settings, urls, wsgi)
├── accounts/           # Custom user model, roles, auth
├── forms_builder/      # Forms, sections, items, submissions, responses
│   └── management/
│       └── commands/
│           └── seed_rhapsodys.py   # Seeds all Rhapsody's checklists
├── dashboard/          # Home dashboard + reports
├── templates/          # All HTML templates
│   ├── base.html       # Master layout with sidebar
│   ├── accounts/       # Login, profile, user management
│   ├── forms_builder/  # Fill forms, builder, submission detail
│   └── dashboard/      # Dashboard, reports
├── media/              # Uploaded images (created at runtime)
├── static/             # Static assets
├── requirements.txt
└── setup.sh
```

---

## 🗝️ User Roles

| Role          | Permissions                                              |
|---------------|----------------------------------------------------------|
| **Admin**     | Full access — manage users, build forms, view all reports|
| **Manager**   | Fill forms, view own reports, see flagged items          |
| **Viewer**    | Read-only access to reports and submissions              |

---

## 📋 Pre-loaded Checklists (from PDF)

1. **Management Opening Checklist** — Opening duties, FOH day setup, administration
2. **Management Closing Checklist** — Night FOH, full closing procedure (33 items)
3. **Cleaning & Maintenance Checklist** — Outside, smoking area, non-smoking, waiter stations, private room
4. **Bar Daily Checklist** — Setup, equipment, cleaning, glassware counts
5. **Kitchen Daily Checklist** — Coordinator checks, grill, flat-top, salad, sushi bar (50+ items)
6. **30-Minute Schedule Check** — Regular interval checks

---

## 🔑 Key Features

### For Managers
- See only forms assigned to them
- Autosave on every Yes/No click (AJAX)
- **No response = required comment/explanation**
- Optional photo upload on failed items
- Progress indicator with real-time percentage
- Draft → submit workflow

### For Administrators
- **Form Builder** — create sections and items visually with instant AJAX updates
- **Bulk add** items by pasting a list
- Assign forms to all managers or specific users
- Manage all users and their roles

### Reports Dashboard
- Filter by: **manager, form, date range, response type, branch**
- Summary stats: total, perfect, flagged submissions
- **Flagged items table** showing all "No" responses with comments and photos
- Colour-coded completion indicators

---

## 🖼️ Image Storage

Photos uploaded on failed checklist items are saved to:
```
media/responses/YYYY/MM/filename.jpg
```

The `MEDIA_ROOT` setting points to the `media/` folder in the project root. For production, configure a proper file storage backend (S3, etc.).

---

## 🔒 Production Checklist

Before going live:

1. Set `DEBUG = False` in `settings.py`
2. Set a strong `SECRET_KEY` (use environment variable)
3. Set `ALLOWED_HOSTS` to your domain
4. Configure a production database (PostgreSQL recommended)
5. Set up a proper WSGI server (Gunicorn + Nginx)
6. Configure file storage for media files
7. Run `python manage.py collectstatic`
8. Change all default passwords

---

## 🔮 Planned: Inventory Module

The codebase is structured to easily add an `inventory` app. When ready:
- Add `inventory` to `INSTALLED_APPS`
- Link inventory items to form submissions for real-time stock tracking

---

## 📞 Tech Stack

- **Backend:** Django 4.2, SQLite (dev) / PostgreSQL (prod)
- **Frontend:** Vanilla HTML/CSS/JS (no framework dependencies)
- **Images:** Pillow
- **Deployment:** Any WSGI-compatible host
