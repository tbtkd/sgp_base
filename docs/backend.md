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
- `agenda`: vista operativa Día/Semana y reagenda; comparte validaciones de citas con `pacientes`.
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

## Agenda rápida y operativa

`GET/POST /pacientes/agendar-cita` implementa la acción del KPI Citas de hoy. El GET no consulta ni renderiza el padrón completo; únicamente resuelve un paciente activo cuando llega un identificador ya seleccionado y construye el resumen de 21 días. `GET /pacientes/buscar_para_cita` exige autenticación, normaliza una búsqueda de 2–100 caracteres, consulta nombre/expediente/teléfono y devuelve hasta ocho coincidencias activas sin datos clínicos. La cita programada, cuando existe, se limita a fecha y hora. `GET /pacientes/disponibilidad_citas` devuelve 21 horarios diarios con estado explícito y sin información de pacientes. Ambas respuestas JSON se marcan como `no-store`.

El POST no confía en el calendario del navegador: valida el identificador, confirma que el paciente siga activo, aplica los validadores comunes de fecha/hora/motivo, limita la anticipación a dos años, impide sobrescribir una cita programada y consulta nuevamente el conflicto del bloque. En el despliegue local actual, la validación final y el `commit` se serializan con el mismo bloqueo de escritura usado por las rutas previas de agendamiento. La auditoría registra `CREAR_CITA` y el origen `kpi_dashboard` o `agenda`, sin guardar el motivo.

`GET /agenda` agrupa citas por día o semana, calcula conteos por estado y limita el motivo clínico a `admin/medico`. Recepción recibe sólo los datos administrativos necesarios. `GET/POST /agenda/citas/<id>/reagendar` conserva paciente e ID, excluye temporalmente ese único bloque al consultar disponibilidad y revalida el conflicto dentro del bloqueo antes del `commit`.

El endpoint de estado acepta únicamente transiciones desde `Programada` hacia `Atendida`, `No Asistió` o `Cancelada`. Las dos primeras requieren que el horario ya haya ocurrido; Cancelada exige motivo. Los estados terminales no se reabren. Éxitos y denegaciones generan `CAMBIAR_ESTADO_CITA` sin copiar el texto completo de la observación.

## Perfiles profesionales

El rol controla permisos (`admin`, `medico`, `recepcion`) y `perfil_profesional` describe el área de atención (`medico_general`, `dentista`, `nutricion`). Sólo `nutricion` puede enviar campos antropométricos o importar el formato XLSX; ocultarlos en HTML no es suficiente y el servidor rechaza intentos forjados.

Cada consulta nueva guarda `profesional_id` y una instantánea del nombre, perfil y cédula. La impresión usa la instantánea, no al usuario que abre posteriormente la nota.

La emisión de receta vuelve a verificar en servidor que el usuario sea de Medicina general u Odontología, que el paciente siga activo y que existan cédula/domicilio profesional. `prescription_payload()` exige confirmaciones de competencia, alcance ordinario y firma, valida hasta 10 medicamentos estructurados y rechaza filas exactamente duplicadas. `Receta` conserva instantáneas y no expone rutas de edición/eliminación: las correcciones crean un folio de sustitución, mientras que los documentos adicionales mantienen vigencia propia.

Cada cambio o restablecimiento de contraseña incrementa `auth_version`, de modo que las sesiones y cookies de recuerdo anteriores dejan de ser válidas. El administrador debe reautenticarse para generar una credencial temporal. `run.py --reset-password` constituye la vía de contingencia local y sólo opera sobre administradores.

## Datos

`app/db.py` resuelve la ruta persistente, crea un respaldo consistente y ejecuta migraciones aditivas seguras. Para retirar la antigua unicidad de una receta por consulta existe una migración específica, transaccional y verificada que preserva filas e índices. El respaldo rota a 10 copias. Los cambios estructurales futuros requieren scripts versionados y una restauración probada.

## Turno diario y orden de receta

La consulta usa `(fecha, numero_cita)` como clave única operativa. `numero_cita` se calcula en el servidor dentro de `ValoracionAntropometrica.bloqueo_numeracion_diaria()`; el valor del formulario se reemplaza antes de validar/persistir. El endpoint de proyección es autenticado, valida fecha no futura y responde `no-store`. La importación XLSX reserva de igual forma una secuencia por cada fecha presente.

La migración `consultation_daily_sequence` reasigna filas legadas por `fecha`, `created_at` e `id`, crea un índice único y ejecuta `integrity_check`. No elimina ni fusiona consultas. Los huecos posteriores por eliminación o cambio de fecha se conservan para no mutar referencias históricas.

Las recetas reciben `orden_medicamento[]`. `prescription_payload()` exige una secuencia única y consecutiva, reordena las columnas paralelas antes de construir cada medicamento y mantiene compatibilidad con clientes 1.7.1 que no envían el nuevo campo.
