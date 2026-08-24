# Matriz de pruebas — versión 1.6.1

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
| CITA-UI-03 | Horarios | 21 etiquetas literales de 09:00 a 19:00 y estilos de contraste |
| CITA-SEC-01 | Autenticación | Disponibilidad redirige al login sin sesión |
| CITA-API-01 | Disponibilidad | Respuesta ordenada, sin caché y exclusión al reagendar |
| CITA-API-02 | Validación | Fecha inválida devuelve HTTP 400 |
| CITA-CRUD-01 | Alta | Cita futura persistida y evento `CREAR_CITA` |
| CITA-CRUD-02 | Reagenda | Mismo registro actualizado y evento `ACTUALIZAR_CITA` |
| CITA-CRUD-03 | Conflictos | Horario ocupado y fecha pasada no se persisten |

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
| UI-HIS-01 | Historial | Paciente y campos clínicos actuales visibles |
| UI-EMPTY-01 | Estados vacíos | Pacientes, historiales y consultas muestran explicación y acción |
| UI-SEARCH-01 | Búsqueda | Teléfono y correo localizan pacientes |
| UI-KPI-01 | Panel | Pacientes, consultas, expedientes y plantillas coinciden con la base |
| UI-TAB-01 | Pestañas | Navegación local, teclado y activación ante campos inválidos |
| UI-PRINT-01 | Impresión | Vista autenticada, independiente, A4 y con nota completa |

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

## Receta e identidad (`tests/test_prescriptions.py`)

| ID | Control | Cobertura |
| --- | --- | --- |
| RX-SEC-01 | Acceso | Anónimo redirigido, Nutrición rechazada y profesional incompleto bloqueado |
| RX-CRUD-01 | Emisión | Folio, medicamento, alergias, snapshots y evento `CREAR_RECETA` |
| RX-PRINT-01 | Documento | A4 independiente con nombre, cédula, domicilio, fecha, posología y firma pendiente |
| RX-IMM-01 | Inmutabilidad | Cambios al usuario no reescriben la receta y la consulta asociada no se elimina |
| RX-VAL-01 | Servidor | Filas desalineadas, más de 10 medicamentos y receta especial rechazados |
| RX-HIS-01 | Historial | Original, adicional y sustitución conservan folios/versiones y vigencia independiente |
| RX-SUB-01 | Corrección | Motivo obligatorio, documento anterior intacto y leyenda de no surtir |
| RX-MIG-01 | Migración | Unicidad legada retirada sin perder folios y llaves foráneas verificadas |
| UI-ID-01 | Identidad | Cuenta sólo en top bar, sidebar sin duplicado e icono canónico en PNG/ICO |

## Mantenimiento de la entrega (`tests/test_project_cleanup.py`)

| ID | Control | Cobertura |
| --- | --- | --- |
| PKG-CLEAN-01 | Limpieza segura | Retira SVG/cachés obsoletos y conserva logo vigente, entorno virtual y base local |

Resultados esperados:

```text
pytest: 65/65 (incluye 15 casos unittest)
ruff: 0 hallazgos
bandit: 0 hallazgos
```
