# Sistema de Expediente Clínico y Gestión de Pacientes

Versión **1.6.6**. Aplicación local para consultorios médicos, dentales, nutricionales y otros servicios de salud. Generaliza el expediente, las consultas, los signos vitales, las citas, los pagos, la receta ordinaria y el seguimiento por WhatsApp.

## Funcionalidad

- Expediente con datos personales, ocupación, dirección y contacto de emergencia.
- Antecedentes patológicos, heredofamiliares, alergias, medicación, hábitos y notas.
- Consultas con síntomas, signos vitales, diagnóstico, plan e indicaciones clínicas.
- Receta médica ordinaria independiente para Medicina/Odontología, con folios originales, adicionales y sustituciones trazables.
- Antropometría y pliegues opcionales, habilitados exclusivamente para perfiles de Nutrición.
- Citas con motivo y estado; pagos con monto, concepto y método.
- Usuarios con roles `admin`, `medico` y `recepcion`, separados de su perfil profesional.
- Perfiles clínicos: Medicina general, Odontología/Dentista y Nutrición.
- Nombre, perfil y cédula del autor conservados dentro de cada consulta nueva.
- Auditoría administrativa de accesos y operaciones críticas.
- Enlaces directos a WhatsApp e impresión limpia de notas y recetas como PDF.
- Shell clínico responsive con búsqueda global, sede local, notificaciones vacías explícitas, breadcrumb y tema claro/oscuro persistente.
- Identidad y menú de cuenta concentrados al pie del sidebar; el botón `...` despliega datos profesionales, cambio de contraseña y cierre de sesión.
- Menú de cuenta cerrado de forma nativa al cargar, con apertura explícita y cierre por Escape o clic exterior.
- Un solo icono institucional para navegador, interfaz y ejecutable Windows.
- Cambio propio de contraseña, restablecimiento administrativo y recuperación local para el administrador del equipo.
- Pestañas clínicas locales, estados vacíos accionables y KPIs coherentes.
- Dashboard operativo con agenda, gráfica local, pacientes recientes, pendientes y actividad basada exclusivamente en datos persistidos; Próximas citas y Acompañamiento Intermedio comparten una fila adaptable, sin duplicar alertas ni mostrar ingresos.
- Acciones rápidas limitadas a Nuevo paciente, Agendar cita y Nueva consulta; Recetas y Expedientes se consultan desde el sidebar para evitar duplicidad.
- Navegación que diferencia enlaces operativos, acceso contextual funcional a recetas, grupo desplegable de Administración y módulos planificados sin crear rutas ficticias.
- Importación XLSX defensiva para expedientes antropométricos históricos.

## Instalación

Requiere Python 3.10 o posterior.

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

En Linux/macOS, la activación es `source .venv/bin/activate`.

### Actualización de una instalación existente

La opción más segura es descomprimir cada versión en una carpeta nueva y copiar únicamente `instance/` y `backups/` después de conservar un respaldo. Al extraer un ZIP sobre una carpeta anterior, Windows reemplaza archivos incluidos pero no elimina archivos que dejaron de formar parte del proyecto.

Si actualizas sobre la misma carpeta, ejecuta después:

```powershell
python scripts\cleanup_project.py
```

La utilidad elimina únicamente `app/static/img/logo.svg`, cachés de Python y cachés de herramientas conocidas. No recorre ni modifica `.venv`, `instance`, `backups`, bases de datos, secretos o registros. También se ejecuta automáticamente antes de construir el ejecutable.

## Inicialización y ejecución

Crear el primer administrador:

```bash
python seed_admin.py
```

Después, iniciar el servidor local:

```bash
python run.py
```

La aplicación escucha exclusivamente en `http://127.0.0.1:5000/`. También se conserva el alta inicial de un solo uso desde `/setup` cuando no existe ningún usuario.

Si se olvida la contraseña, otro administrador puede generar una credencial temporal desde **Gestión de usuarios**. Cuando ningún administrador puede ingresar, en el mismo equipo se utiliza:

```bash
python run.py --reset-password NOMBRE_USUARIO
```

El ejecutable admite `SistemaPacientes.exe --reset-password NOMBRE_USUARIO`. La recuperación local sólo permite cuentas administradoras, invalida sesiones anteriores y obliga a cambiar nuevamente la contraseña después del login.

Consulta el procedimiento y su modelo de seguridad en [docs/RECUPERACION_ACCESO.md](docs/RECUPERACION_ACCESO.md).

Si el arranque falla, la consola muestra la causa concreta y la ruta de `instance/logs/startup.log`. En PowerShell también puede consultarse el registro de Flask con:

```powershell
Get-Content .\instance\logs\app.log -Tail 80
Get-Content .\instance\logs\startup.log -Tail 80
```

Para una inicialización automatizada se admiten `SGPN_ADMIN_USERNAME`, `SGPN_ADMIN_PASSWORD`, `SGPN_ADMIN_NAME`, `SGPN_ADMIN_LASTNAME`, `SGPN_ADMIN_MATERNAL` y `SGPN_ADMIN_EMAIL`.

## Persistencia y respaldos

- Ejecución normal: `instance/pacientes.db` dentro del proyecto.
- PyInstaller: `instance/pacientes.db` junto al ejecutable, nunca dentro de `_MEIPASS`.
- Ruta personalizada: variable `SGPN_DATA_DIR`.
- Secreto de sesión: `instance/.secret_key`, generado con 32 bytes criptográficos.
- Respaldos: `backups/pacientes_backup_YYYYMMDD_HHMMSS_microsegundos.db`.
- Retención: últimas 10 copias verificadas mediante `PRAGMA integrity_check`.

Si una base muy antigua no contiene el correo de sus usuarios, la migración conserva las cuentas y asigna valores únicos `usuario-migrado-<id>@local.invalid`. Son marcadores locales que no reciben mensajes y deben reemplazarse desde el panel **Usuarios**.

El directorio que contiene el ejecutable debe ser escribible. Los datos, respaldos y secretos están excluidos del paquete y del control de versiones.

## Impresión de notas clínicas y recetas

Desde el detalle de una consulta selecciona **Imprimir nota / PDF**. La aplicación abre una hoja A4 independiente; después pulsa **Imprimir / guardar PDF**, elige **Guardar como PDF** y desactiva **Encabezados y pies de página** en las opciones del navegador. La nota imprimible no depende de Tailwind, Alpine ni recursos CDN.

La nota clínica y la receta son documentos distintos. Cuando el usuario tiene perfil de Medicina general u Odontología, cédula y domicilio profesional, el detalle ofrece **Generar receta**. El formulario exige por medicamento denominación genérica, presentación, dosis, vía, frecuencia y duración; la salida conserva una instantánea del paciente y del profesional.

La receta implementada es únicamente **ordinaria**: debe revisarse, imprimirse y llevar firma autógrafa. Una receta emitida no se edita; una corrección crea un folio de sustitución y marca el anterior como no vigente. Desde una misma consulta pueden emitirse recetas adicionales con folio independiente. No admite estupefacientes, psicotrópicos ni otros flujos sujetos a receta especial. Consulta [docs/RECETA_MEDICA_MEXICO.md](docs/RECETA_MEDICA_MEXICO.md) antes de usarla con datos reales.

## Roles

| Función | admin | medico | recepcion |
| --- | --- | --- | --- |
| Pacientes, citas y pagos | Sí | Sí | Sí |
| Expediente clínico | Sí | Sí | No |
| Consultas, diagnóstico e indicaciones | Sí | Sí | No |
| Emitir receta ordinaria | Sólo con perfil Medicina/Odontología y datos completos | Sólo con perfil Medicina/Odontología y datos completos | No |
| Antropometría e importación | Sólo con perfil Nutrición | Sólo con perfil Nutrición | No |
| Usuarios y auditoría | Sí | No | No |

## Pruebas y calidad

`pytest` es el único comando oficial y también descubre los casos heredados escritos con `unittest`, evitando ejecutar dos veces la misma cobertura:

```bash
python -m pytest -q
ruff check app tests run.py seed_admin.py
bandit -q -r app run.py seed_admin.py -x app/static,app/templates
pip-audit -r requirements.txt
```

La aceptación funcional incluye 68 casos, de los cuales 15 también pueden ejecutarse directamente con `unittest`; el detalle se encuentra en [docs/TEST_MATRIX.md](docs/TEST_MATRIX.md). Las instrucciones para PowerShell están en [docs/EJECUCION_PRUEBAS.md](docs/EJECUCION_PRUEBAS.md). El roadmap funcional está en [docs/ROADMAP_MODULOS_UI_CITAS.md](docs/ROADMAP_MODULOS_UI_CITAS.md), la base histórica del panel en [docs/DASHBOARD_VISUAL_1_6_3.md](docs/DASHBOARD_VISUAL_1_6_3.md), el shell base en [docs/SHELL_NAVEGACION_1_6_4.md](docs/SHELL_NAVEGACION_1_6_4.md) y el ajuste vigente en [docs/AJUSTE_DASHBOARD_NAVEGACION_1_6_6.md](docs/AJUSTE_DASHBOARD_NAVEGACION_1_6_6.md).

## Compilación para Windows

```bat
pip install -r requirements-build.txt
build_exe.bat
```

El ejecutable se genera sin base de datos, secretos, registros ni respaldos. `PyInstaller` se mantiene como dependencia de compilación, no de ejecución.

## Seguridad y límites

Consulta [SECURITY_REVIEW.md](SECURITY_REVIEW.md) antes de utilizar datos reales. Esta versión está pensada para una estación local controlada; para despliegue en red aún se requiere cifrado en reposo, HTTPS mediante proxy local confiable, gestión formal de respaldos y una evaluación de privacidad aplicable al consultorio.
