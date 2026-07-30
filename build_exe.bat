@echo off
setlocal enabledelayedexpansion
cls

echo ========================================================
echo   COMPILANDO SISTEMA PACIENTES (ONEFILE + CONSOLE)
echo ========================================================
echo.

:: 1. Validar que PyInstaller este disponible
where pyinstaller >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller no esta instalado o no esta activado el entorno virtual.
    echo Por favor activa tu entorno virtual ^(ej. venv\Scripts\activate^) e intenta de nuevo.
    echo.
    pause
    exit /b 1
)

:: 2. Validar que todos los archivos y carpetas --add-data y el icono existan obligatoriamente
echo [--] Validando integridad de recursos y dependencias...

if not exist "app\templates" (
    echo [ERROR] La carpeta obligatoria 'app\templates' no existe.
    pause
    exit /b 1
)

if not exist "app\static" (
    echo [ERROR] La carpeta obligatoria 'app\static' no existe.
    pause
    exit /b 1
)

if not exist "app\static\img\icons\logo.ico" (
    echo [ERROR] El archivo de icono obligatorio 'app\static\img\icons\logo.ico' no existe.
    pause
    exit /b 1
)

:: Validar si la base de datos existe en instance; si no, crear la carpeta vacía o advertir/crearla
if not exist "instance" mkdir instance
if not exist "instance\sgpn_nutricion.db" (
    echo [ADVERTENCIA] No se encontro 'instance\sgpn_nutricion.db'. Se creara un archivo base vacio para empaquetar.
    type nul > "instance\sgpn_nutricion.db"
)

:: 3. Limpieza de carpetas y archivos temporales previos
echo [--] Limpiando compilaciones anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /f /q *.spec

if exist dist (
    echo.
    echo [ERROR] No se pudo eliminar la carpeta 'dist'. 
    echo Asegurate de cerrar 'SistemaPacientes.exe' si esta ejecutandose.
    echo.
    pause
    exit /b 1
)

echo [--] Iniciando empaquetado con PyInstaller...
echo.

:: 4. Ejecutar PyInstaller con separador Windows (;) y todas las validaciones
pyinstaller --noconfirm --onefile --console ^
  --add-data "app/templates;app/templates" ^
  --add-data "app/static;app/static" ^
  --add-data "instance/sgpn_nutricion.db;instance" ^
  --icon="app/static/img/icons/logo.ico" ^
  --name "SistemaPacientes" run.py

:: 5. Evaluacion de Errores
if %errorlevel% equ 0 (
    if exist "dist\SistemaPacientes.exe" (
        echo.
        echo ========================================================
        echo   ¡COMPILACION EXITOSA!
        echo ========================================================
        echo Archivo generado en: dist\SistemaPacientes.exe
        echo.
    ) else (
        echo.
        echo [ERROR] PyInstaller finalizo sin codigo de error, pero no se encontro el .exe en dist\
        echo.
    )
) else (
    echo.
    echo ========================================================
    echo   [ERROR] FALLO LA COMPILACION CON CODIGO %errorlevel%
    echo ========================================================
    echo Revisa los mensajes anteriores en la consola para identificar la causa.
    echo.
)

pause
