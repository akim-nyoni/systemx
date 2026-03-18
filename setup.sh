#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
#  System X – Quick Start Script
#  Rhapsody's Phakalane Management Platform
# ─────────────────────────────────────────────────────────────────

set -e

echo "🚀 Setting up System X..."

# 1. Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# 2. Run migrations
echo ""
echo "🗄️  Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# 3. Seed with Rhapsody's data
echo ""
echo "🌱 Seeding Rhapsody's checklist data..."
python manage.py seed_rhapsodys

# 4. Collect static files (optional for dev)
# python manage.py collectstatic --noinput

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  ✅  System X is ready!"
echo ""
echo "  Start the server:"
echo "    python manage.py runserver"
echo ""
echo "  Then open:  http://127.0.0.1:8000"
echo ""
echo "  Login credentials:"
echo "    Admin:    admin    / admin123"
echo "    Manager:  akim     / manager123"
echo "    Viewer:   viewer   / viewer123"
echo "═══════════════════════════════════════════════════════════"
