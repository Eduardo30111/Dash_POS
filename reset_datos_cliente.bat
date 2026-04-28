@echo off
setlocal
set "APP_DIR=%LOCALAPPDATA%\VmPOS"
set "DB_DIR=%APP_DIR%\database"

echo VmPOS - Reinicio de datos locales de cliente
echo Carpeta objetivo: "%DB_DIR%"
echo.
choice /M "Esto borrara ventas/usuarios locales de este equipo. Desea continuar"
if errorlevel 2 exit /b 0

if exist "%DB_DIR%" (
  rmdir /s /q "%DB_DIR%"
)
mkdir "%DB_DIR%" >nul 2>nul
copy "%~dp0database\license_remote.example.json" "%DB_DIR%\license_remote.json" >nul 2>nul

echo.
echo Listo. Al abrir VmPOS de nuevo, se creara base limpia con:
echo   usuario: admin
echo   clave:   admin123
pause
