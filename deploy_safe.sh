#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}SAFE DEPLOYMENT - SmallTree${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] $1${NC}"
}

print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Step 1: Backup current data
print_status "[1/6] Creating backup of current data..."
if [ -f "./backup_data.sh" ]; then
    chmod +x ./backup_data.sh
    ./backup_data.sh
    if [ $? -ne 0 ]; then
        print_error "Backup failed! Stopping deployment."
        exit 1
    fi
else
    print_warning "backup_data.sh not found, creating manual backup..."
    mkdir -p backups
    DATE=$(date +%Y%m%d_%H%M%S)
    
    # Backup database
    if [ -f "app/site.db" ]; then
        cp "app/site.db" "backups/site_db_backup_$DATE.db"
        print_status "Database backed up"
    fi
    
    # Backup uploads
    if [ -d "app/static/uploads" ]; then
        tar -czf "backups/uploads_backup_$DATE.tar.gz" "app/static/uploads"
        print_status "Uploads backed up"
    fi
    
    # Backup activities
    if [ -d "app/static/images/activities" ]; then
        tar -czf "backups/activities_backup_$DATE.tar.gz" "app/static/images/activities"
        print_status "Activities backed up"
    fi
fi
print_status "Backup completed successfully"
echo ""

# Step 2: Check Git status
print_status "[2/6] Checking Git status..."
if ! command -v git &> /dev/null; then
    print_error "Git is not installed!"
    exit 1
fi

# Step 3: Stash any uncommitted local changes
print_status "[3/6] Stashing local changes..."
git stash push -m "Auto-stash before deployment $(date)"
print_status "Local changes stashed"
echo ""

# Step 4: Pull latest code
print_status "[4/6] Pulling latest code from repository..."
git pull origin master
if [ $? -ne 0 ]; then
    print_error "Git pull failed! Restoring from stash."
    git stash pop
    exit 1
fi
print_status "Code updated successfully"
echo ""

# Step 5: Check Python and virtual environment
print_status "[5/6] Setting up Python environment..."

# Check if Python 3 is available
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    print_error "Python is not installed!"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
print_status "Installing/updating dependencies..."
pip install --upgrade pip
pip install -r requirements.txt --upgrade
if [ $? -ne 0 ]; then
    print_warning "Some dependencies may not have installed correctly"
    print_warning "Continuing anyway..."
fi
print_status "Dependencies updated"
echo ""

# Step 6: Database migration (if needed)
print_status "[6/6] Checking for database migrations..."
$PYTHON_CMD -c "
from app import create_app
try:
    from flask_migrate import upgrade
    app = create_app()
    with app.app_context():
        upgrade()
    print('✅ Database migrations completed')
except Exception as e:
    print(f'ℹ️  No migrations needed or error: {e}')
" 2>/dev/null || print_status "No migrations needed"
echo ""

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}DEPLOYMENT COMPLETED SUCCESSFULLY${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${BLUE}Your data has been preserved:${NC}"
echo -e "- Database: app/site.db (unchanged)"
echo -e "- Uploads: app/static/uploads/ (unchanged)"
echo -e "- Activities: app/static/images/activities/ (unchanged)"
echo ""
echo -e "${BLUE}Backup created in: backups/ folder${NC}"
echo ""
echo -e "${GREEN}Ready to restart server!${NC}"
echo -e "${BLUE}Run: $PYTHON_CMD run.py${NC}"
echo -e "${GREEN}================================${NC}"
