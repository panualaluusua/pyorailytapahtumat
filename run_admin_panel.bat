@echo off
echo === Pyöräilytapahtumat - Hallintapaneeli ===
echo Tämä työkalu auttaa hallitsemaan tapahtumia ja poistamaan duplikaatteja
echo ===============================
echo.

python -m streamlit run src/event_admin.py

echo.
echo Press any key to exit...
pause > nul 