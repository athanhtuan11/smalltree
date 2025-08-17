#!/bin/bash
# Backup script for production data

# Configuration
BACKUP_DIR="backups"
DB_FILE="app/site.db"
UPLOADS_DIR="app/static/uploads"
ACTIVITIES_DIR="app/static/images/activities"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory if not exists
mkdir -p "$BACKUP_DIR"

echo "Starting backup at $(date)"

# Backup database
if [ -f "$DB_FILE" ]; then
    cp "$DB_FILE" "$BACKUP_DIR/site_db_backup_$DATE.db"
    echo "✅ Database backed up to: $BACKUP_DIR/site_db_backup_$DATE.db"
else
    echo "⚠️  Database file not found: $DB_FILE"
fi

# Backup uploaded files
if [ -d "$UPLOADS_DIR" ]; then
    tar -czf "$BACKUP_DIR/uploads_backup_$DATE.tar.gz" "$UPLOADS_DIR"
    echo "✅ Uploads backed up to: $BACKUP_DIR/uploads_backup_$DATE.tar.gz"
fi

# Backup activity images
if [ -d "$ACTIVITIES_DIR" ]; then
    tar -czf "$BACKUP_DIR/activities_backup_$DATE.tar.gz" "$ACTIVITIES_DIR"
    echo "✅ Activity images backed up to: $BACKUP_DIR/activities_backup_$DATE.tar.gz"
fi

# Backup .env file (if exists)
if [ -f ".env.production" ]; then
    cp ".env.production" "$BACKUP_DIR/env_backup_$DATE"
    echo "✅ Environment config backed up"
fi

echo "Backup completed at $(date)"

# Clean up old backups (keep last 30 days)
find "$BACKUP_DIR" -name "*backup*" -mtime +30 -delete
echo "✅ Old backups cleaned up"
