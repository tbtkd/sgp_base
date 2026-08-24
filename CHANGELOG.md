# Changelog

## 1.6.2 — Cabecera determinista y roadmap visual

- El Panel Clínico muestra un título de módulo estable y deja de duplicar la identidad con el saludo “Bienvenido”.
- El detalle de cuenta utiliza `hidden` como estado inicial nativo; permanece cerrado incluso si Alpine o un recurso CDN no carga.
- El desplegable se controla con JavaScript local y accesible: apertura explícita, cierre por clic exterior o Escape y sincronización de `aria-expanded`.
- El sidebar continúa reservado exclusivamente para marca y navegación.
- Se amplió la regresión de identidad para comprobar el título, el estado cerrado y la ausencia de la dependencia Alpine en el menú de cuenta.
- Nuevo análisis de etapa y roadmap visual priorizado en `docs/ROADMAP_VISUAL_Y_ANALISIS_1_6_2.md`.
- Verificación de entrega: 65 pruebas `pytest`, 15 casos `unittest`, Ruff y Bandit sin hallazgos.

## 1.6.1 — Identidad de cuenta y actualización limpia

- El top bar muestra el nombre de usuario estable en vez de construir abreviaturas ambiguas como “Administradora A.”.
- El menú de cuenta diferencia con rótulos explícitos el nombre registrado, usuario, rol de acceso, área clínica y cédula profesional.
- La prueba de marca valida los recursos realmente referenciados y deja de depender de que una extracción de ZIP elimine archivos ajenos al paquete.
- Nueva utilidad `scripts/cleanup_project.py` para retirar el SVG obsoleto y cachés sin tocar `.venv`, datos, respaldos, secretos o logs.
- `build_exe.bat` ejecuta la limpieza segura antes de empaquetar.
- Suite ampliada a 65 pruebas; se conservan 15 casos compatibles con `unittest`.

## 1.6.0 — Historial de recetas, recuperación de acceso e identidad sanitaria

- Varias recetas por consulta: original, adicionales y sustituciones con folio y versión propios.
- Corrección no destructiva: el documento anterior queda `sustituida`, conserva medicamentos/snapshots y enlaza al nuevo folio.
- Impresiones de folios sustituidos marcadas de forma visible como “NO ENTREGAR NI SURTIR”.
- Motivo de sustitución obligatorio, controles de concurrencia y migración transaccional de la restricción legada de una receta por consulta.
- Validación de firma pendiente, duplicados exactos, paciente activo, máximo de documentos y campos farmacológicos rotulados con mayor precisión.
- Cambio propio de contraseña con invalidación de sesiones, restablecimiento por administrador con reautenticación y credencial temporal de una sola visualización.
- Recuperación local exclusiva de administradores mediante `run.py` o el ejecutable, sin correo ni servicios externos.
- `auth_version`, cambio obligatorio y eventos de auditoría sin contraseñas ni contenido farmacológico.
- Nombre corto en el top bar; nombre legal completo, rol, perfil y cédula permanecen en el menú desplegable.
- Nuevo icono sanitario en PNG y su derivado ICO; retirada la marca SVG anterior.
- Suite ampliada a 64 pruebas; se conservan 15 casos compatibles con `unittest`.

## 1.5.0 — Receta ordinaria e identidad visual unificada

- Receta médica ordinaria separada de la nota clínica y restringida a perfiles de Medicina general u Odontología.
- Bloqueo de emisión cuando falta cédula o domicilio profesional completo; Nutrición conserva indicaciones nutricionales sin acceso al módulo.
- Medicamentos estructurados con denominación genérica, presentación, dosis, vía, frecuencia, duración, cantidad e indicaciones.
- Instantánea inmutable de paciente, alergias y profesional, folio propio y evento `CREAR_RECETA` sin contenido farmacológico en la auditoría.
- Exclusión explícita de medicamentos sujetos a receta especial y confirmación de competencia profesional antes de emitir.
- Vista A4 independiente con fecha, datos profesionales, firma autógrafa pendiente y advertencia de alcance.
- Consultas con receta emitida protegidas frente a eliminación accidental.
- Datos de cuenta concentrados en el top bar; se retiraron el usuario y cierre de sesión duplicados del sidebar.
- Rol y perfil se muestran con etiquetas comprensibles en lugar de valores internos.
- `logo.svg` adoptado como fuente visual canónica; `logo.ico` derivado se usa en favicon y PyInstaller.
- Migración aditiva para domicilio y establecimiento profesional; tablas nuevas para recetas y medicamentos.
- Suite ampliada a 55 pruebas; 15 casos siguen compatibles con `unittest`.

## 1.4.0 — Perfiles profesionales y trazabilidad de indicaciones

- Separación entre rol de acceso y perfil profesional: Medicina general, Odontología/Dentista y Nutrición.
- Cédula profesional validada y mostrada de forma condicional; si no existe, no aparece en la impresión.
- Cada consulta nueva conserva una instantánea del nombre, perfil y cédula del profesional que la registró.
- Antropometría e importación antropométrica disponibles únicamente para perfiles de Nutrición, con control en interfaz y servidor.
- Los nutriólogos reciben el rótulo “Indicaciones nutricionales / plan alimentario”, no “receta médica”.
- Documento normativo sobre los requisitos pendientes para considerar la impresión una receta ordinaria en México.
- Migración aditiva de las nuevas columnas, sin modificar ni eliminar registros existentes.
- Suite ampliada a 50 pruebas; se mantienen los 14 casos compatibles con `unittest`.

## 1.3.1 — Compatibilidad de pruebas SQLite en Windows

- Liberación explícita de la sesión y del `Engine` de SQLAlchemy en aplicaciones temporales de prueba.
- Corregido `WinError 32` al eliminar `legacy.db` con Python 3.13 en Windows.
- Conservadas las 44 pruebas de la suite completa y los 14 casos compatibles con `unittest`.
- Sin cambios en el esquema, los datos clínicos ni el comportamiento de ejecución de la aplicación.

## 1.3.0 — Consistencia de módulos e impresión clínica

- KPIs del Panel Clínico conectados a conteos reales y respetando permisos por rol.
- Búsqueda de pacientes ampliada a teléfono y correo, contador de resultados y estados vacíos.
- Lista de historiales migrada a los campos clínicos actuales y relación ORM del paciente.
- Pestañas de consultas y panel controladas por JavaScript local accesible, sin depender de Alpine/CDN.
- Vista A4 independiente para imprimir o guardar una nota clínica como PDF.
- Valores opcionales del historial mostrados como `—` en lugar de `None`.
- Encabezados específicos por módulo y protección visual del menú de usuario.
- Roadmap integral regenerado e instrucciones de prueba para Windows PowerShell.
- Suite oficial ampliada a 44 casos.

## 1.2.3 — Flujo estable de citas y roadmap de módulos

- Roadmap documentado para Panel, Pacientes, Consultas, Historial y Agenda antes de modificar la aplicación.
- Modal de citas cerrado por defecto y abierto únicamente desde la acción explícita del expediente.
- Eliminada la dependencia de Alpine/CDN para abrir, cerrar, cargar disponibilidad y reagendar.
- Cierre consistente mediante Cancelar, X, Escape y fondo; limpieza al restaurar la navegación.
- Horarios literales cada 30 minutos de 09:00 a 19:00, con contraste explícito y ocupados deshabilitados.
- Consultas de disponibilidad sin caché, cancelables y con exclusión de la propia cita al reagendar.
- Protección visual contra doble envío y conservación de la validación autoritativa del servidor.
- Suite oficial unificada en `pytest`, ampliada a 38 casos.

## 1.2.2 — Migración de usuarios sin correo

- Compatibilidad con tablas `usuarios` antiguas que no contienen `email`.
- Backfill único y reconocible mediante el dominio reservado `local.invalid`, sin alterar nombres de usuario ni contraseñas.
- Índice único para los correos temporales generados durante la migración.
- Advertencia posterior al login para actualizar el correo temporal.
- Prueba de regresión con dos cuentas legadas y conservación de sus registros.

## 1.2.1 — Diagnóstico de arranque y compatibilidad legada

- El arranque muestra la excepción concreta y conserva el traceback en `instance/logs/startup.log`.
- Eliminada la segunda creación de Flask dentro del manejador de fallos.
- Las importaciones tempranas quedan cubiertas por el diagnóstico de inicio.
- Migración aditiva compatible con columnas obligatorias nuevas que poseen valores seguros (`usuarios`, pagos y marcas de tiempo).
- Pruebas de regresión para esquemas legados con datos y para fallos anteriores a Flask.

## 1.2.0 — Expediente clínico general

- Generalización de nutrición a servicios médicos, dentales, nutricionales y de salud.
- Pacientes ampliados con dirección, ocupación y contacto de emergencia.
- Historial reorganizado en antecedentes, alergias/medicación y hábitos.
- Consulta clínica con signos vitales, síntomas, diagnóstico, tratamiento y receta.
- Antropometría convertida en sección opcional.
- Roles normalizados a `admin`, `medico`, `recepcion`.
- Limitación de acceso por IP y cuenta durante cinco minutos.
- Panel administrativo de auditoría.
- Citas con motivo y pagos con monto, concepto y método.
- WhatsApp directo e impresión/PDF mediante el navegador.
- `app/db.py` con persistencia PyInstaller, respaldo nativo, rotación de 10 copias y migración aditiva.
- Nuevo `seed_admin.py`; eliminado `manage.py`.
- Suite estándar `unittest` y ampliación de la suite completa a 27 pruebas.
- Dependencias de ejecución reducidas a las realmente utilizadas.

## 1.1.0 — Endurecimiento base

- Autenticación, RBAC, CSRF, validación centralizada, auditoría y errores genéricos.
- Importación XLSX defensiva y atómica.
- Servidor local Waitress, pruebas automatizadas y limpieza de datos/artefactos.
