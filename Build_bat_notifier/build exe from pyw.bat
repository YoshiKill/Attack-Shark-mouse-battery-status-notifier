@echo off
pyinstaller --noconsole --onefile --icon="app_icon.ico" --add-data "rain.png;." Atack_bat_monitor.pyw
echo.
echo ===== Готово. Нажми любую клавишу для выхода =====
pause >nul