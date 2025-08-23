@echo off
REM Tạo và apply migration cho database (an toàn, báo lỗi rõ ràng)
set FLASK_APP=run.py
set FLASK_ENV=development
echo [INFO] Start migration...
python -m flask db migrate -m "auto migration"
echo [INFO] Upgrade database...
python -m flask db upgrade
echo [SUCCESS] Migration SUCCESS!
