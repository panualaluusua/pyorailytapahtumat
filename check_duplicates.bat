@echo off
echo === Bike Event Duplicate Checker ===
echo This script will check for duplicate events in all_events.json
echo ===============================
echo.

python src/check_duplicates.py

echo.
echo Press any key to exit...
pause > nul 