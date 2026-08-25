# Ejecución de pruebas de validación

## 1. Preparación en Windows PowerShell

Desde la carpeta raíz del proyecto, donde se encuentran `run.py` y `requirements.txt`:

```powershell
cd C:\ruta\al\proyecto\SMBase
py -3.10 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

Si el entorno ya existe, basta con activarlo e instalar o actualizar las dependencias de desarrollo:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

También es posible ejecutar sin activar el entorno:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## 2. Prueba oficial con pytest

Comando recomendado:

```powershell
python -m pytest -q
```

Resultado esperado para la versión 1.7.6:

```text
80 passed
```

`pytest` también descubre los 15 casos escritos con `unittest`; por ello no es necesario ejecutar ambos comandos en cada validación.

Para ejecutar únicamente los casos de interfaz, shell, tema, contraste de estados interactivos, pestañas, impresión, KPIs y estados vacíos:

```powershell
python -m pytest -q tests/test_ui_modules.py
```

Para validar el modal existente, búsqueda privada de pacientes, agenda rápida del KPI, calendario, disponibilidad, conflictos y auditoría:

```powershell
python -m pytest -q tests/test_appointments.py
```

Para validar perfiles profesionales, cédula, snapshot del autor y restricción de antropometría:

```powershell
python -m pytest -q tests/test_professional_profiles.py
```

Para validar recetas originales/adicionales/sustituciones, migración, impresión compacta, orden, cuenta en sidebar, estado cerrado del menú e icono:

```powershell
python -m pytest -q tests/test_prescriptions.py
```

Para validar el turno diario global, su API sin caché y la migración de consultas legadas:

```powershell
python -m pytest -q tests/test_daily_consultation_sequence.py
```

Para validar login, cambio/restablecimiento de contraseña, invalidación de sesiones y recuperación local:

```powershell
python -m pytest -q tests/test_security.py
```

Para validar que la limpieza de actualizaciones no elimina datos ni el entorno virtual:

```powershell
python -m pytest -q tests/test_project_cleanup.py
```

Para ver el nombre de cada prueba:

```powershell
python -m pytest -v
```

## 3. Compatibilidad con unittest

El comando solicitado originalmente continúa disponible:

```powershell
python -m unittest tests/test_sistema.py
```

Resultado esperado:

```text
Ran 15 tests
OK
```

Este comando sólo ejecuta `tests/test_sistema.py`; no incluye todos los casos modernos de seguridad, citas, importación, pestañas o interfaz de receta. La validación completa debe realizarse con `pytest`.

## 4. Controles opcionales de calidad y seguridad

```powershell
python -m ruff check app tests run.py seed_admin.py
python -m bandit -q -r app run.py seed_admin.py -x app/static,app/templates
python -m pip_audit -r requirements.txt
```

## 5. Consideraciones

- Las pruebas usan SQLite en memoria y datos sintéticos; no modifican `instance/pacientes.db`.
- Ejecuta los comandos desde la raíz del proyecto.
- No uses `python run.py` al mismo tiempo que las pruebas si estás modificando archivos del proyecto.
- Si aparece `No module named pytest`, instala `requirements-dev.txt` dentro del mismo entorno virtual.
- Desde la versión 1.3.1, las pruebas de migración liberan explícitamente SQLAlchemy antes de borrar sus bases temporales; esto evita `WinError 32` en Windows/Python 3.13.
- Si `WinError 32` persiste con otro archivo, cierra `python run.py`, visores de SQLite y procesos que mantengan abierta esa ruta.
- Si una actualización se descomprimió sobre una carpeta anterior, ejecuta `python scripts\cleanup_project.py`. Windows no elimina por sí mismo archivos que ya no forman parte del ZIP, como el antiguo `app/static/img/logo.svg`.
- La prueba del icono valida que las plantillas usan `logo.png` y la compilación usa `logo.ico`; un archivo no referenciado que haya quedado de una versión anterior no cambia la interfaz. La utilidad de limpieza permite retirarlo físicamente.
- Si una prueba falla, conserva la salida completa desde la primera línea `FAILURES` hasta el resumen final para diagnosticarla.
