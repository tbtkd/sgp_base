# Matriz de pruebas — versión 1.9.0

## Suite de aceptación (`tests/test_sistema.py`)

| ID | Área | Resultado esperado |
| --- | --- | --- |
| SYS-01 | Secreto | Clave de 64 caracteres hexadecimales, persistente en `.secret_key` |
| SYS-02 | Autenticación | Hash distinto del texto, verificación correcta y login 302 |
| SYS-03 | Validadores | Teléfono, correo y nacimiento válidos; entradas inválidas rechazadas |
| SYS-04 | Pacientes | Alta, lectura, búsqueda, actualización y cambio de estado |
| SYS-05 | Historial | Antecedentes y alergias persistidos |
| SYS-06 | Consulta | Signos vitales, indicaciones e IMC calculado por servidor |
| SYS-07 | Citas/pagos | Motivo, monto, concepto y método persistidos |
| SYS-08 | Auditoría | Acción normalizada, módulo, usuario e IP |
| SYS-09 | Respaldos | Copia legible y rotación exacta a 10 archivos |
| SYS-10 | Acceso | Rutas clínicas redirigen a login |
| SYS-11 | Migración | Columnas nuevas se agregan y los datos previos se conservan |
| SYS-12 | Compatibilidad | `sgpn.db` y `.session_secret` se copian al formato actual |
| SYS-13 | Esquema legado | Campos obligatorios y correos temporales únicos se agregan sin perder usuarios ni pagos |
| SYS-14 | Arranque | La causa aparece en consola y el traceback queda en `startup.log` sin recrear Flask |
| SYS-15 | Receta ordinaria | Medicamento estructurado, snapshot profesional y persistencia relacionada |

Estos 15 casos permanecen por compatibilidad y son recolectados por la suite unificada.

## Citas e interfaz (`tests/test_appointments.py`)

| ID | Control | Cobertura |
| --- | --- | --- |
| CITA-UI-01 | Estado inicial | Modal y advertencia cerrados al cargar el detalle |
| CITA-UI-02 | Contrato local | Cierres, Escape, `pageshow`, cancelación de red y doble envío |
| CITA-SEARCH-01 | Privacidad de búsqueda | La agenda no renderiza el padrón; el endpoint exige sesión, limita resultados y omite datos clínicos |
| CITA-SEARCH-02 | Selección accesible | Combobox/listbox, flechas, Enter, Escape, cancelación y ficha única seleccionada |
| CITA-UI-03 | Horarios | 21 etiquetas literales de 09:00 a 19:00 y estilos de contraste |
| CITA-SEC-01 | Autenticación | Disponibilidad redirige al login sin sesión |
| CITA-API-01 | Disponibilidad | Respuesta ordenada, sin caché y exclusión al reagendar |
| CITA-API-02 | Validación | Fecha inválida devuelve HTTP 400 |
| CITA-CRUD-01 | Alta | Cita futura persistida y evento `CREAR_CITA` |
| CITA-CRUD-02 | Reagenda | Mismo registro actualizado y evento `ACTUALIZAR_CITA` |
| CITA-CRUD-03 | Conflictos | Horario ocupado y fecha pasada no se persisten |
| CITA-KPI-01 | Acceso dedicado | KPI abre agenda rápida, sin agregarla al sidebar ni retirar el modal del detalle |
| CITA-KPI-02 | Calendario visual | 21 fechas y API con 21 bloques disponibles/ocupados/transcurridos |
| CITA-KPI-03 | Alta rápida | Paciente activo, cita y auditoría con origen de Dashboard persistidos |
| CITA-KPI-04 | Protección | Cita previa y horario que dejó de estar libre son rechazados sin sobrescribir datos |
| CITA-KPI-05 | Frontend seguro | DOM local, cancelación de solicitudes, doble envío, ARIA y tema oscuro |
| AGENDA-01 | Ruta operativa | Sidebar abre `/agenda`; autenticación y vistas Día/Semana |
| AGENDA-02 | Privacidad por rol | Recepción no recibe motivo clínico ni acceso para iniciar consulta |
| AGENDA-03 | Alta contextual | Agenda reutiliza la búsqueda/disponibilidad y registra su origen |
| AGENDA-04 | Reagenda | Conserva cita/paciente, excluye su propio espacio y revalida conflictos |
| AGENDA-05 | Citas cerradas | Una cita terminal no puede reagendarse ni volver a Programada |
| AGENDA-06 | Transiciones temporales | Citas futuras no se cierran como Atendida/No Asistió |
| AGENDA-07 | Cancelación | Motivo obligatorio, estado cerrado y auditoría de éxito/denegación |
| AGENDA-08 | Interfaz | Estado local seguro, doble envío, ARIA, responsive y tema oscuro |

Comando oficial único:

```bash
python -m pytest -q
```

## Suite complementaria

| ID | Control | Cobertura |
| --- | --- | --- |
| SEC-01 | CSRF | POST sin token rechazado |
| SEC-02 | Cabeceras | CSP, frame deny, nosniff, cache y request ID |
| SEC-03 | Bloqueo | Cinco fallos bloquean cuenta/IP |
| SEC-04 | Roles | `recepcion` no accede a expediente, consultas ni usuarios |
| SEC-05 | Migración | Una cuenta con correo temporal recibe advertencia al iniciar sesión |
| SEC-06 | Cambio de contraseña | Requiere la credencial actual, aplica política e invalida otras sesiones |
| SEC-07 | Restablecimiento admin | Reautenticación, credencial temporal, cambio obligatorio y auditoría sin secreto |
| SEC-08 | Recuperación local | Limitada a administradores, activa la cuenta y obliga a cambiar contraseña |
| SEC-09 | Ayuda pública | No recibe ni confirma nombres de usuario |
| VAL-01 | Contraseñas | Longitud, composición y datos personales |
| VAL-02 | Consulta | IMC manipulado ignorado y TA/rangos verificados |
| XLS-01 | Importación | Archivo inválido no deja registros parciales |
| XLS-02 | Importación | Libro válido crea una consulta histórica |

## Consistencia de módulos (`tests/test_ui_modules.py`)

| ID | Control | Cobertura |
| --- | --- | --- |
| UI-HIS-01 | Historial | Paciente y campos clínicos visibles, ordenados como Historial Médico, Alimentación y Actividad Física |
| UI-EMPTY-01 | Estados vacíos | Pacientes, historiales y consultas muestran explicación y acción |
| UI-SEARCH-01 | Búsqueda | Teléfono y correo localizan pacientes |
| UI-KPI-01 | Panel | Pacientes, citas de hoy y consultas pendientes coinciden con la base |
| UI-DASH-01 | Dashboard | Los tres KPIs proceden de SQLite y el indicador de ingresos está ausente |
| UI-DASH-02 | Composición | Agenda, gráfica, recientes, pendientes únicos, actividad y acompañamiento visibles |
| UI-DASH-03 | Privacidad por rol | Recepción no recibe pendientes, acciones o actividad clínica |
| UI-TAB-01 | Pestañas | Navegación local, teclado, activación ante campos inválidos y contraste oscuro de controles/divisores |
| UI-PRINT-01 | Impresión | Vista autenticada, independiente, A4 y con nota completa |
| UI-SHELL-01 | Navegación | Búsqueda, sede, notificaciones, breadcrumb, tema y controles ARIA visibles |
| UI-SHELL-02 | Módulos planificados | Opciones sin backend quedan deshabilitadas y sin rutas ficticias |
| UI-DASH-04 | Próximas citas | Consulta ordenada por fecha/hora y representación con datos persistidos |
| UI-SHELL-03 | Recetas y administración | Recetas enlaza al contexto existente; Administración agrupa opciones sin cambiar permisos |
| UI-DASH-05 | Densidad y tema | Acciones no duplicadas, seguimiento junto a próximas citas y separadores oscuros consistentes |
| UI-DASH-06 | KPI accionables | Sin fila paralela; tres acciones separadas y enlaces informativos accesibles |
| UI-SHELL-04 | Topbar persistente | Shell limitado al viewport, contenido desplazable y cabecera compacta visible |
| UI-SHELL-05 | Legibilidad | Sidebar con tamaños reforzados y estados `hover` oscuros sin fondos blancos |

## Perfiles profesionales (`tests/test_professional_profiles.py`)

| ID | Control | Cobertura |
| --- | --- | --- |
| PRO-01 | Validación | Perfil obligatorio para rol clínico y cédula numérica válida |
| PRO-02 | Usuarios | Alta conserva perfil profesional y cédula |
| PRO-03 | Antropometría | Medicina general no ve la pestaña y un POST forjado es rechazado |
| PRO-04 | Nutrición | Pestaña habilitada, autor guardado y rótulo de indicaciones correcto |
| PRO-05 | Impresión | Cédula ausente omitida y snapshot histórico inmutable |
| PRO-06 | Edición | Un profesional general no borra antropometría preexistente |
| PRO-07 | Migración | Columnas de autoría se agregan sin perder consultas legadas |
| PRO-08 | Seguimiento | Sin consulta reciente sólo se renderiza para Nutrición, no para Medicina general u Odontología |
| PRO-09 | Visibilidad antropométrica | La columna % Grasa del historial sólo se renderiza para Nutrición |

## Receta e identidad (`tests/test_prescriptions.py`)

| ID | Control | Cobertura |
| --- | --- | --- |
| RX-SEC-01 | Acceso | Anónimo redirigido, Nutrición rechazada y profesional incompleto bloqueado |
| RX-CRUD-01 | Emisión | Folio, medicamento, alergias, snapshots y evento `CREAR_RECETA` |
| RX-PRINT-01 | Documento | A4 compacto con identidad única, rótulo Domicilio, orden `1..n`, firma centrada, cajas de margen vacías y márgenes clínicos 14/12 mm |
| RX-IMM-01 | Inmutabilidad | Cambios al usuario no reescriben la receta y la consulta asociada no se elimina |
| RX-VAL-01 | Servidor | Filas desalineadas, más de 10 medicamentos y receta especial rechazados |
| RX-HIS-01 | Historial | Original, adicional y sustitución conservan folios/versiones y vigencia independiente |
| RX-SUB-01 | Corrección | Motivo obligatorio, documento anterior intacto y leyenda de no surtir |
| RX-MIG-01 | Migración | Unicidad legada retirada sin perder folios y llaves foráneas verificadas |
| RX-ORDER-01 | Captura | Agregar usa inserción superior, foco inicial y orden oculto consecutivo |
| RX-ORDER-02 | Persistencia/impresión | Filas visuales `3,2,1` se guardan y muestran como `1,2,3` en una lista compacta sin tarjetas |
| UI-ID-01 | Identidad | Cuenta sólo en sidebar, topbar sin identidad e icono canónico PNG/ICO versionado contra caché |
| UI-ID-02 | Estado de cuenta | Panel cerrado por `hidden`, sin saludo duplicado y control local con `aria-expanded` |

## Mantenimiento de la entrega (`tests/test_project_cleanup.py`)

| ID | Control | Cobertura |
| --- | --- | --- |
| PKG-CLEAN-01 | Limpieza segura | Retira SVG/cachés obsoletos y conserva logo vigente, entorno virtual y base local |

## Turno diario (`tests/test_daily_consultation_sequence.py`)

| ID | Control | Cobertura |
| --- | --- | --- |
| CONS-DAY-01 | Asignación | El servidor ignora el número enviado, asigna `1,2…` global y reinicia en otra fecha |
| CONS-DAY-02 | Proyección | Requiere sesión, valida fecha futura y responde sin caché |
| CONS-DAY-03 | Migración | Filas legadas se conservan, renumeran determinísticamente y reciben unicidad diaria |

## Índice de consultas y datos demo (`tests/test_consultation_index.py`)

| ID | Control | Cobertura |
| --- | --- | --- |
| CONS-IDX-01 | Paciente único | Cada paciente aparece una vez y Ver nota abre la última consulta por fecha, turno e ID |
| CONS-IDX-02 | Búsqueda/orden | Nombre y apellidos sin distinción de mayúsculas o acentos; orden permitido e inválidos normalizados |
| CONS-IDX-03 | Paginación | 25 pacientes por página, sin repetir ni omitir expedientes |
| CONS-RX-01 | Compatibilidad | El contexto Recetas conserva todas las consultas específicas e históricas |
| XLS-RBAC-01 | Visibilidad | Botón, formulario y resultado de importación sólo se renderizan para Nutrición |
| XLS-RBAC-02 | Autorización | Solicitud forjada se rechaza antes de consultar al paciente y queda auditada como denegada |
| DEMO-01 | Datos de prueba | Carga idempotente, perfiles, pacientes, consultas, receta ordenada y XLSX demostrativo |
| DEMO-02 | XLSX demostrativo | El archivo incluido es aceptado por el flujo real de importación de Nutrición |

Resultados esperados:

```text
pytest: 97/97 (incluye 15 casos unittest)
ruff: 0 hallazgos
bandit: 0 hallazgos
```
