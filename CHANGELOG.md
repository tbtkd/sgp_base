# Changelog

## 1.10.1 — Endurecimiento local y continuidad operativa

- Se eliminan Tailwind CDN, Font Awesome CDN, Google Fonts, Alpine CDN y SweetAlert CDN; utilidades, iconos y diálogos se sirven desde `app/static` y funcionan sin Internet.
- `scripts/build_local_assets.py` genera de forma determinista `utilities.css` e `icons.css`; `--check` detecta recursos desactualizados.
- La CSP deja de admitir `unsafe-inline` y orígenes externos: usa un nonce criptográfico por respuesta, bloquea atributos ejecutables y atributos de estilo.
- Los flujos de Excel, confirmaciones, impresión, dashboard, plantillas y modales migran a eventos JavaScript locales sin atributos `onclick`, `onchange` o `style`.
- Después de una mutación crítica confirmada se crea una copia SQLite consistente; los rechazos no generan copia y una falla del medio no revierte la transacción clínica ya confirmada.
- Nuevo panel **Administración → Respaldos** para crear, verificar y descargar copias internas.
- La restauración sólo acepta nombres internos, verifica integridad/esquema, exige contraseña administrativa y la frase `RESTAURAR`, crea una copia previa, reemplaza atómicamente la base y cierra la sesión.
- Los eventos de creación, verificación, descarga y restauración quedan auditados sin almacenar contraseñas.
- Se agregan pruebas positivas y negativas para CSP, recursos locales, respaldo por mutación, corrupción, autorización, CSRF, confirmaciones y restauración; se incluye una especificación E2E opcional con Playwright/Chromium.
- Nueva guía `docs/ENDURECIMIENTO_LOCAL_1_10_1.md` y actualización de manual, arquitectura, matriz, seguridad y contexto.

## 1.10.0 — Integridad e historial operativo de pagos

- Los importes nuevos se validan con `Decimal` y se guardan en centavos enteros; `monto` queda sólo como espejo de compatibilidad.
- Cada pago recibe moneda MXN, folio único, clave idempotente de operación, usuario registrador y cita opcional validada contra el paciente.
- La migración transaccional `payments_v110` conserva pagos anteriores, convierte importes válidos y aísla filas incompletas como `requiere_revision` sin sumarlas.
- La relación con Paciente cambia de eliminación en cascada a `ON DELETE RESTRICT`; usuarios y citas opcionales usan `SET NULL`.
- El detalle del paciente muestra último pago vigente, importe/folio e historial inmutable de hasta cincuenta movimientos.
- Nuevo módulo global **Pagos** para Administración/Recepción con total vigente, desglose por método, búsqueda Unicode, filtros, rango máximo y paginación.
- La búsqueda admite nombres completos divididos entre nombre y apellidos; **Ver en Pagos** conserva el comportamiento esperado desde el detalle del paciente.
- Administración dispone de resumen diario/mensual y exportaciones CSV del filtro o del historial por paciente, limitadas y neutralizadas contra fórmulas de hoja de cálculo.
- Sólo Administración puede cancelar; la operación exige motivo y conserva monto, folio, autor y fila originales con auditoría.
- Tras cancelar, el formulario permanece en el flujo de la tabla y el retorno conserva visible/resaltado el folio, aun si el filtro previo era Vigente.
- La confirmación nativa se sustituye por un aviso visual con folio y lenguaje claro: explica que el pago no se elimina, ofrece **Volver** y rotula la decisión irreversible como **Sí, cancelar pago**; conserva un respaldo seguro si el componente visual no carga.
- Doble envío protegido en interfaz y base; intentos repetidos se reconocen sin insertar un segundo movimiento.
- `seed_demo.py --confirm` incorpora una cuenta administrativa, siete citas y dieciocho pagos para validar todos los estados, relaciones explícitas/sin cita, cancelación, periodos, responsables, métodos y CSV seguro.
- La interfaz aclara que una cita no se relaciona automáticamente y que el método de pago es operativo, no una decisión de facturación.
- Hospitalización se retira de la navegación actual porque la edición 1.10.0 está enfocada en consultorios.
- Se retira la hoja legada no referenciada `_sidebar.css`; la limpieza de actualización elimina también cualquier copia residual sin tocar datos ni entornos.
- Nueva documentación operativa en `docs/PAGOS_OPERATIVOS_1_10_0.md` y suite ampliada a 109 pruebas.
- Sin dependencias de ejecución nuevas; no se implementan CFDI, cargos, adeudos, reembolsos, recibos ni corte formal de caja.

## 1.9.1 — Legibilidad de pendientes y detalle progresivo

- Los pacientes y estados desplegados en **Pendientes de atención** reciben colores oscuros específicos para texto, texto secundario, hover y foco, con contraste WCAG AA sobre el panel.
- El detalle del paciente mantiene siempre los datos principales y el seguimiento operativo, pero deja de repetir campos opcionales vacíos como múltiples valores “No registrado”.
- La información complementaria capturada se muestra campo por campo; si no existe ninguna, aparece un único estado compacto con acceso a **Completar datos**.
- Los datos ausentes no se eliminan, no cambian el formulario de edición y no alteran la persistencia, los permisos ni los reportes.
- Suite ampliada a 100 pruebas; sin dependencias ni migraciones de esquema nuevas.

## 1.9.0 — Consultas simplificadas y datos demostrativos

- Consultas clínicas muestra una sola fila por paciente y abre la nota más reciente usando desempate por fecha, turno diario e ID.
- Búsqueda por nombre/apellidos normalizada para mayúsculas y acentos, orden accesible por fecha y paginación de 25 pacientes en servidor.
- El contexto Recetas conserva todas las consultas históricas para no perder el acceso a folios emitidos desde notas anteriores.
- Importar Excel, su formulario y el resultado sólo se renderizan para Nutrición; solicitudes forjadas se rechazan antes de resolver al paciente y se auditan.
- `seed_demo.py --confirm` agrega de forma idempotente usuarios por perfil, seis pacientes, historiales, nueve consultas, citas, pagos y una receta ficticia.
- Se incluye `demo_data/expediente_antropometrico_demo.xlsx` para validar la importación nutricional.
- Suite ampliada a 97 pruebas; sin dependencias ni migraciones de esquema nuevas.

## 1.8.0 — Agenda operativa y estados seguros

- **Agenda y citas** abre `/agenda` en lugar de desplazar el Dashboard.
- Se incorporan vistas Día/Semana, navegación por periodo, conteos de estado y estados vacíos accionables.
- El alta contextual reutiliza la búsqueda privada, el calendario y la validación final existentes.
- La reagenda conserva cita/paciente, excluye sólo su espacio actual y vuelve a comprobar conflictos bajo bloqueo.
- Atendida, No Asistió y Cancelada son estados terminales; las citas futuras no pueden cerrarse como atendidas/inasistentes y cancelar exige motivo.
- Recepción puede operar la agenda sin recibir motivos clínicos ni acciones de inicio de consulta.
- Los cambios y denegaciones se auditan sin copiar el texto clínico completo.
- La columna **% Grasa** permanece visible exclusivamente para Nutrición.
- No cambian esquema ni dependencias.
- Verificación: 89 pruebas `pytest`; 15 casos heredados compatibles con `unittest`; Ruff y Bandit sin hallazgos.

## 1.7.6 — Legibilidad del sidebar y contraste interactivo

- La receta sustituye el rótulo visual **Domicilio profesional** por **Domicilio**, sin modificar el dato persistido ni su instantánea histórica.
- Se incrementan de forma moderada los tamaños de marca, secciones, enlaces, submenús, iconos e identidad del sidebar, conservando su ancho y navegación adaptable.
- El tema oscuro redefine los estados `hover` claros de tablas, tarjetas y controles para evitar fondos blancos con texto de bajo contraste.
- El historial de consultas muestra la columna **% Grasa** únicamente a perfiles de Nutrición y documenta el futuro módulo operativo de Agenda y la lista deduplicada de Consultas.
- Se mantienen rutas, permisos, esquema, dependencias y comportamiento clínico.
- Se incorpora un manual operativo para usuarios médicos, administradores y asistentes/recepción.
- Verificación: 81 pruebas `pytest`; 15 casos heredados compatibles con `unittest`.

## 1.7.5 — Impresión de receta sin metadatos del navegador

- La receta reemplaza las cajas de margen superiores e inferiores del navegador por contenido vacío, retirando fecha/hora, título, URL y paginación automáticos en navegadores Chromium modernos.
- La impresión conserva un margen clínico moderado de 14 mm arriba y 12 mm a los lados y abajo.
- El botón oculta temporalmente el título del documento como respaldo y lo restaura al cerrar la impresión.
- El cambio se limita a la vista de receta: no modifica folios, datos profesionales, tratamiento, firma, orden, permisos ni persistencia.
- Verificación: 80 pruebas `pytest`; 15 casos heredados compatibles con `unittest`.

## 1.7.4 — Firma simplificada y favicon vigente

- La receta declara explícitamente el favicon sanitario vigente y versiona la URL del recurso para evitar que el navegador conserve el icono anterior.
- La ruta de compatibilidad `/favicon.ico` obliga a revalidar el archivo en lugar de reutilizar una copia obsoleta.
- Se incrementa la separación entre el último medicamento y la firma, incluso en recetas con modo denso.
- La firma queda como una sola línea centrada, rotulada “Firma autógrafa del profesional”.
- Nombre, perfil, cédula y domicilio del profesional permanecen una sola vez en el encabezado; se elimina su duplicación al pie y el segundo segmento “Fecha y sello”.
- No cambian folios, medicamentos, snapshots, vigencia, permisos ni datos persistidos.
- Verificación: 80 pruebas `pytest`; 15 casos heredados compatibles con `unittest`.

## 1.7.3 — Receta impresa compacta

- La impresión de medicamentos deja de usar tarjetas con borde y cuadrículas repetidas.
- Cada medicamento se presenta en tres líneas compactas: denominación/presentación, vía/cantidad y posología; las indicaciones adicionales aparecen sólo cuando existen.
- La cantidad opcional ya no imprime un marcador vacío y los datos farmacológicos obligatorios permanecen completos.
- A partir de seis medicamentos se activa una densidad tipográfica adicional para aprovechar mejor la hoja A4.
- Cada bloque usa reglas de salto de página para evitar que un medicamento quede dividido entre dos hojas.
- Se reducen márgenes, espacios de cabecera y firma sin modificar folios, vigencia, alergias, snapshots ni orden clínico.
- Verificación: 80 pruebas pytest; 15 casos heredados compatibles con unittest.

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
