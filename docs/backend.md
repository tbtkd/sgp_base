# Backend del Sistema Clínico

## Stack

- Flask 3.1 y Blueprints.
- Flask-Login para sesiones.
- Flask-WTF para CSRF.
- Flask-SQLAlchemy sobre SQLite.
- OpenPyXL y DefusedXML para XLSX.
- Waitress ligado a `127.0.0.1`.

## Blueprints

- `auth`: bootstrap, login/logout, usuarios, cambio/restablecimiento de contraseña, auditoría y administración de respaldos.
- `main`: dashboard y seguimiento.
- `pacientes`: pacientes, citas, alta contextual de pagos e importación.
- `pagos`: listado global, agregados filtrados y cancelación administrativa.
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
7. Si una auditoría exitosa marcó una mutación crítica, se crea una copia SQLite verificada.
8. Se añaden cabeceras de seguridad, CSP con nonce y no-cache.

## Agenda rápida y operativa

`GET/POST /pacientes/agendar-cita` implementa la acción del KPI Citas de hoy. El GET no consulta ni renderiza el padrón completo; únicamente resuelve un paciente activo cuando llega un identificador ya seleccionado y construye el resumen de 21 días. `GET /pacientes/buscar_para_cita` exige autenticación, normaliza una búsqueda de 2–100 caracteres, consulta nombre/apellidos/expediente/teléfono/correo sin distinguir mayúsculas o acentos, acepta fragmentos por término y devuelve hasta ocho coincidencias activas sin datos clínicos. La cita programada, cuando existe, se limita a fecha y hora. `GET /pacientes/disponibilidad_citas` devuelve 21 horarios diarios con estado explícito y sin información de pacientes. Ambas respuestas JSON se marcan como `no-store`.

El POST no confía en el calendario del navegador: valida el identificador, confirma que el paciente siga activo, aplica los validadores comunes de fecha/hora/motivo, limita la anticipación a dos años, impide sobrescribir una cita programada y consulta nuevamente el conflicto del bloque. En el despliegue local actual, la validación final y el `commit` se serializan con el mismo bloqueo de escritura usado por las rutas previas de agendamiento. La auditoría registra `CREAR_CITA` y el origen `kpi_dashboard` o `agenda`, sin guardar el motivo.

`GET /agenda` agrupa citas por día o semana, calcula conteos por estado y limita el motivo clínico a `admin/medico`. Recepción recibe sólo los datos administrativos necesarios. `GET/POST /agenda/citas/<id>/reagendar` conserva paciente e ID, excluye temporalmente ese único bloque al consultar disponibilidad y revalida el conflicto dentro del bloqueo antes del `commit`.

El endpoint de estado acepta únicamente transiciones desde `Programada` hacia `Atendida`, `No Asistió` o `Cancelada`. Las dos primeras requieren que el horario ya haya ocurrido; Cancelada exige motivo. Los estados terminales no se reabren. Éxitos y denegaciones generan `CAMBIAR_ESTADO_CITA` sin copiar el texto completo de la observación.

## Perfiles profesionales

El rol controla permisos (`admin`, `medico`, `recepcion`) y `perfil_profesional` describe el área de atención (`medico_general`, `dentista`, `nutricion`). Sólo `nutricion` puede enviar campos antropométricos o importar el formato XLSX; ocultarlos en HTML no es suficiente y el servidor rechaza intentos forjados.

Cada consulta nueva guarda `profesional_id` y una instantánea del nombre, perfil y cédula. La impresión usa la instantánea, no al usuario que abre posteriormente la nota.

La emisión de receta vuelve a verificar en servidor que el usuario sea de Medicina general u Odontología, que el paciente siga activo y que existan cédula/domicilio profesional. `prescription_payload()` exige confirmaciones de competencia, alcance ordinario y firma, valida hasta 10 medicamentos estructurados y rechaza filas exactamente duplicadas. `Receta` conserva instantáneas y no expone rutas de edición/eliminación: las correcciones crean un folio de sustitución, mientras que los documentos adicionales mantienen vigencia propia.

Cada cambio o restablecimiento de contraseña y cada modificación de rol/estado incrementa `auth_version`, de modo que las sesiones y cookies de recuerdo anteriores dejan de ser válidas. El administrador debe reautenticarse para generar una credencial temporal. Una cuenta administrativa no puede cambiar su propio rol ni estado; tampoco puede retirarse el último administrador activo. `run.py --reset-password` constituye la vía de contingencia local para una cuenta que aún es administradora. `run.py --recover-admin` sólo funciona cuando `active_admin_count()` es cero y promueve/reactiva una cuenta existente con contraseña temporal y auditoría.

## Datos

`app/db.py` resuelve la ruta persistente, crea respaldos consistentes, valida bases en modo lectura y restaura mediante archivo temporal y reemplazo atómico. Para retirar la antigua unicidad de una receta por consulta, normalizar turnos y reconstruir pagos 1.10.0 existen migraciones específicas, transaccionales y verificadas que preservan filas e índices. El respaldo rota a 10 copias y desde 1.10.1 se ejecuta al arrancar, después de mutaciones críticas y a solicitud administrativa.

Las rutas `/administracion/respaldos` exigen Administración. El nombre se valida con una expresión cerrada y debe resolver dentro de `backups/`; no hay carga arbitraria. La restauración exige CSRF, contraseña actual y `RESTAURAR`, verifica `integrity_check` y tablas mínimas, crea una copia previa, libera conexiones SQLAlchemy, reemplaza la base y cierra la sesión.

## Pagos operativos

`POST /pacientes/<id>/pago` utiliza `payment_payload()`, convierte el importe a centavos, valida una cita opcional del mismo paciente y delega la construcción a `Pago.crear()`. El pago recibe folio, moneda MXN, UUID v4 de operación y usuario. `operation_key` posee unicidad de base: un segundo POST del mismo formulario no inserta otra fila y genera `RECHAZAR_PAGO_DUPLICADO`.

`GET /pagos/` requiere rol Administración o Recepción. La consulta acepta paciente/folio/concepto, fechas, método, estado y página; normaliza Unicode, elimina diferencias de mayúsculas/acentos y divide el texto en fragmentos, de modo que nombre y apellidos pueden coincidir en columnas separadas. Cada fragmento usa parámetros y trata comodines aportados por el usuario como texto literal. Limita el rango a 366 días y pagina 25 filas. `SUM` opera sólo sobre `monto_centavos` con estado `vigente`. `POST /pagos/<id>/cancelar` requiere Administración, motivo de 5–500 caracteres y conserva la fila original. El destino de retorno acepta exclusivamente rutas internas de Pagos/Pacientes; añade un ancla al movimiento y sustituye filtros incompatibles por el folio cancelado.

La relación `cita_id` es opcional y nunca se infiere por la sola existencia de una cita: el operador selecciona el evento que originó el cobro. `metodo_pago` alimenta el desglose operativo y no contiene ninguna decisión de facturación.

Administración recibe además agrupación `dia|mes`. `GET /pagos/exportar.csv` reaplica los filtros y `GET /pagos/paciente/<id>/historial.csv` genera el historial individual. `_export_rows()` limita ambas salidas a 10,000 filas; `_csv_safe()` neutraliza `=`, `+`, `-`, `@`, tabulador y retorno de carro al inicio de una celda. La respuesta usa BOM UTF-8, `Cache-Control: no-store` y genera `EXPORTAR_PAGOS`.

`payments_v110` reconstruye `pagos` antes de la migración aditiva general. Las filas válidas se convierten mediante `Decimal`; las incompletas pasan a `requiere_revision`. Ese estado sólo puede originarse en esta conservación de datos anteriores o en la carga demo; `payment_payload()` rechaza altas actuales incompletas. No existe una mutación de aprobación: Administración cancela el registro preservado y crea otro movimiento si la evidencia permite reconstruir el cobro. La migración cambia Paciente a `ON DELETE RESTRICT`, usa `SET NULL` para usuarios/cita, recrea unicidad e índices y ejecuta `foreign_key_check`/`integrity_check`.

## Turno diario y orden de receta

La consulta usa `(fecha, numero_cita)` como clave única operativa. `numero_cita` se calcula en el servidor dentro de `ValoracionAntropometrica.bloqueo_numeracion_diaria()`; el valor del formulario se reemplaza antes de validar/persistir. El endpoint de proyección es autenticado, valida fecha no futura y responde `no-store`. La importación XLSX reserva de igual forma una secuencia por cada fecha presente.

La migración `consultation_daily_sequence` reasigna filas legadas por `fecha`, `created_at` e `id`, crea un índice único y ejecuta `integrity_check`. No elimina ni fusiona consultas. Los huecos posteriores por eliminación o cambio de fecha se conservan para no mutar referencias históricas.

Las recetas reciben `orden_medicamento[]`. `prescription_payload()` exige una secuencia única y consecutiva, reordena las columnas paralelas antes de construir cada medicamento y mantiene compatibilidad con clientes 1.7.1 que no envían el nuevo campo.

El índice `GET /valoraciones/` selecciona una sola nota reciente por paciente mediante una ventana SQL ordenada por fecha, turno e ID. Acepta `q`, `orden=fecha_desc|fecha_asc` y `page`; filtra y pagina en servidor. `?origen=recetas` conserva el listado completo de consultas para mantener accesibles folios históricos.

`POST /pacientes/<id>/cargar-excel` exige además el perfil profesional `nutricion`. La interfaz no renderiza sus controles para otros perfiles y un intento directo se deniega y audita antes de resolver el identificador del paciente.
