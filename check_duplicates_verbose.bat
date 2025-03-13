@echo off
echo === Bike Event Duplicate Checker (Verbose Mode) ===
echo This script will check for duplicate events in all_events.json
echo with verbose output and a lower similarity threshold (0.7)
echo ===============================
echo.

python src/check_duplicates.py --verbose --threshold 0.7

echo.
echo Press any key to exit...
pause > nul 