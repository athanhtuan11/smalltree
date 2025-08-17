@echo off
REM Backup script for production data on Windows

REM Configuration
set BACKUP_DIR=backups
set DB_FILE=app\site.db
set UPLOADS_DIR=app\static\uploads
set ACTIVITIES_DIR=app\static\images\activities
set DATE=%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set DATE=%DATE: =0%

REM Create backup directory if not exists
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

echo Starting backup at %date% %time%

REM Backup database
if exist "%DB_FILE%" (
    copy "%DB_FILE%" "%BACKUP_DIR%\site_db_backup_%DATE%.db"
    echo ✅ Database backed up to: %BACKUP_DIR%\site_db_backup_%DATE%.db
) else (
    echo ⚠️  Database file not found: %DB_FILE%
)

REM Backup uploaded files
if exist "%UPLOADS_DIR%" (
    powershell Compress-Archive -Path "%UPLOADS_DIR%" -DestinationPath "%BACKUP_DIR%\uploads_backup_%DATE%.zip" -Force
    echo ✅ Uploads backed up to: %BACKUP_DIR%\uploads_backup_%DATE%.zip
)

REM Backup activity images
if exist "%ACTIVITIES_DIR%" (
    powershell Compress-Archive -Path "%ACTIVITIES_DIR%" -DestinationPath "%BACKUP_DIR%\activities_backup_%DATE%.zip" -Force
    echo ✅ Activity images backed up to: %BACKUP_DIR%\activities_backup_%DATE%.zip
)

REM Backup .env file (if exists)
if exist ".env.production" (
    copy ".env.production" "%BACKUP_DIR%\env_backup_%DATE%.env"
    echo ✅ Environment config backed up
)

echo Backup completed at %date% %time%

REM Clean up old backups (keep last 30 files)
forfiles /p "%BACKUP_DIR%" /s /m "*backup*" /d -30 /c "cmd /c del @path" 2>nul

echo ✅ Old backups cleaned up
pause
