@echo off
setlocal
cd /d "%~dp0"

set "VENV_PY=.venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
  echo .venv no existe. Creando entorno virtual...
  py -3.12 -m venv .venv 2>nul
  if errorlevel 1 python -m venv .venv
)

"%VENV_PY%" -V >nul 2>nul
if errorlevel 1 (
  echo .venv esta dañado. Recreando entorno virtual...
  rmdir /s /q .venv 2>nul
  py -3.12 -m venv .venv 2>nul
  if errorlevel 1 python -m venv .venv
)

"%VENV_PY%" -V >nul 2>nul
if errorlevel 1 (
  echo No se pudo crear un entorno virtual funcional en .venv
  pause
  exit /b 1
)

echo [1/3] Instalando dependencias de build...
"%VENV_PY%" -m pip install pyinstaller python-escpos pyusb pywin32 pillow pandas openpyxl xlsxwriter reportlab python-barcode qrcode pyttsx3 matplotlib
if errorlevel 1 (
  echo Error instalando dependencias.
  pause
  exit /b 1
)
"%VENV_PY%" -m PyInstaller --version >nul 2>nul
if errorlevel 1 (
  echo PyInstaller no quedo disponible tras instalar dependencias.
  pause
  exit /b 1
)

echo [2/3] Generando ejecutable PyInstaller...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
rmdir /s /q dist_installer 2>nul
"%VENV_PY%" -m PyInstaller --noconfirm VmPOS.spec
if errorlevel 1 (
  echo Error generando el ejecutable.
  pause
  exit /b 1
)
if not exist "dist\VmPOS\VmPOS.exe" (
  echo No se encontro dist\VmPOS\VmPOS.exe despues de compilar.
  pause
  exit /b 1
)

echo [3/3] Construyendo instalador Inno Setup...
set "ISCC_EXE="
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC_EXE=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC_EXE=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC_EXE=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE for /f "delims=" %%I in ('where.exe ISCC.exe 2^>nul') do (
  if not defined ISCC_EXE set "ISCC_EXE=%%~I"
)
if not defined ISCC_EXE (
  echo No se encontro Inno Setup (ISCC.exe).
  echo Instala Inno Setup 6: https://jrsoftware.org/isdl.php
  pause
  exit /b 1
)

"%ISCC_EXE%" "installer\VmPOS.iss"
if errorlevel 1 (
  echo Error construyendo instalador.
  pause
  exit /b 1
)
if not exist "dist_installer" mkdir "dist_installer"
if not exist "dist_installer\VmPOS_instalador.exe" (
  echo Inno Setup termino pero no se encontro dist_installer\VmPOS_instalador.exe
  echo Revisa el OutputDir/OutputBaseFilename en installer\VmPOS.iss
  pause
  exit /b 1
)

echo.
echo Listo: dist_installer\VmPOS_instalador.exe
pause
