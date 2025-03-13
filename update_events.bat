@echo off
echo === Bike Event Manager ===
echo This script will:
echo 1. Scrape events from Bikeland.fi
echo 2. Process events from the CSV file
echo 3. Process manual events from simple_events.txt
echo 4. Combine all events and remove duplicates
echo 5. Generate the output file for the Streamlit app
echo ===============================
echo.

python src/event_manager.py

echo.
echo Press any key to exit...
pause > nul 