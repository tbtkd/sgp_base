# Changelog

## 1.7.2 — Orden de receta y turno diario de consultas

- **Agregar medicamento** inserta la tarjeta nueva en la parte superior y enfoca su primer campo obligatorio.
- Cada fila conserva un orden de captura oculto, consecutivo, único y validado por el servidor; la receta persistida e impresa mantiene `1, 2, 3…` aunque el formulario muestre primero la captura más reciente.
- El número de consulta deja de aceptar valores del navegador y se convierte en **Turno diario**, global para todos los pacientes y reiniciado por fecha.
- La proyección del siguiente turno se actualiza al cambiar la fecha, exige autenticación y usa `Cache-Control: no-store`; la asignación definitiva ocurre dentro de la transacción.
- La restricción única `(fecha, numero_cita)`, el bloqueo local de asignación y el manejo de conflictos evitan duplicados bajo los hilos de Waitress.
- Las importaciones XLSX también reciben turnos diarios en servidor; los valores del archivo no pueden forzar el consecutivo persistido.
- Migración no destructiva para renumerar consultas legadas por fecha/creación/ID y crear el índice diario tras `integrity_check`.
- Verificación: 80 pruebas `pytest`; 15 casos heredados compatibles con `unittest`.

## 1.7.1 — Búsqueda privada en agenda y revisión funcional del Dashboard

- La agenda rápida deja de renderizar el padrón completo de pacientes al abrir.
- La búsqueda autenticada consulta bajo demanda por nombre, expediente o teléfono y devuelve como máximo ocho coincidencias activas.
- Después de elegir una coincidencia se oculta la lista y permanece visible únicamente la ficha del paciente seleccionado.
- Cambiar el texto invalida la selección anterior; teclado, ARIA, cancelación de solicitudes y bloqueo de doble envío permanecen cubiertos.
- La respuesta no incluye datos clínicos ni el motivo de una cita existente y se marca como `no-store`.
- Se documenta la diferencia entre Agenda de hoy, Próximas citas y Pacientes recientes, sin retirar módulos del Dashboard en esta versión.
- Verificación: 75 pruebas `pytest`; 15 casos heredados compatibles con `unittest`.

## 1.7.0 — Agenda rápida desde el KPI

- La acción **Agendar cita** de Citas de hoy abre un flujo dedicado, sin obligar a navegar primero al detalle del paciente.
- Selector con búsqueda sobre pacientes activos registrados y referencia visible de expediente/teléfono.
- Calendario visual de 21 días con conteo de espacios libres y selector adicional de fecha hasta dos años.
- Horarios completos de 09:00 a 19:00 diferenciados como disponibles, ocupados o transcurridos.
- Resumen previo de paciente, expediente, fecha y hora, con doble envío bloqueado y nueva validación de disponibilidad al confirmar.
- Una cita existente nunca se sobrescribe desde el flujo rápido; la interfaz dirige al detalle para reagendarla mediante el comportamiento previo.
- El modal del detalle del paciente, el sidebar y el resto de los KPI conservan su funcionamiento.
- Verificación: 74 pruebas `pytest`; 15 casos heredados compatibles con `unittest`.

## 1.6.8 — Contraste clínico y seguimiento por especialidad

- Las pestañas inactivas, el botón Cancelar y el botón Guardar de la consulta usan estados propios y legibles en tema oscuro.
- Los divisores superior e inferior del formulario clínico adoptan el borde azul petróleo de la interfaz en lugar de líneas claras.
- El detalle del paciente ordena las tarjetas como Historial Médico, Alimentación y Actividad Física.
- **Sin consulta reciente** se consulta y muestra exclusivamente a perfiles de Nutrición; Medicina general y Odontología conservan los demás pendientes autorizados.
- Las reglas se verifican en interfaz y controlador, sin cambios de esquema, rutas, permisos base ni datos clínicos.
- Verificación: 69 pruebas `pytest`; 15 casos heredados compatibles con `unittest`.

## 1.6.7 — KPI accionables y topbar persistente

- Eliminada la fila independiente de Acciones rápidas; sus tres operaciones se integran dentro de los KPI correspondientes.
- Cada KPI separa correctamente el enlace informativo de la acción de captura para evitar controles anidados y conservar teclado/foco visible.
- Los textos vacíos distinguen agenda disponible y atención clínica al día; recepción conserva el estado restringido sin recibir una acción clínica.
- El shell se limita a la altura visible y delega el desplazamiento al área principal, por lo que el topbar permanece visible.
- Topbar reducido de 4.4 a 3.65 rem, con controles y espaciado compactados sin retirar buscador, sede, notificaciones, tema o breadcrumb.
- Los enlaces internos por ancla ya no activan el indicador de carga de una navegación inexistente.
- Verificación: 68 pruebas `pytest`; no se introducen cambios de esquema, permisos ni lógica clínica.

## 1.6.6 — Densidad del dashboard y navegación administrativa

- **Acompañamiento Intermedio (14-15 Días)** se coloca junto a **Próximas citas** en una cuadrícula de dos columnas que se apila en pantallas menores a 1100 px.
- Retiradas del dashboard las acciones duplicadas **Crear receta** y **Ver expedientes**; permanecen los accesos funcionales en el sidebar.
- **Recetas** deja de ser un módulo planificado: abre el listado de consultas en contexto de gestión de recetas y muestra cabecera específica.
- Plantillas de mensajes, Usuarios y permisos, Auditoría y Configuración se agrupan bajo **Administración**, conservando permisos y dejando Configuración como opción planificada.
- Corregidos los separadores claros heredados dentro del tema oscuro mediante bordes azul petróleo consistentes.
- Verificación: 68 pruebas `pytest`; no se introducen cambios de esquema, permisos ni lógica clínica.

## 1.6.5 — Simplificación visual e identidad en sidebar

- Eliminado el bloque **Alertas clínicas y administrativas** porque duplicaba exactamente las fuentes de **Pendientes de atención**.
- Conservado **Pendientes de atención** como única vista de seguimiento, incluyendo sus detalles expandibles y progreso diario.
- **Próximas citas** ocupa el espacio liberado y distribuye sus elementos de forma adaptable.
- Retirada la acción superior duplicada de **Nuevo paciente**; permanece dentro de Acciones rápidas.
- Reducido el espacio vertical del encabezado del dashboard para aligerar la zona superior.
- Sidebar actualizado a la gama azul petróleo/teal de la referencia, manteniendo logotipo, iconos, rutas y permisos.
- Identidad de usuario retirada del topbar y trasladada al pie del sidebar.
- Nuevo botón `...` accesible para desplegar nombre completo, rol/perfil, cédula condicional, cambio de contraseña y cierre de sesión.
- El topbar queda dedicado a contexto, búsqueda, sede, notificaciones y tema.
- Verificación: 67 pruebas `pytest`; no se introducen cambios de esquema ni de lógica clínica.

## 1.6.4 — Shell clínico accesible y dashboard ampliado

- Sidebar reorganizado por General, Clínico, Gestión y Otros, conservando las rutas y permisos existentes.
- Agenda enlaza al bloque operativo real; Recetas informa que se gestionan desde una consulta; Laboratorio, Hospitalización, Facturación, Inventario, Reportes, Configuración y Portal del paciente quedan identificados como planificados, sin rutas ni datos simulados.
- Cierre de sesión disponible en el sidebar y en el menú de cuenta, manteniendo la identidad detallada exclusivamente en el top bar.
- Top bar con búsqueda real de pacientes, selector informativo de sede local, notificaciones con estado vacío, breadcrumb, menú de cuenta y selector de tema.
- Tema claro/oscuro persistente mediante `localStorage`, paleta oscura teal local y estilos de impresión forzados a claro.
- Sidebar móvil, popovers y menú de cuenta controlados por JavaScript local con Escape, foco restaurado y estados ARIA; Alpine deja de ser necesario para estos componentes.
- Indicador de navegación, mensajes accesibles para módulos planificados y foco visible global.
- Dashboard con acciones rápidas, KPI de consultas pendientes, gráfica SVG de citas/consultas de siete días, gráfica secundaria de altas, próximas citas y alertas basadas en SQLite.
- La vista de recepción conserva los límites de acceso clínico y no recibe conteos de consultas ni accesos protegidos.
- Verificación: 67 pruebas `pytest`; 15 casos heredados compatibles con `unittest`.

## 1.6.3 — Dashboard clínico operativo

- Nueva composición central inspirada en la referencia visual, adaptada al tema claro existente y sin modificar top bar, sidebar, logotipo o iconos institucionales.
- Encabezado contextual con fecha, saludo y acción directa para registrar pacientes.
- KPIs reales para pacientes activos, citas de hoy y consultas del mes; se excluye expresamente cualquier indicador de ingresos.
- Agenda diaria compacta con estados, acceso al expediente, inicio de consulta según permisos y actualización de inasistencia/cancelación.
- Gráfica SVG local de altas de pacientes durante seis meses, sin dependencias nuevas ni datos simulados.
- Tabla de pacientes recientes, pendientes expandibles y actividad reciente alimentadas desde SQLite.
- Conservado íntegramente el bloque de Acompañamiento Intermedio de 14–15 días y sus acciones WhatsApp/posponer.
- Recepción no recibe conteos, pendientes ni accesos clínicos en el nuevo dashboard.
- Retiradas las plantillas de pestañas del panel que quedaron obsoletas; las pestañas de consulta siguen intactas.
- Verificación: 65 pruebas `pytest`, 15 casos `unittest`, Ruff y Bandit sin hallazgos.

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
