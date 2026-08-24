# Revisión de seguridad y generalización clínica

## Dictamen

La versión 1.7.0 es adecuada para pruebas funcionales y para un piloto en una estación local controlada. No debe exponerse directamente a Internet ni considerarse una plataforma clínica multiusuario de red hasta completar los pendientes prioritarios descritos al final.

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
- CSP, `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy: no-referrer`, políticas de permisos y no-cache para HTML. Estos valores son más estrictos que `SAMEORIGIN` y `strict-origin-when-cross-origin`.

### Validaciones

| Área | Validaciones de servidor |
| --- | --- |
| Paciente | nombres normalizados, género enumerado, nacimiento ≥1900 y no futuro, teléfono de 10 dígitos, correo, longitudes, contacto de emergencia |
| Usuario | usuario normalizado, correo único, rol/estado enumerados, contraseña fuerte |
| Profesional | perfil enumerado, cédula numérica de 5–12 dígitos, establecimiento y domicilio con longitudes limitadas |
| Consulta | fecha no futura, motivo obligatorio, textos limitados, IMC recalculado |
| Signos vitales | TA estructurada, FC 30–250, FR 5–80, temperatura 30–45, SpO₂ 50–100, peso/estatura positivos |
| Antropometría | todos los campos opcionales; cuando existen se validan como números finitos y con rangos |
| Cita | fecha/hora futura, intervalos permitidos, motivo limitado y horario no duplicado |
| Pago | monto 0–10,000,000, concepto obligatorio y método enumerado |
| Receta ordinaria | emisor autorizado, paciente activo, cédula/domicilio, máximo 10 medicamentos, filas completas/no duplicadas y confirmaciones de competencia, alcance y firma |
| XLSX | extensión, tamaño, ZIP válido, rutas internas, ratio de compresión, componentes, dimensiones, filas y transacción atómica |

### Trazabilidad y mensajes

- Eventos críticos normalizados (`LOGIN`, `LOGOUT`, `CREAR_PACIENTE`, `CREAR_CONSULTA`, `REGISTRAR_PAGO`, etc.).
- Registros con usuario, módulo, acción, descripción, entidad, IP, resultado y `request_id`.
- Vista `/auditoria` exclusiva de administradores, con filtros y límite de 500 resultados.
- Metadatos limitados y sin almacenar contraseñas, recetas completas o datos clínicos en el log técnico.
- Excepciones internas y SQL no se devuelven al usuario.
- Mensajes `success`, `error`, `warning` e `info` con iconos y cierre.
- El formulario de citas permanece cerrado al cargar, no depende de Alpine/CDN y cancela las consultas de disponibilidad al cerrarse.
- Los horarios tienen etiquetas HTML reales, contraste explícito y revalidación autoritativa en el servidor.
- La agenda rápida sólo acepta pacientes activos, limita fechas a dos años, rechaza citas previas y revalida el horario dentro de un bloqueo de escritura del proceso local.
- La API visual de disponibilidad exige sesión, no entrega datos personales y marca su respuesta como `no-store`.
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
- Nombre, perfil y cédula del autor se conservan como instantánea; la impresión no usa la identidad del usuario que sólo consulta.
- La nota clínica no se presenta como receta; las indicaciones nutricionales nunca se rotulan como prescripción médica.
- La receta ordinaria requiere Medicina/Odontología, cédula y domicilio; Nutrición y Recepción son rechazados por el servidor.
- La emisión exige confirmar competencia y ausencia de medicamentos sujetos a receta especial.
- La receta guarda instantáneas inmutables y la bitácora omite nombres de medicamentos, dosis y observaciones.
- Originales, adicionales y sustituciones usan folio/versiones independientes; sustituir exige motivo y nunca modifica el documento anterior.
- Un folio sustituido imprime “NO ENTREGAR NI SURTIR” y enlaza al reemplazo.
- La consulta asociada no puede eliminarse una vez emitida cualquier receta.
- Los restablecimientos registran sólo IDs, método y resultado; la credencial nunca se escribe en bitácora o log técnico.

### Persistencia y entrega

- Base `pacientes.db` fuera de `_MEIPASS`.
- Respaldos consistentes mediante `sqlite3.Connection.backup()` y verificación de integridad.
- Retención automática de 10 respaldos.
- Migración aditiva guardada y migración transaccional específica para retirar la unicidad legada de recetas, con `foreign_key_check` e `integrity_check`.
- ZIP y compilación excluyen bases, secretos, logs, cachés, entorno virtual y respaldos.
- La limpieza de actualizaciones sólo elimina el recurso SVG obsoleto y cachés conocidas dentro del código; no recorre el entorno virtual ni los directorios de datos.

## Decisiones que no se aplicaron literalmente

No se redujo `requirements.txt` a únicamente Flask y OpenPyXL porque el proyecto utiliza autenticación, ORM y CSRF; hacerlo eliminaría controles de seguridad esenciales. PyInstaller está separado como dependencia de construcción. Tampoco se relajaron las cabeceras `DENY/no-referrer`, ya que ya satisfacen de forma más estricta las cabeceras solicitadas.

## Pendientes antes de producción en red

1. Cifrado en reposo para base y respaldos, con llaves fuera del equipo.
2. HTTPS y terminación TLS confiable si deja de ser exclusivamente localhost.
3. Política formal de consentimiento, acceso, retención, anonimización y eliminación.
4. Aislamiento por consultorio/tenant si varias organizaciones comparten una instalación.
5. Recursos frontend autocontenidos y CSP sin `unsafe-inline`/CDN.
6. Restauraciones programadas y comprobadas en otra estación.
7. Versionado inmutable de notas clínicas y firma/cierre profesional.
8. Revisión legal y clínica según jurisdicción y especialidad.
9. Firma electrónica regulada, si se desea sustituir la firma autógrafa en papel.
10. Flujo independiente para medicamentos controlados o recetas especiales; no reutilizar la receta ordinaria.

## Evidencia de verificación

- `python -m unittest tests/test_sistema.py`: 15 pruebas.
- `python -m pytest -q`: 74 pruebas totales.
- Ruff: sin hallazgos.
- Bandit: sin hallazgos.
- `pip-audit`: sin vulnerabilidades conocidas en `requirements.txt`.
- Compilación de plantillas y registro de rutas verificados durante la aceptación.
- Arranque local verificado con Waitress y cabeceras de seguridad.
