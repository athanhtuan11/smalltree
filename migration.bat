@echo off
REM Tạo và apply migration cho database (an toàn, báo lỗi rõ ràng)
set FLASK_APP=run.py
set FLASK_ENV=development
echo [INFO] Start migration...
flask db migrate -m "init db"
echo [INFO] Upgrade database...
flask db upgrade
echo [SUCCESS] Migration SUCCESS!
