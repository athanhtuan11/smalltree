#!/bin/bash
# smalltree Website Maintenance Script
# Auto update and maintain Nginx + Gunicorn setup

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_NAME="smalltree"
DOMAIN="mamnoncaynho.com"
SERVER_IP="180.93.136.198"
PROJECT_PATH="/home/smalltree/smalltree"  # Git clone location
SERVICE_NAME="smalltree-gunicorn"
VENV_PATH="$PROJECT_PATH/venv"

print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  update       - Update code from git and restart services"
    echo "  restart      - Restart all services"
    echo "  status       - Show service status"
    echo "  logs         - Show recent logs"
    echo "  backup       - Manual backup"
    echo "  health       - Health check"
    echo "  ssl          - Install SSL certificate (Let's Encrypt)"
    echo "  deps         - Update Python dependencies"
    echo "  clean        - Clean temporary files and logs"
    echo
}

update_code() {
    print_info "Updating code from repository..."
    cd $PROJECT_PATH
    
    # Backup current state
    print_info "Creating backup before update..."
    /usr/local/bin/smalltree-backup.sh
    
    # Pull latest code
    git pull origin master
    
    # Activate virtual environment and update dependencies
    sudo -u www-data bash -c "
        cd $PROJECT_PATH
        source $VENV_PATH/bin/activate
        pip install -r requirements.txt --upgrade
    "
    
    # Run migrations if any
    sudo -u www-data bash -c "
        cd $PROJECT_PATH
        source $VENV_PATH/bin/activate
        export FLASK_APP=run.py
        flask db upgrade
    "
    
    # Restart services
    restart_services
    
    print_status "Code updated successfully"
}

restart_services() {
    print_info "Restarting services..."
    systemctl restart $SERVICE_NAME
    systemctl restart nginx
    sleep 3
    
    if check_services; then
        print_status "Services restarted successfully"
    else
        print_error "Service restart failed"
        return 1
    fi
}

check_services() {
    local gunicorn_status=$(systemctl is-active $SERVICE_NAME)
    local nginx_status=$(systemctl is-active nginx)
    
    if [ "$gunicorn_status" = "active" ] && [ "$nginx_status" = "active" ]; then
        return 0
    else
        return 1
    fi
}

show_status() {
    echo -e "${BLUE}========== SERVICE STATUS ==========${NC}"
    echo
    
    echo -e "${YELLOW}Gunicorn Status:${NC}"
    systemctl status $SERVICE_NAME --no-pager -l
    echo
    
    echo -e "${YELLOW}Nginx Status:${NC}"
    systemctl status nginx --no-pager -l
    echo
    
    echo -e "${YELLOW}Disk Usage:${NC}"
    df -h $PROJECT_PATH
    echo
    
    echo -e "${YELLOW}Memory Usage:${NC}"
    free -h
    echo
    
    echo -e "${YELLOW}Process Information:${NC}"
    ps aux | grep -E "(gunicorn|nginx)" | grep -v grep
}

show_logs() {
    echo -e "${BLUE}========== RECENT LOGS ==========${NC}"
    echo
    
    echo -e "${YELLOW}Gunicorn Logs (last 50 lines):${NC}"
    journalctl -u $SERVICE_NAME -n 50 --no-pager
    echo
    
    echo -e "${YELLOW}Nginx Error Logs:${NC}"
    tail -n 20 /var/log/nginx/error.log
    echo
    
    echo -e "${YELLOW}Application Logs:${NC}"
    if [ -f "/var/log/smalltree/gunicorn_error.log" ]; then
        tail -n 20 /var/log/smalltree/gunicorn_error.log
    else
        echo "No application logs found"
    fi
}

manual_backup() {
    print_info "Starting manual backup..."
    /usr/local/bin/smalltree-backup.sh
    print_status "Manual backup completed"
    
    echo -e "${YELLOW}Backup files:${NC}"
    ls -la /var/backups/smalltree/ | tail -5
}

health_check() {
    print_info "Performing health check..."
    
    # Check services
    if check_services; then
        print_status "Services are running"
    else
        print_error "Services are not running properly"
    fi
    
    # Check website response
    if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200"; then
        print_status "Website is responding"
    else
        print_warning "Website may not be responding correctly"
    fi
    
    # Check disk space
    local disk_usage=$(df $PROJECT_PATH | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ $disk_usage -lt 80 ]; then
        print_status "Disk space is sufficient ($disk_usage% used)"
    else
        print_warning "Disk space is getting low ($disk_usage% used)"
    fi
    
    # Check database
    if [ -f "$PROJECT_PATH/app/site.db" ]; then
        print_status "Database file exists"
    else
        print_error "Database file is missing"
    fi
    
    # Check logs for errors
    local error_count=$(journalctl -u $SERVICE_NAME --since "1 hour ago" | grep -i error | wc -l)
    if [ $error_count -eq 0 ]; then
        print_status "No recent errors in logs"
    else
        print_warning "Found $error_count errors in recent logs"
    fi
}

install_ssl() {
    print_info "Installing SSL certificate with Let's Encrypt..."
    
    # Install certbot
    apt update
    apt install -y certbot python3-certbot-nginx
    
    # Get domain from nginx config
    local domain=$(grep server_name /etc/nginx/sites-available/$PROJECT_NAME | awk '{print $2}' | sed 's/;//')
    
    if [ "$domain" = "localhost" ]; then
        print_error "Cannot install SSL for localhost. Please update domain in nginx config first."
        return 1
    fi
    
    print_info "Installing SSL for domain: $domain"
    certbot --nginx -d $domain
    
    # Set up auto-renewal
    crontab -l | grep -q certbot || (crontab -l; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
    
    print_status "SSL certificate installed and auto-renewal configured"
}

update_dependencies() {
    print_info "Updating Python dependencies..."
    cd $PROJECT_PATH
    
    sudo -u www-data bash -c "
        cd $PROJECT_PATH
        source $VENV_PATH/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt --upgrade
    "
    
    # Check for security vulnerabilities
    sudo -u www-data bash -c "
        cd $PROJECT_PATH
        source $VENV_PATH/bin/activate
        pip install safety
        safety check
    "
    
    restart_services
    print_status "Dependencies updated"
}

clean_system() {
    print_info "Cleaning temporary files and logs..."
    
    # Clean Python cache
    find $PROJECT_PATH -name "__pycache__" -type d -exec rm -rf {} +
    find $PROJECT_PATH -name "*.pyc" -delete
    
    # Rotate logs
    if [ -f "/var/log/smalltree/gunicorn_access.log" ]; then
        logrotate -f /etc/logrotate.d/smalltree 2>/dev/null || true
    fi
    
    # Clean old backups (keep last 30 days)
    find /var/backups/smalltree -name "*.db" -mtime +30 -delete 2>/dev/null || true
    find /var/backups/smalltree -name "*.tar.gz" -mtime +30 -delete 2>/dev/null || true
    
    # Clean package cache
    apt autoremove -y
    apt autoclean
    
    print_status "System cleaned"
}

# Main script logic
case "$1" in
    update)
        update_code
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    backup)
        manual_backup
        ;;
    health)
        health_check
        ;;
    ssl)
        install_ssl
        ;;
    deps)
        update_dependencies
        ;;
    clean)
        clean_system
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
