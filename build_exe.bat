@echo off
setlocal
cd /d "%~dp0"

call .venv\Scripts\activate 2>nul
if errorlevel 1 (
  echo Crea un venv: python -m venv .venv
  exit /b 1
)

pip install -q pyinstaller python-escpos pyusb pywin32 pillow pandas openpyxl xlsxwriter reportlab python-barcode qrcode pyttsx3 2>nul

rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

pyinstaller --noconfirm VmPOS.spec
echo.
echo Salida: dist\VmPOS\
pause
