@echo off
pyinstaller --noconsole --onefile --icon="app_icon.ico" Mouse_Scanner.py
echo.
echo ===== Готово. Нажми любую клавишу для выхода =====
pause >nul