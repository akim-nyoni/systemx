# System X — Rhapsody’s Management Platform

A professional web application built with Django for managing checklists, form submissions, reporting, and user access control.

---

## Getting Started

To run the project locally:

1. Set up a virtual environment and activate it
2. Install the required dependencies
3. Run database migrations and seed initial data
4. Start the development server
5. Open the app in your browser at the local server address

Default login accounts are provided for testing (Admin, Manager, Viewer), but these should be changed immediately before deploying to production.

---

## Project Overview

The system is organized into several core components:

* Core configuration — handles project settings and routing
* Accounts module — manages users, authentication, and roles
* Forms builder — allows creation of checklists, sections, and submissions
* Dashboard — provides reports and system overview
* Templates — contains all frontend pages
* Static and media files — stores assets and uploaded images

---

## User Roles

The platform supports three main roles:

* Admin
  Full system control, including managing users, building forms, and viewing all reports

* Manager
  Completes assigned checklists, submits forms, and views relevant reports

* Viewer
  Read-only access to submissions and reports

---

## Preloaded Checklists

The system comes with ready-to-use checklists based on operational needs:

* Management Opening Checklist
* Management Closing Checklist
* Cleaning and Maintenance Checklist
* Bar Daily Checklist
* Kitchen Daily Checklist
* 30-Minute Schedule Check

These cover daily operations across front-of-house, kitchen, and maintenance activities.

---

## Key Features

### For Managers

* Access only assigned forms
* Automatic saving while filling forms
* Required comments for incomplete or failed items
* Optional photo uploads for issues
* Real-time progress tracking
* Ability to save drafts and submit later

### For Administrators

* Visual form builder with live updates
* Bulk item creation for faster setup
* Flexible assignment of forms to users
* Full user and role management

### Reporting Dashboard

* Filter reports by manager, form, date, and response type
* Overview statistics including total, completed, and flagged submissions
* Highlighted problem areas with comments and images
* Visual indicators for completion status

---

## Image Handling

Images uploaded during form submissions are stored in a structured media directory.

For production environments, it is recommended to use a scalable storage solution such as cloud storage.

---

## Production Readiness

Before deploying:

* Disable debug mode
* Use a secure secret key
* Configure allowed hosts
* Switch to a production database such as PostgreSQL
* Set up a production server such as Gunicorn with Nginx
* Configure static and media file handling
* Update all default credentials

---

## Future Expansion

An inventory module is planned, which will allow:

* Tracking of stock items
* Integration with form submissions
* Real-time inventory updates

---

## Technology Stack

* Backend: Django
* Database: SQLite for development, PostgreSQL for production
* Frontend: HTML, CSS, and JavaScript
* Image Processing: Pillow
* Deployment: Compatible with standard web servers
