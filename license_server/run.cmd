@echo off
REM Token para entrar al panel /dashboard (mismo valor que en app.py si no hay variable de entorno).
if "%VMPOS_LICENSE_ADMIN_TOKEN%"=="" set VMPOS_LICENSE_ADMIN_TOKEN=Eduardo2180
cd /d "%~dp0"
python app.py
