@echo off
setlocal
cd /d "%~dp0"

echo ========================================================
echo   COMPILANDO SGPN PARA WINDOWS
echo ========================================================

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python no esta disponible en PATH.
    exit /b 1
)

python -c "import PyInstaller, defusedxml, flask, flask_login, flask_sqlalchemy, flask_wtf, openpyxl, waitress" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Faltan dependencias. Ejecuta: pip install -r requirements-build.txt
    exit /b 1
)

if not exist "app\templates" (
    echo [ERROR] No existe app\templates.
    exit /b 1
)
if not exist "app\static" (
    echo [ERROR] No existe app\static.
    exit /b 1
)

echo [1/4] Generando y validando recursos locales...
python scripts\build_local_assets.py
if errorlevel 1 exit /b 1

echo [2/4] Validando sintaxis...
python -m compileall -q app run.py seed_admin.py
if errorlevel 1 exit /b 1

echo [3/4] Limpiando compilaciones anteriores...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "SistemaPacientes.spec" del /f /q "SistemaPacientes.spec"
python scripts\cleanup_project.py --quiet
if errorlevel 1 (
    echo [ERROR] No fue posible limpiar artefactos obsoletos.
    exit /b 1
)

echo [4/4] Generando ejecutable...
pyinstaller --noconfirm --clean --onefile --console ^
  --icon "app/static/img/logo.ico" ^
  --add-data "app/templates;app/templates" ^
  --add-data "app/static;app/static" ^
  --collect-submodules flask_wtf ^
  --name "SistemaPacientes" run.py
if errorlevel 1 (
    echo [ERROR] PyInstaller no pudo generar la entrega.
    exit /b 1
)

if not exist "dist\SistemaPacientes.exe" (
    echo [ERROR] No se encontro dist\SistemaPacientes.exe.
    exit /b 1
)

echo [OK] Ejecutable generado: dist\SistemaPacientes.exe
exit /b 0
