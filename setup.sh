#!/bin/bash
# MediChain Django Setup Script
# Automates project initialization and configuration

set -e

echo "=========================================="
echo "  MediChain Framework Setup"
echo "=========================================="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"

# Create virtual environment
echo "→ Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "→ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "→ Installing dependencies..."
pip install -r requirements.txt

# Create directories
echo "→ Creating project directories..."
mkdir -p logs
mkdir -p media
mkdir -p static

# Run migrations
echo "→ Running database migrations..."
python manage.py migrate --database=default
python manage.py migrate --database=blockchain

# Collect static files
echo "→ Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser (optional)
echo ""
read -p "Create superuser? (y/n): " CREATE_SUPER
if [ "$CREATE_SUPER" = "y" ]; then
    python manage.py createsuperuser
fi

# Run tests
echo ""
read -p "Run test suite? (y/n): " RUN_TESTS
if [ "$RUN_TESTS" = "y" ]; then
    echo "→ Running tests..."
    python manage.py test tests --verbosity=2
fi

echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "Start the server:"
echo "  source venv/bin/activate"
echo "  python manage.py runserver"
echo ""
echo "Dashboard: http://localhost:8000/"
echo "Admin:     http://localhost:8000/admin/"
echo "API Docs:  http://localhost:8000/api/v1/"
echo ""
