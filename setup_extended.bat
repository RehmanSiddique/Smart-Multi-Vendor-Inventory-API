@echo off
REM Setup script for Extended Features

echo ========================================
echo Smart Multi-Vendor Inventory API
echo Extended Features Setup
echo ========================================
echo.

echo Step 1: Installing dependencies...
pip install -r requirements\extended.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

echo Step 2: Creating migrations...
python manage.py makemigrations
if %errorlevel% neq 0 (
    echo ERROR: Failed to create migrations
    pause
    exit /b 1
)
echo.

echo Step 3: Running migrations...
python manage.py migrate --skip-checks
if %errorlevel% neq 0 (
    echo ERROR: Failed to run migrations
    pause
    exit /b 1
)
echo.

echo Step 4: Collecting static files...
python manage.py collectstatic --noinput
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Start Redis: redis-server --port 6380
echo 2. Start Django: python manage.py runserver
echo 3. Start Celery Worker: celery -A config worker --pool=solo -l info
echo 4. Start Celery Beat: celery -A config beat -l info
echo.
echo See QUICK_START.md for testing instructions
echo.
pause
