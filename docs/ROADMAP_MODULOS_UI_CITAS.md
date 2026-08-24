# Roadmap integral de módulos e interfaz clínica

## 1. Estado general

La versión 1.7.2 completa la primera fase de consistencia funcional, perfiles profesionales, historial de recetas, recuperación de acceso e identidad de navegación. El panel central presenta KPI accionables, agenda, próximas citas junto a acompañamiento, gráficas locales, pacientes recientes, pendientes únicos y actividad con datos reales, sin incluir ingresos. La acción de Citas de hoy incorpora una agenda rápida que no precarga el padrón: busca bajo demanda, conserva una única ficha seleccionada y mantiene calendario/horarios sin duplicarse en el sidebar ni retirar el modal individual. Top bar y sidebar cuentan con shell responsive y tema persistente; la cabecera compacta permanece visible, la cuenta reside en el footer del sidebar, Administración concentra sus accesos secundarios y los iconos canónicos permanecen sin cambios. El formulario clínico ya no hereda botones ni divisores blancos en tema oscuro; el resumen del paciente prioriza Historial Médico y el seguimiento sin consulta reciente es exclusivo de Nutrición. La receta inserta nuevas tarjetas arriba sin alterar su orden final y las consultas reciben un turno global diario asignado en servidor. Las columnas nuevas se incorporan mediante migración aditiva; las restricciones legadas de recetas y turnos se actualizan mediante migraciones transaccionales específicas que conservan y verifican los datos.

Módulos evaluados:

1. Panel Clínico.
2. Pacientes.
3. Historial Clínico.
4. Consultas Clínicas.
5. Agenda de citas.
6. Nota clínica e impresión/PDF.
7. Cabecera y navegación.
8. Usuarios, perfiles profesionales y cédula.
9. Receta ordinaria e identidad visual.
10. Cambio, restablecimiento y recuperación local de contraseña.

## 2. Diagnóstico de las capturas recibidas

| Captura | Causa raíz | Corrección aplicada |
| --- | --- | --- |
| Historial sin nombre ni padecimientos | La plantilla trataba objetos ORM como diccionarios y solicitaba campos eliminados: `padecimientos`, `tipo_actividad_fisica` y `frecuencia_actividad_fisica`. | Uso de la relación `historial.paciente` y campos actuales: antecedentes, alergias, medicación y actividad física. |
| Pestañas de consulta sin navegación | El cambio de pestaña dependía de Alpine cargado desde CDN. Cuando el recurso no se cargaba, sólo permanecía visible la primera sección. | Navegación local en `app/static/js/tabs.js`, sin dependencia externa, con clic, teclado y activación del panel que contiene un campo inválido. |
| PDF en blanco | `window.print()` imprimía el shell completo de la aplicación. Los contenedores con altura/overflow y el CSS de impresión recortaban la nota. | Ruta y plantilla de impresión independientes, con tamaño A4, sin sidebar, header, Tailwind, Alpine ni CDN. |
| Historial de consultas con `None` | Los valores opcionales se concatenaban directamente con unidades. | Sustitución por `—` y unidades únicamente cuando existe un valor. |
| Cuenta “Administradora A.” | La interfaz fabricaba un alias con nombre e inicial del apellido, que podía parecer un rol o un dato truncado. | El top bar usa el `username`; el desplegable rotula nombre registrado, usuario, rol, área clínica y cédula por separado. |
| Prueba falla por `logo.svg` | Descomprimir un ZIP sobre una carpeta existente no elimina archivos ausentes en la versión nueva. La prueba comprobaba el disco en vez del recurso usado. | La prueba revisa referencias efectivas; `scripts/cleanup_project.py` retira físicamente el SVG y las cachés sin tocar datos o `.venv`. |

## 3. Fases completadas

### Base de seguridad y generalización clínica — completada

- Autenticación, roles, CSRF, auditoría y limitación de login.
- Validaciones de pacientes, consultas, signos vitales, citas, pagos y XLSX.
- Persistencia para ejecución normal/PyInstaller, respaldos y migración aditiva.
- Expediente clínico general con antropometría opcional.

### Estabilización del flujo de citas — completada en 1.2.3

- Modal cerrado por defecto y apertura explícita.
- Cierre por Cancelar, X, Escape y fondo.
- Horarios literales cada 30 minutos de 09:00 a 19:00.
- Contraste del selector y horarios ocupados deshabilitados.
- Disponibilidad cancelable, sin caché y revalidada por el servidor.
- Reagenda sin duplicar la cita y protección contra doble envío.

### Fase 1: consistencia de módulos e impresión — completada en 1.3.0

#### Panel Clínico

- Corregida la correspondencia de los KPIs con los datos del controlador.
- Consultas, expedientes y plantillas muestran conteos reales.
- “WhatsApp / SMS” se cambió a “WhatsApp” porque SMS no está implementado.
- Los accesos clínicos se ocultan para `recepcion` y los KPIs restringidos no exponen conteos.
- Las pestañas del panel también utilizan el controlador local.

#### Pacientes

- Búsqueda ampliada a nombre, apellidos, teléfono y correo.
- Contador de resultados.
- Estado vacío para listas activas/inactivas y búsquedas sin coincidencias.
- Acciones para registrar paciente o limpiar búsqueda.

#### Historial Clínico

- Retiradas todas las referencias a campos legados.
- Carga anticipada de la relación paciente para evitar consultas repetidas.
- Columnas alineadas al expediente clínico general.
- Estado vacío con acceso a la lista de pacientes.

#### Consultas Clínicas

- Pestañas independientes de Alpine/CDN.
- Roles ARIA, navegación con flechas, Inicio y Fin.
- Al detectar un campo inválido se abre automáticamente su pestaña.
- Estado vacío accionable en el listado general.
- Valores opcionales del historial mostrados como `—`, no como `None`.

#### Impresión / PDF

- Nueva vista de impresión autenticada y exclusiva para `admin` y `medico`.
- Documento independiente con motivo, síntomas, signos vitales, diagnóstico, tratamiento, indicaciones y antropometría disponible.
- Formato A4, saltos de página controlados y texto largo ajustable.
- La barra de ayuda se oculta al imprimir.
- No se imprime el historial completo de consultas: la salida corresponde únicamente a la nota seleccionada.

#### Cabecera

- Títulos y subtítulos específicos por módulo.
- Menú del usuario protegido inicialmente con `x-cloak`; en 1.6.2 se reemplazó por `hidden` nativo y control local determinista.
- Identidad y rol/perfil concentrados en el top bar; el sidebar sólo agrega el cierre de sesión solicitado, sin repetir el perfil.

### Fase 1.1: perfiles profesionales y autoría — completada en 1.4.0

- El rol de permisos se separó del perfil clínico.
- Perfiles disponibles: Medicina general, Odontología/Dentista y Nutrición.
- El perfil es obligatorio para usuarios con rol Médico / Profesional clínico.
- Cédula validada como identificador numérico y omitida de la impresión cuando falta.
- Nombre, perfil y cédula se copian a la consulta para preservar su autoría histórica.
- Antropometría e importación XLSX se permiten sólo a Nutrición, tanto en interfaz como en servidor.
- Un POST forjado de antropometría por otro perfil es rechazado.
- Las indicaciones de Nutrición no se rotulan como receta médica.
- Se documentaron los requisitos pendientes de receta ordinaria en `RECETA_MEDICA_MEXICO.md`.

### Fase 1.2: receta ordinaria e identidad — completada en 1.5.0

- Receta separada de la nota clínica, inicialmente limitada a una por consulta.
- Emisión sólo para Medicina general u Odontología con cédula y domicilio profesional.
- Medicamentos estructurados y máximo de 10 filas validadas en servidor.
- Confirmación de competencia y exclusión expresa de receta especial/controlada.
- Snapshot de paciente, alergias y profesional, folio y auditoría sin datos farmacológicos.
- Vista A4 autocontenida con fecha y espacio de firma autógrafa.
- Bloqueo de eliminación de consultas asociadas a una receta.
- Marca unificada e ICO derivado para Windows/PyInstaller.

### Fase 1.3: historial documental y recuperación — completada en 1.6.0

- Receta original, documentos adicionales y sustituciones dentro de la misma consulta.
- Folio y versión únicos; una sustitución enlaza el documento previo y lo marca como no vigente.
- Impresión del folio anterior con advertencia “NO ENTREGAR NI SURTIR”.
- Motivo de sustitución obligatorio y precarga de datos sin sobrescribir el documento emitido.
- Validaciones de paciente activo, filas completas/no duplicadas, revisión/firma y máximo defensivo de documentos.
- Migración transaccional de la unicidad legada, con llaves/índices recreados y comprobaciones SQLite.
- Cambio propio de contraseña e invalidación de otras sesiones.
- Restablecimiento por administrador con reautenticación y contraseña temporal de una sola visualización.
- Recuperación local exclusiva de administradores desde `run.py` o `SistemaPacientes.exe`.
- Nombre corto en el top bar y detalle legal completo dentro del desplegable.
- Nuevo icono sanitario PNG/ICO; eliminado el recurso SVG anterior.

### Fase 1.4: identidad inequívoca y actualización limpia — completada en 1.6.1

- Nombre de usuario estable en la vista compacta de la cabecera.
- Nombre registrado, usuario, rol de acceso, área clínica y cédula mostrados como conceptos distintos.
- Eliminada la propiedad de presentación que generaba abreviaturas ambiguas.
- Prueba del icono basada en referencias reales de plantillas/compilación, no en residuos de una extracción anterior.
- Limpieza estándar, acotada y probada para SVG obsoleto, `__pycache__`, `.pyc`, `.pytest_cache` y `.ruff_cache`.
- Integración de la limpieza en `build_exe.bat` sin recorrer `.venv`, `instance` o `backups`.

### Fase 1.5: cabecera determinista — completada en 1.6.2

- El dashboard muestra “Panel clínico” y elimina el saludo que duplicaba la identidad de cuenta.
- El detalle de cuenta se entrega con `hidden`, por lo que el navegador lo oculta aun si Alpine o su CDN no cargan.
- La interacción usa JavaScript local con apertura explícita, cierre por clic exterior o Escape y estado accesible mediante `aria-expanded`.
- El comportamiento seguro ante un fallo de JavaScript es mantener el detalle cerrado.

### Fase 1.6: dashboard operativo — completada en 1.6.3

- Encabezado de bienvenida dentro del contenido, fecha local y acceso directo a alta de paciente.
- Tres KPIs reales: pacientes activos, citas del día y consultas del mes; ingresos omitidos.
- Agenda compacta con estados y acciones limitadas por rol.
- Gráfica SVG local de altas de seis meses, sin biblioteca o servicio externo.
- Pacientes recientes, pendientes expandibles y actividad clínica derivados de SQLite.
- Acompañamiento Intermedio de 14–15 días conservado con sus acciones.
- Sidebar, top bar, PNG e ICO comprobados sin modificaciones.

### Fase 1.7: shell clínico y tema — completada en 1.6.4

- Sidebar reagrupado con accesos operativos, contextuales y planificados claramente diferenciados.
- Top bar con búsqueda real, sede informativa, notificaciones vacías, breadcrumb, tema y cuenta.
- Tema oscuro persistente, foco visible, teclado/Escape y sidebar móvil controlado localmente.
- Dashboard ampliado con acciones rápidas, gráfica de siete días, próximas citas y alertas reales.
- Se mantienen sin backend Laboratorio, Hospitalización, Facturación, Inventario, Reportes, Configuración y Portal del paciente.
- Próximo: autocontener recursos CDN, pruebas de navegador y diseño formal de cada módulo antes de habilitarlo.

### Fase 1.8: simplificación del shell — completada en 1.6.5

- Identidad y cuenta trasladadas del topbar al footer del sidebar mediante menú `...`.
- Paleta del sidebar alineada a la referencia azul petróleo/teal.
- Acción duplicada de Nuevo paciente retirada del encabezado.
- Alertas duplicadas eliminadas; Pendientes de atención queda como única fuente operativa.
- Próximas citas ampliada sin cambiar su consulta ni sus permisos.

### Fase 1.9: densidad del panel y jerarquía administrativa — completada en 1.6.6

- Acompañamiento Intermedio comparte fila con Próximas citas y se apila de forma responsive.
- Crear receta y Ver expedientes se retiran de Acciones rápidas por duplicar módulos del sidebar.
- Recetas se convierte en un acceso contextual funcional hacia la lista de consultas existente.
- Plantillas, Usuarios, Auditoría y Configuración se agrupan bajo Administración sin modificar permisos.
- Los separadores del dashboard usan bordes azul petróleo consistentes en tema oscuro.
- Próximo: diseñar y aprobar funcionalmente Configuración, módulos planificados y pruebas de navegador antes de habilitar rutas nuevas.

### Fase 1.10: KPI accionables y cabecera persistente — completada en 1.6.7

- Eliminada la fila separada de Acciones rápidas.
- Pacientes, Citas y Consultas combinan resumen navegable y acción explícita sin controles HTML anidados.
- Los estados con cero registros utilizan mensajes informativos y la acción sigue disponible cuando el permiso lo permite.
- Recepción conserva el KPI clínico restringido y no recibe Nueva consulta.
- El shell se ajusta a `100dvh`; sólo el contenido principal se desplaza y el topbar permanece visible.
- Altura, espaciado, buscador y controles del topbar se compactan sin retirar funcionalidad.
- Los saltos por ancla dentro del dashboard no simulan una navegación completa.

### Fase 1.11: contraste clínico y seguimiento especializado — completada en 1.6.8

- Pestañas activas/inactivas y acciones del formulario clínico tienen estados explícitos en tema oscuro.
- Divisores de pestañas y pie de formulario usan bordes azul petróleo consistentes.
- El detalle del paciente presenta Historial Médico primero, Alimentación al centro y Actividad Física al final.
- **Sin consulta reciente** se calcula y renderiza sólo cuando el perfil profesional efectivo es Nutrición.
- Medicina general y Odontología mantienen pendientes de agenda/expediente sin recibir seguimiento nutricional irrelevante.
- No se modifican esquema, rutas, datos clínicos ni permisos base.

### Fase 1.12: agenda rápida del KPI — completada en 1.7.0

- **Agendar cita** deja de dirigir a la lista de pacientes y abre un flujo dedicado.
- Búsqueda y selección de pacientes activos con expediente/teléfono visibles.
- Calendario de 21 días con conteo real de espacios y selector para fechas posteriores.
- Horarios de 09:00 a 19:00 clasificados como disponibles, ocupados o transcurridos.
- Resumen previo y confirmación protegida contra doble envío, fecha inválida, paciente inactivo y conflicto de último momento.
- Una cita existente no se reemplaza desde el KPI; el usuario conserva la reagenda en el detalle.
- Sidebar, modal del paciente, datos, esquema y permisos actuales permanecen intactos.

### Fase 1.13: búsqueda mínima y análisis del Dashboard — completada en 1.7.1

- La pantalla inicial de agenda no contiene nombres, teléfonos ni expedientes del padrón.
- La búsqueda autenticada requiere al menos dos caracteres y devuelve hasta ocho coincidencias activas.
- Nombre, expediente y teléfono se muestran sólo en resultados temporales y en la única ficha seleccionada.
- La respuesta omite contenido clínico y motivo de cita, usa `no-store` y conserva validación autoritativa al confirmar.
- El combobox admite flechas, Enter y Escape; cambiar el texto invalida el identificador previamente seleccionado.
- Agenda de hoy, Próximas citas y Pacientes recientes fueron analizados, pero no retirados ni reinterpretados en esta entrega.

### Fase 1.14: orden de receta y turno diario — completada en 1.7.2

- Agregar medicamento inserta la tarjeta nueva arriba y traslada el foco al primer campo requerido.
- Un identificador oculto conserva el orden real de captura; el servidor exige `1..n`, reordena antes de guardar y la receta imprime esa misma secuencia.
- El número editable de consulta se reemplaza por un turno diario de sólo lectura, global entre pacientes y reiniciado por fecha.
- La proyección al cambiar de fecha es accesible y no se almacena en caché; el servidor asigna el valor definitivo bajo bloqueo.
- SQLite impone unicidad `(fecha, numero_cita)` y una migración no destructiva normaliza filas existentes.
- La importación XLSX y el cambio de fecha de una consulta aplican la misma secuencia y generan trazabilidad.

## 4. Elementos conservados, modificados y retirados

| Área | Conservado | Modificado | Retirado/reemplazado |
| --- | --- | --- | --- |
| Diseño | Paleta teal/esmeralda, tarjetas, sidebar y tablas | Estados vacíos, jerarquía, top bar e icono unificado | Identidad/cierre duplicados del sidebar |
| Base de datos | Relaciones y todos los datos existentes | Columnas aditivas, múltiples recetas y turno diario migrados transaccionalmente | Ninguna fila ni dato clínico |
| Historial | Expediente individual y permisos | Lista con campos actuales | Campos de nutrición legados inexistentes |
| Pestañas | Tres secciones generales | Cuarta sección sólo para Nutrición | Estado `activeTab` dependiente de Alpine |
| Impresión | Botón desde la nota clínica | Vistas A4 separadas para nota y receta | Nota rotulada implícitamente como receta |
| Pruebas | Casos `unittest` existentes | Suite `pytest` ampliada | Ejecución duplicada como requisito |

## 5. Uso correcto de impresión/PDF

1. Abre una nota clínica guardada.
2. Selecciona **Imprimir nota / PDF**.
3. Revisa que los datos de la nota sean correctos.
4. Pulsa **Imprimir / guardar PDF**.
5. En Chrome, Edge u Opera selecciona **Guardar como PDF** como destino.
6. En **Más ajustes**, desactiva **Encabezados y pies de página** para eliminar URL, fecha y número de página generados por el navegador.
7. Mantén escala en 100 %; activa gráficos de fondo sólo si deseas conservar tonos de tablas.

La aplicación prepara la vista imprimible; el archivo PDF lo genera el navegador. No se añadió una biblioteca de PDF porque no es necesaria para este flujo y aumentaría dependencias y superficie de mantenimiento.

Para una receta, primero selecciona **Generar receta**, completa los medicamentos y abre la vista emitida. Después puedes usar **Receta adicional** para otro folio independiente o **Sustituir** para corregir uno vigente sin reescribirlo. La receta debe revisarse, imprimirse y firmarse de forma autógrafa; el PDF sin firma no sustituye ese requisito. No uses este flujo para medicamentos sujetos a receta especial.

## 6. Validaciones y pruebas incorporadas

| ID | Caso | Resultado esperado |
| --- | --- | --- |
| UI-HIS-01 | Historial con paciente y datos actuales | Nombre, antecedentes, alergias y actividad visibles |
| UI-EMPTY-01 | Módulos sin registros | Mensaje explicativo y acción disponible |
| UI-SEARCH-01 | Buscar por teléfono/correo | Paciente localizado |
| UI-KPI-01 | Panel con datos persistidos | Tres contadores coherentes y ningún KPI de ingresos |
| UI-DASH-01 | Composición del panel | Agenda, resumen, recientes, pendientes, actividad y acompañamiento |
| UI-DASH-02 | Rol Recepción | Sin pendientes, actividad ni acciones clínicas |
| UI-TAB-01 | Formulario de consulta | Tres pestañas generales y cuarta sólo para Nutrición |
| UI-PRINT-01 | Vista de impresión | Nota completa, independiente y autenticada |
| RX-CRUD-01 | Emitir receta | Datos obligatorios, snapshot, auditoría e inmutabilidad |
| RX-PRINT-01 | Imprimir receta | Documento A4 completo y sin shell/CDN |
| RX-HIS-01 | Adicional/sustitución | Folios y versiones conservados; documento anterior no vigente |
| RX-ORDER-01 | Orden de receta | Alta visual superior y salida persistida/impresa `1..n` |
| CONS-DAY-01 | Turno diario | Asignación en servidor, reinicio por fecha y cliente ignorado |
| CONS-DAY-02 | Migración diaria | Consultas legadas preservadas y unicidad por fecha verificada |
| RX-MIG-01 | Esquema legado | Datos preservados y nueva relación 1:N verificada |
| SEC-PASS-01 | Recuperación de acceso | Cambio, temporal, invalidación y contingencia local |
| UI-ID-01 | Navegación | Identidad y logout sólo en sidebar, topbar limpio e icono canónico |
| UI-ID-02 | Identidad | Usuario, nombre, rol, área y cédula diferenciados |
| UI-ID-03 | Cabecera | Título sin saludo duplicado, panel nativamente cerrado y control local accesible |
| UI-NAV-04 | Densidad y navegación | Acciones no duplicadas, Recetas contextual y Administración desplegable |
| UI-DASH-06 | KPI accionables | Información y captura unificadas en tarjetas con controles separados |
| UI-SHELL-04 | Topbar persistente | Viewport estable, contenido desplazable y cabecera compacta visible |
| UI-THEME-05 | Consulta oscura | Pestañas, botones secundarios y divisores sin fondos/líneas blancas |
| PRO-08 | Seguimiento nutricional | Ausencia de consulta reciente visible sólo para Nutrición |
| CITA-KPI-01 | Agenda rápida | Paciente, calendario, horarios, revalidación y auditoría sin duplicar navegación |
| CITA-SEARCH-01 | Búsqueda privada | Sin padrón inicial, máximo ocho resultados, ficha única y respuesta sin datos clínicos |
| PKG-CLEAN-01 | Actualización | Cachés/SVG retirados; logo, base y entorno preservados |

Suite oficial:

```bash
python -m pytest -q
```

Resultado de aceptación de 1.7.2: **80 pruebas aprobadas**, incluyendo 15 casos `unittest`. Las pruebas cubren perfiles, recetas originales/adicionales/sustituidas, orden de medicamentos, turno diario, cédula/domicilio, snapshots, inmutabilidad, migraciones, recuperación de contraseñas, invalidación de sesiones, restricción de antropometría, seguimiento nutricional, orden del historial, contraste clínico oscuro, búsqueda privada de pacientes, agenda rápida, calendario y conflictos de citas, KPI accionables, shell persistente, tema, navegación contextual, agrupación administrativa, cabecera, iconos, limpieza segura y compatibilidad de SQLite en Windows.

Instrucciones completas: [EJECUCION_PRUEBAS.md](EJECUCION_PRUEBAS.md).

## 7. Fase 2 recomendada — volumen y operación

- Filtros de consultas por paciente, fecha y texto.
- Paginación real en Pacientes, Consultas, Historial y Auditoría.
- Índices y medición de consultas para bases con mayor volumen.
- Estados y filtros de citas desde un módulo de agenda dedicado.
- Exportación controlada de reportes sin incluir datos no solicitados.
- Confirmaciones y auditoría de operaciones administrativas masivas.

## 8. Fase 3 recomendada — frontend autocontenido

- Compilar Tailwind localmente y retirar su CDN.
- Empaquetar FontAwesome, Alpine y SweetAlert o reemplazar sus usos restantes con componentes locales.
- Consolidar reglas duplicadas de tablas, formularios, pestañas y modales.
- Sustituir los usos legados restantes de Alpine; sidebar, top bar, pestañas clínicas y menú de cuenta ya utilizan JavaScript local.
- Pruebas de interfaz con navegador real para resoluciones de escritorio y móvil.
- Pruebas visuales específicas de impresión en Chrome/Edge y ejecutable PyInstaller.

## 9. Fase 4 antes de producción en red

- Cifrado en reposo para base de datos y respaldos.
- HTTPS y terminación TLS confiable.
- Gestión formal de consentimiento, retención, eliminación y acceso a datos clínicos.
- Versionado inmutable y firma/cierre profesional de notas clínicas.
- Firma electrónica de receta jurídicamente evaluada, si se desea sustituir la firma autógrafa.
- Flujo independiente para medicamentos sujetos a receta especial/controlada.
- Recuperación comprobada de respaldos en otra estación.
- Aislamiento por consultorio si se implementa multi-tenancy.
- Evaluación legal y clínica aplicable a la jurisdicción y especialidad.

## 10. Criterios de aceptación alcanzados

- Los datos del historial se muestran con el modelo actual.
- Las pestañas funcionan aunque Alpine o Internet no estén disponibles.
- La vista imprimible contiene la nota y no el shell de la aplicación.
- La receta ordinaria se genera separada, con datos profesionales completos y medicamentos estructurados.
- Se pueden emitir recetas adicionales y sustituir una vigente sin borrar o reescribir ningún folio.
- Un usuario puede cambiar su contraseña; un administrador puede restablecer otra cuenta y existe una contingencia local para el administrador único.
- La identidad y el cierre de sesión residen únicamente en el footer del sidebar y toda la aplicación utiliza el mismo icono.
- La identidad compacta no inventa abreviaturas: usa el usuario y separa claramente datos personales, permisos y área profesional.
- Los módulos sin datos explican el estado y ofrecen una acción.
- Los KPIs coinciden con los registros persistidos.
- Las columnas nuevas se aplican de forma aditiva y la única reconstrucción controlada (`recetas`) conserva filas y supera las comprobaciones de integridad.
- `python -m pytest -q` y el comando heredado de `unittest` finalizan correctamente.
- El paquete final no contiene base, secretos, logs, respaldos, cachés ni entorno virtual.
- Una actualización sobre carpeta existente dispone de limpieza explícita que conserva datos y entorno virtual.
