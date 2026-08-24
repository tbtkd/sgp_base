# Backend del Sistema Clínico

## Stack

- Flask 3.1 y Blueprints.
- Flask-Login para sesiones.
- Flask-WTF para CSRF.
- Flask-SQLAlchemy sobre SQLite.
- OpenPyXL y DefusedXML para XLSX.
- Waitress ligado a `127.0.0.1`.

## Blueprints

- `auth`: bootstrap, login/logout, usuarios, cambio/restablecimiento de contraseña y auditoría.
- `main`: dashboard y seguimiento.
- `pacientes`: pacientes, citas, pagos e importación.
- `historial_clinico`: expediente, limitado a `admin/medico`.
- `valoracion`: consultas clínicas, limitado a `admin/medico`.
- `recetas`: emisión de receta ordinaria por Medicina/Odontología e impresión clínica para `admin/medico`.
- `plantillas`: mensajes, limitado a `admin/medico`.

## Solicitudes y transacciones

1. Se genera un `request_id`.
2. Se valida sesión, estado y rol.
3. CSRF protege métodos mutables.
4. `validators.py` normaliza y valida.
5. La operación y su evento de auditoría se confirman en una sola transacción.
6. Errores internos se registran, pero no se exponen.
7. Se añaden cabeceras de seguridad y no-cache.

## Agenda rápida

`GET/POST /pacientes/agendar-cita` implementa la acción del KPI Citas de hoy. El GET sólo lista pacientes activos y construye un resumen de 21 días mediante una consulta acotada. `GET /pacientes/disponibilidad_citas` devuelve 21 horarios diarios con estado explícito y sin información de pacientes.

El POST no confía en el calendario del navegador: valida el identificador, confirma que el paciente siga activo, aplica los validadores comunes de fecha/hora/motivo, limita la anticipación a dos años, impide sobrescribir una cita programada y consulta nuevamente el conflicto del bloque. En el despliegue local actual, la validación final y el `commit` se serializan con el mismo bloqueo de escritura usado por las rutas previas de agendamiento. La auditoría registra `CREAR_CITA` y el origen `kpi_dashboard`, sin guardar el motivo.

## Perfiles profesionales

El rol controla permisos (`admin`, `medico`, `recepcion`) y `perfil_profesional` describe el área de atención (`medico_general`, `dentista`, `nutricion`). Sólo `nutricion` puede enviar campos antropométricos o importar el formato XLSX; ocultarlos en HTML no es suficiente y el servidor rechaza intentos forjados.

Cada consulta nueva guarda `profesional_id` y una instantánea del nombre, perfil y cédula. La impresión usa la instantánea, no al usuario que abre posteriormente la nota.

La emisión de receta vuelve a verificar en servidor que el usuario sea de Medicina general u Odontología, que el paciente siga activo y que existan cédula/domicilio profesional. `prescription_payload()` exige confirmaciones de competencia, alcance ordinario y firma, valida hasta 10 medicamentos estructurados y rechaza filas exactamente duplicadas. `Receta` conserva instantáneas y no expone rutas de edición/eliminación: las correcciones crean un folio de sustitución, mientras que los documentos adicionales mantienen vigencia propia.

Cada cambio o restablecimiento de contraseña incrementa `auth_version`, de modo que las sesiones y cookies de recuerdo anteriores dejan de ser válidas. El administrador debe reautenticarse para generar una credencial temporal. `run.py --reset-password` constituye la vía de contingencia local y sólo opera sobre administradores.

## Datos

`app/db.py` resuelve la ruta persistente, crea un respaldo consistente y ejecuta migraciones aditivas seguras. Para retirar la antigua unicidad de una receta por consulta existe una migración específica, transaccional y verificada que preserva filas e índices. El respaldo rota a 10 copias. Los cambios estructurales futuros requieren scripts versionados y una restauración probada.
