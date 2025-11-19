#!/bin/bash
# Script tự động migrate ảnh cũ lên R2
# Setup cronjob: crontab -e
# Thêm dòng: 0 3 * * * /path/to/auto_migrate_r2.sh >> /path/to/logs/r2-cron.log 2>&1

# Đường dẫn project
PROJECT_DIR="/path/to/smalltree-website"  # THAY ĐỔI ĐƯỜNG DẪN NÀY
VENV_DIR="${PROJECT_DIR}/venv"

# Chuyển vào thư mục project
cd "$PROJECT_DIR" || exit 1

# Kích hoạt virtual environment
source "${VENV_DIR}/bin/activate" || exit 1

# Chạy migration
echo "=========================================="
echo "$(date '+%Y-%m-%d %H:%M:%S') - Bắt đầu migrate R2"
echo "=========================================="

python migrate_to_r2.py

echo "=========================================="
echo "$(date '+%Y-%m-%d %H:%M:%S') - Hoàn thành"
echo "=========================================="
