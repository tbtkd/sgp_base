# Frontend y UI/UX

La interfaz conserva Jinja2, Tailwind CSS y la paleta teal/esmeralda del proyecto original. El shell responsive, sus popovers, el menú de cuenta y el selector de tema se controlan con JavaScript local; Alpine permanece cargado únicamente por compatibilidad con vistas legadas.

## Convenciones

- Formularios complejos agrupados en secciones/pestañas.
- Validación HTML como ayuda; el servidor es autoritativo.
- Mensajes `success`, `error`, `warning`, `info` con icono y cierre.
- Contenido del usuario renderizado con escape de Jinja o `textContent`.
- Solicitudes mutables del mismo origen incluyen CSRF.
- Enlaces externos usan `noopener noreferrer`.
- `.no-print`, menú, encabezado, botones y modales se ocultan al imprimir.

## Consulta clínica

La captura usa tres pestañas generales: consulta, signos vitales y evolución/indicaciones. El perfil Nutrición recibe una cuarta pestaña de antropometría. Esta regla se replica en el servidor. En tema oscuro, cada pestaña tiene fondo, texto y borde explícitos; los botones secundarios y los divisores del formulario utilizan la misma paleta azul petróleo, sin heredar blancos del tema claro.

La impresión genera una nota limpia que el navegador puede guardar como PDF. Muestra el profesional responsable y su perfil; la cédula sólo se presenta cuando fue registrada. Para Nutrición se usa “Indicaciones nutricionales / plan alimentario” y no “receta médica”.

## Receta ordinaria

La receta se genera después de guardar una consulta y nunca comparte la plantilla de la nota. Su formulario permite agregar o quitar hasta 10 medicamentos y su vista A4 es autocontenida. La acción sólo aparece para Medicina general u Odontología; una pantalla de requisitos impide emitir cuando falta cédula o domicilio. El detalle lista todos los folios, permite emitir una receta adicional y ofrece **Sustituir** sólo sobre documentos vigentes. El folio sustituido se conserva y su impresión muestra una advertencia roja.

## Navegación, identidad y tema

El sidebar contiene marca, navegación y la identidad del usuario en su footer. La fila compacta muestra avatar, nombre completo, rol/perfil y un botón `...`. El desplegable abre hacia arriba y presenta nombre legal, rol, área clínica, cédula cuando existe, cambio de contraseña y cierre de sesión. El topbar queda libre de identidad y se dedica a contexto, búsqueda, sede, notificaciones y tema.

La búsqueda global ejecuta la búsqueda existente de pacientes por nombre, teléfono o correo. La sede muestra el único consultorio local configurado y explica que la administración multi-sede aún no existe. Notificaciones muestra un estado vacío real. El tema claro/oscuro se guarda en `localStorage` bajo `sgpn-theme`; las vistas impresas siempre fuerzan fondo claro.

Los módulos sin backend aparecen como botones con `aria-disabled="true"`, distintivo **Próximamente** y mensaje contextual. No se crean enlaces falsos. Recetas es un enlace funcional **Desde consulta**: abre la lista existente con un contexto específico para localizar la consulta que contiene sus folios. Plantillas, Usuarios, Auditoría y Configuración se agrupan bajo el desplegable nativo **Administración**; Configuración continúa planificada. Esta agrupación evita convertir Configuración en un contenedor semánticamente incorrecto. `logo.png` es la marca sanitaria canónica usada en login, sidebar, impresión y favicon; `logo.ico`, derivado del mismo recurso, cubre navegadores legados y PyInstaller.

El dashboard no contiene una fila independiente de Acciones rápidas. Cada KPI dispone de un control informativo que abre la vista correspondiente y de una acción explícita para Nuevo paciente, Agendar cita o Nueva consulta. No se envuelve un botón dentro de otro enlace. Recepción mantiene el KPI clínico restringido y no recibe la acción Nueva consulta. Los accesos a Recetas y Expedientes viven exclusivamente en el sidebar. Próximas citas y Acompañamiento Intermedio comparten una fila de dos columnas y se apilan en resoluciones menores. En tema oscuro, bordes y separadores usan la gama azul petróleo en lugar de conservar líneas claras del tema base.

La acción **Agendar cita** del KPI abre una vista dedicada de cuatro pasos: paciente, fecha, horario y motivo. El padrón completo no se inserta en el HTML. Un `combobox` consulta coincidencias bajo demanda después de dos caracteres, muestra como máximo ocho opciones y permite recorrerlas con flechas, Enter y Escape. Tras elegir, la lista se oculta y sólo permanece una ficha compacta; editar el texto invalida la selección previa. Todo contenido se crea con `textContent`/APIs DOM seguras y las búsquedas anteriores se cancelan. El calendario muestra 21 días y el número de bloques libres; otra fecha puede capturarse con un control nativo. Los horarios se recuperan mediante `fetch` y diferencian texto/estado además del color. Si falla una consulta o no hay paciente confirmado, el envío permanece bloqueado. Esta vista no aparece en el sidebar y no reemplaza el modal existente del detalle.

El bloque de datos históricos del paciente prioriza **Historial Médico**, conserva **Alimentación** en el centro y deja **Actividad Física** al final. En Pendientes de atención, **Sin consulta reciente** se reserva a Nutrición; los demás perfiles clínicos mantienen pendientes de agenda y expedientes según sus permisos.

El shell ocupa la altura visible del navegador y el área principal es el único contenedor vertical desplazable. Por ello el topbar se mantiene visible sin superponerse al contenido. Su altura mínima es 3.65 rem y los controles globales se reducen proporcionalmente; en móvil conserva el comportamiento adaptable previo.

El foco visible se aplica a enlaces, botones, campos, selectores y `summary`. Sidebar, popovers, menú de cuenta y pestañas de gráfica responden a teclado y Escape. El cambio entre gráficas y los popovers no recarga la página; los cambios de módulo mantienen la navegación Flask tradicional para conservar seguridad y contratos existentes.

## Pendiente para producción en red

Tailwind, Alpine, SweetAlert, Font Awesome y fuentes aún se consumen por CDN para preservar el diseño. Deben empaquetarse localmente antes de retirar excepciones CSP como `unsafe-inline`.
