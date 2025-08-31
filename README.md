# SmallTree Academy - Nursery Management System

**Production Website**: [mamnoncaynho.com](http://mamnoncaynho.com)

A comprehensive nursery school management system built with Flask, featuring student management, attendance tracking, activities, and curriculum planning.

## 🚀 Quick Deployment

### Prerequisites
- Ubuntu/Debian server
- Domain pointing to server IP
- Git installed

### 1. Clone Repository
```bash
su - smalltree  # Switch to smalltree user
git clone https://github.com/athanhtuan11/smalltree.git /home/smalltree/smalltree
cd /home/smalltree/smalltree
```

### 2. Setup Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Deploy to Production
```bash
sudo bash deploy.sh
```

## 🛠️ Development

### Local Setup
```bash
# Clone and setup
git clone https://github.com/athanhtuan11/smalltree.git
cd smalltree
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run development server
python3 run.py
```

### Project Structure
```
smalltree/
├── app/                 # Main application
│   ├── __init__.py     # App factory
│   ├── models.py       # Database models
│   ├── routes.py       # Application routes
│   ├── forms.py        # WTF forms
│   ├── static/         # CSS, JS, images
│   └── templates/      # HTML templates
├── migrations/         # Database migrations
├── deploy.sh          # Production deployment
├── debug.sh           # Debug tool
├── run.py             # Application entry point
├── config.py          # Configuration
└── requirements.txt   # Dependencies
```

## 📊 Features

- **Student Management**: Registration, profiles, class assignment
- **Attendance Tracking**: Daily attendance with history
- **Activities**: School activities with photo galleries
- **Curriculum**: Weekly curriculum planning and materials
- **Staff Management**: Teacher and staff profiles
- **Food Safety**: 3-step food safety process tracking
- **Reports**: Excel exports for various reports

## 🔧 Management Commands

```bash
# Check status
sudo systemctl status smalltree
sudo systemctl status nginx

# View logs
sudo journalctl -u smalltree -f

# Restart services
sudo systemctl restart smalltree
sudo systemctl restart nginx

# Debug issues
bash debug.sh
```

## 📁 Database

- **Type**: SQLite (production) / Any SQL database supported
- **Location**: `app/site.db`
- **Models**: Child, Staff, Activity, Curriculum, AttendanceRecord, etc.

## 🚨 Troubleshooting

### Common Issues

1. **Permission errors**: Check file ownership
   ```bash
   sudo chown -R smalltree:smalltree /home/smalltree/smalltree
   ```

2. **Database errors**: Verify database permissions
   ```bash
   ls -la /home/smalltree/smalltree/app/
   ```

3. **Service won't start**: Check logs
   ```bash
   sudo journalctl -u smalltree -f
   ```

### Debug Tools
- `bash debug.sh` - Quick system check
- `python3 debug_database.py` - Database diagnostics

## 🔐 Configuration

### Environment Variables (`.env`)
```
SECRET_KEY=your-secret-key
FLASK_ENV=production
DATABASE_URL=sqlite:///app/site.db
DOMAIN=mamnoncaynho.com
```

### Nginx Configuration
- **Static files**: Served directly by Nginx
- **Application**: Proxied to Gsmalltree-website on port 5000
- **Domain**: mamnoncaynho.com, www.mamnoncaynho.com

## 📜 License

Private project for SmallTree Academy.

## 👥 Support

For technical support, contact the development team.

---

**Last Updated**: August 2025
**Version**: 2.0 (Clean & Optimized)