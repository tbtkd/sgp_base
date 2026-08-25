# Revisión de seguridad y generalización clínica

## Dictamen

La versión 1.10.1 es adecuada para pruebas funcionales y para un piloto en una estación local controlada. En el alcance de la aplicación cumple el nivel técnico mínimo definido: autenticación, roles, CSRF, validación, sesiones revocables, auditoría, frontend autocontenido, CSP estricta y restauración verificada. No debe exponerse directamente a Internet ni considerarse una plataforma clínica multiusuario de red.

### Nivel mínimo para utilizar información real en una estación local

La evaluación de esta entrega deja fuera los requisitos físicos y del sistema operativo del equipo. El dictamen es **mínimo técnico de aplicación cumplido para piloto local controlado**. No incluye una prueba de penetración, una certificación, cifrado en reposo ni la evaluación legal/organizacional necesaria para decidir el uso de información clínica real.

## Controles implementados

### Identidad y acceso

- Alta inicial sin contraseña predeterminada mediante `/setup` o `seed_admin.py`.
- Contraseñas con Scrypt y política de 12–128 caracteres.
- Roles permitidos: `admin`, `medico`, `recepcion`.
- Decoradores de autenticación/RBAC aplicados en backend.
- Protección contra desactivar la propia cuenta o eliminar el último administrador.
- Cinco fallos bloquean la cuenta y la IP durante cinco minutos.
- Comparación con hash ficticio para usuarios inexistentes y mensajes de acceso genéricos.
- Cambio propio con contraseña actual, restablecimiento administrativo con reautenticación y recuperación local limitada a administradores.
- Contraseñas temporales mostradas una sola vez, cambio obligatorio e invalidación de sesiones mediante `auth_version`.

### Sesión, red y navegador

- Secreto de 32 bytes persistido fuera del código en `.secret_key`.
- Cookies `HttpOnly`, `SameSite=Lax`, sesiones de 30 minutos y recordatorio de ocho horas.
- CSRF en formularios, cierre de sesión y solicitudes AJAX mutables.
- Límite global de petición de 16 MB y límite XLSX específico de 5 MB.
- Escucha exclusiva en `127.0.0.1` mediante Waitress.
- CSP por respuesta sin `unsafe-inline` ni CDN, `script-src-attr/style-src-attr 'none'`, `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy: no-referrer`, políticas de permisos y no-cache para HTML.

### Validaciones

| Área | Validaciones de servidor |
| --- | --- |
| Paciente | nombres normalizados, género enumerado, nacimiento ≥1900 y no futuro, teléfono de 10 dígitos, correo, longitudes, contacto de emergencia |
| Usuario | usuario normalizado, correo único, rol/estado enumerados, contraseña fuerte |
| Profesional | perfil enumerado, cédula numérica de 5–12 dígitos, establecimiento y domicilio con longitudes limitadas |
| Consulta | fecha no futura, motivo obligatorio, textos limitados, IMC recalculado y turno diario ignorado del cliente/asignado en servidor |
| Signos vitales | TA estructurada, FC 30–250, FR 5–80, temperatura 30–45, SpO₂ 50–100, peso/estatura positivos |
| Antropometría | todos los campos opcionales; cuando existen se validan como números finitos y con rangos |
| Cita | fecha/hora futura, intervalos permitidos, motivo limitado, horario no duplicado, transiciones terminales y cancelación motivada |
| Pago | importe exacto mayor que cero y hasta 10,000,000 MXN, máximo dos decimales, UUID de operación, concepto, método y cita opcional explícita del mismo paciente |
| Reporte de pagos | sólo Administración, rango máximo de 366 días, catálogo de agrupación, máximo 10,000 filas, UTF-8 y neutralización de prefijos de fórmula CSV |
| Receta ordinaria | emisor autorizado, paciente activo, cédula/domicilio, máximo 10 medicamentos, filas completas/no duplicadas, orden exacto `1..n` y confirmaciones de competencia, alcance y firma |
| XLSX | extensión, tamaño, ZIP válido, rutas internas, ratio de compresión, componentes, dimensiones, filas y transacción atómica |

### Trazabilidad y mensajes

- Eventos críticos normalizados (`LOGIN`, `LOGOUT`, `CREAR_PACIENTE`, `CREAR_CONSULTA`, `REGISTRAR_PAGO`, etc.).
- Pagos registra también `RECHAZAR_PAGO_DUPLICADO`, `CANCELAR_PAGO` y `EXPORTAR_PAGOS`; la auditoría conserva alcance, filas, folio/IDs/resultado sin duplicar el importe completo.
- Registros con usuario, módulo, acción, descripción, entidad, IP, resultado y `request_id`.
- Vista `/auditoria` exclusiva de administradores, con filtros y límite de 500 resultados.
- Metadatos limitados y sin almacenar contraseñas, recetas completas o datos clínicos en el log técnico.
- Excepciones internas y SQL no se devuelven al usuario.
- Mensajes `success`, `error`, `warning` e `info` con iconos y cierre.
- El formulario de citas permanece cerrado al cargar, no depende de Alpine/CDN y cancela las consultas de disponibilidad al cerrarse.
- Los horarios tienen etiquetas HTML reales, contraste explícito y revalidación autoritativa en el servidor.
- La agenda rápida sólo acepta pacientes activos, limita fechas a dos años, rechaza citas previas y revalida el horario dentro de un bloqueo de escritura del proceso local.
- La agenda rápida no entrega el padrón en el HTML: su búsqueda autenticada exige al menos dos caracteres, limita la respuesta a ocho coincidencias, no incluye datos clínicos y conserva sólo nombre, expediente, teléfono, enlace interno y fecha/hora de una cita programada.
- La API visual de disponibilidad exige sesión, no entrega datos personales y marca su respuesta como `no-store`.
- La Agenda dedicada reutiliza las validaciones existentes; Recepción sólo recibe identidad/horario/estado y no el motivo clínico ni acciones de consulta.
- La reagenda conserva el ID, valida paciente activo, excluye sólo el espacio editado y vuelve a comprobar conflictos dentro del bloqueo.
- Las citas futuras no pueden cerrarse como atendidas o no asistidas; una cita terminal no puede reabrirse. Los rechazos se auditan como `denied`.
- Las pestañas de consulta y panel funcionan con JavaScript local, sin depender de Alpine/CDN.
- El menú de cuenta inicia cerrado mediante HTML nativo y usa JavaScript local; si el script falla, el detalle permanece oculto y no expone información por defecto.
- El sidebar móvil, selector de sede y notificaciones usan estados `hidden`/ARIA y controles locales; no existe navegación hacia módulos sin autorización o backend.
- La búsqueda global reutiliza la consulta limitada y validada de pacientes; no introduce un endpoint universal que exponga datos clínicos.
- El tema se conserva sólo como preferencia visual en `localStorage`; no almacena identidad, datos clínicos ni credenciales.
- El dashboard no calcula ni presenta ingresos; las métricas operativas proceden de consultas acotadas a SQLite y respetan permisos clínicos.
- Recepción no recibe el contenido de pendientes clínicos, actividad de consultas ni acciones para iniciar atención.
- El seguimiento **Sin consulta reciente** no se consulta ni se entrega a Medicina general u Odontología; sólo se incluye para el perfil profesional de Nutrición.
- La vista de impresión es una ruta clínica autenticada, aislada del shell y sin recursos externos.
- El perfil profesional se valida por separado del rol de acceso.
- La antropometría se oculta y se rechaza en servidor salvo para perfiles de Nutrición.
- La importación XLSX no renderiza botón ni modales fuera de Nutrición; una solicitud manipulada se rechaza antes de resolver el paciente y se audita como `denied`.
- El índice de Consultas expone sólo paciente, expediente y fecha de última nota; búsqueda, selección determinista, orden y paginación se resuelven en SQLite con parámetros permitidos.
- Nombre, perfil y cédula del autor se conservan como instantánea; la impresión no usa la identidad del usuario que sólo consulta.
- La nota clínica no se presenta como receta; las indicaciones nutricionales nunca se rotulan como prescripción médica.
- La receta ordinaria requiere Medicina/Odontología, cédula y domicilio; Nutrición y Recepción son rechazados por el servidor.
- La emisión exige confirmar competencia y ausencia de medicamentos sujetos a receta especial.
- La receta guarda instantáneas inmutables y la bitácora omite nombres de medicamentos, dosis y observaciones.
- Originales, adicionales y sustituciones usan folio/versiones independientes; sustituir exige motivo y nunca modifica el documento anterior.
- Un folio sustituido imprime “NO ENTREGAR NI SURTIR” y enlaza al reemplazo.
- La consulta asociada no puede eliminarse una vez emitida cualquier receta.
- Los restablecimientos registran sólo IDs, método y resultado; la credencial nunca se escribe en bitácora o log técnico.
- El turno diario mostrado por JavaScript es orientativo, se entrega sin caché y nunca se acepta como autoridad; el servidor lo recalcula bajo bloqueo y la base rechaza duplicados por fecha.
- La bitácora de consulta conserva fecha y turno asignado, pero no diagnósticos, síntomas o contenido de la receta.
- El orden de medicamentos se valida como una secuencia única y consecutiva antes de persistir; no se confía en la posición visual ni en valores manipulados del navegador.
- La compactación de la receta es exclusivamente de presentación: conserva todos los campos farmacológicos obligatorios, omite sólo opcionales vacíos y mantiene cada medicamento unido al paginar.
- La simplificación de la firma no elimina identidad: nombre, perfil, cédula, domicilio y fecha permanecen impresos en el encabezado, mientras la firma autógrafa conserva una línea única claramente rotulada.
- La supresión de metadatos del navegador se limita a CSS y al estado temporal del título; no altera el folio, la ruta autenticada, los snapshots ni el contenido clínico.
- La idempotencia de pagos combina UUID v4 de formulario, restricción única y bloqueo visual; un reintento confirmado no crea una segunda fila.
- La búsqueda por nombre completo se tokeniza y continúa parametrizada por SQLAlchemy; no concatena SQL proporcionado por el usuario.
- Sólo Administración cancela pagos. Recepción consulta el módulo global y Medicina mantiene el acceso contextual, sin elevar permisos de cancelación.
- Los totales financieros usan centavos enteros y excluyen cancelados/filas `requiere_revision`; ninguna suma depende del `Float` legado.
- Cancelar conserva el original y exige motivo; el historial financiero no se elimina en cascada al eliminar un paciente. El retorno se limita a rutas internas de Pagos/Pacientes, descarta origen externo y evita que un filtro incompatible oculte el movimiento cancelado.
- El resumen diario/mensual y los CSV global/individual exigen Administración. Las exportaciones limitan volumen, usan `no-store` y anteponen apóstrofo a celdas con prefijos interpretables como fórmula.

### Persistencia y entrega

- Base `pacientes.db` fuera de `_MEIPASS`.
- Respaldos consistentes mediante `sqlite3.Connection.backup()` y verificación de integridad.
- Retención automática de 10 respaldos.
- Respaldo consistente al arrancar y después de mutaciones críticas aceptadas; los rechazos no generan copia.
- Panel administrativo para crear, verificar y descargar; restauración con reautenticación, frase explícita, copia previa, reemplazo atómico y cierre de sesión.
- Migración aditiva guardada, migraciones transaccionales para recetas, turno diario y pagos 1.10.0, con `foreign_key_check` e `integrity_check`.
- ZIP y compilación excluyen bases, secretos, logs, cachés, entorno virtual y respaldos.
- La limpieza de actualizaciones sólo elimina el SVG, la hoja de sidebar legada no referenciada y cachés conocidas dentro del código; no recorre el entorno virtual ni los directorios de datos.

## Decisiones que no se aplicaron literalmente

No se redujo `requirements.txt` a únicamente Flask y OpenPyXL porque el proyecto utiliza autenticación, ORM y CSRF; hacerlo eliminaría controles de seguridad esenciales. PyInstaller está separado como dependencia de construcción. Tampoco se relajaron las cabeceras `DENY/no-referrer`, ya que ya satisfacen de forma más estricta las cabeceras solicitadas.

## Pendientes antes de producción en red

1. Cifrado en reposo para base y respaldos, con llaves fuera del equipo.
2. HTTPS y terminación TLS confiable si deja de ser exclusivamente localhost.
3. Política formal de consentimiento, acceso, retención, anonimización y eliminación.
4. Aislamiento por consultorio/tenant si varias organizaciones comparten una instalación.
5. Versionado inmutable de notas clínicas y firma/cierre profesional.
6. Revisión legal y clínica según jurisdicción y especialidad.
7. Firma electrónica regulada, si se desea sustituir la firma autógrafa en papel.
8. Flujo independiente para medicamentos controlados o recetas especiales; no reutilizar la receta ordinaria.
9. Definición formal de cargos, adeudos, reembolsos, recibos, conciliación y corte de caja antes de presentar el módulo de pagos como sistema contable.

## Siguiente fase recomendada

El siguiente paso recomendado es **1.11 — cierre y versionado inmutable de notas clínicas**: estados borrador/cerrada, autor y momento de cierre, correcciones mediante addendum trazable y prohibición de sobrescribir una nota firmada. Es el riesgo de integridad clínica más importante que permanece y debe resolverse antes de ampliar Facturación o exponer el sistema en red.

La solicitud de factura, recibos no fiscales y datos fiscales deberá diseñarse después como flujo separado; nunca se inferirá a partir del método de pago.

## Evidencia de verificación

- `python -m unittest tests/test_sistema.py`: 15 pruebas.
- `python -m pytest -q`: 118 pruebas obligatorias aprobadas; un E2E adicional queda disponible con Playwright/Chromium.
- Ruff: sin hallazgos.
- Bandit: sin hallazgos.
- `pip-audit`: sin vulnerabilidades conocidas en las dependencias instaladas; el entorno de verificación usa `pip 26.2.1`.
- Compilación de plantillas y registro de rutas verificados durante la aceptación.
- Arranque local verificado con Waitress y cabeceras de seguridad.

El dictamen vigente sigue siendo **apto para pruebas y piloto local controlado**, no para exposición en red o Internet. Los datos demo prueban controles funcionales, pero no sustituyen una prueba de penetración ni una evaluación legal de privacidad.
