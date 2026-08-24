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

La captura usa tres pestañas generales: consulta, signos vitales y evolución/indicaciones. El perfil Nutrición recibe una cuarta pestaña de antropometría. Esta regla se replica en el servidor.

La impresión genera una nota limpia que el navegador puede guardar como PDF. Muestra el profesional responsable y su perfil; la cédula sólo se presenta cuando fue registrada. Para Nutrición se usa “Indicaciones nutricionales / plan alimentario” y no “receta médica”.

## Receta ordinaria

La receta se genera después de guardar una consulta y nunca comparte la plantilla de la nota. Su formulario permite agregar o quitar hasta 10 medicamentos y su vista A4 es autocontenida. La acción sólo aparece para Medicina general u Odontología; una pantalla de requisitos impide emitir cuando falta cédula o domicilio. El detalle lista todos los folios, permite emitir una receta adicional y ofrece **Sustituir** sólo sobre documentos vigentes. El folio sustituido se conserva y su impresión muestra una advertencia roja.

## Navegación, identidad y tema

El sidebar contiene marca, navegación y la identidad del usuario en su footer. La fila compacta muestra avatar, nombre completo, rol/perfil y un botón `...`. El desplegable abre hacia arriba y presenta nombre legal, rol, área clínica, cédula cuando existe, cambio de contraseña y cierre de sesión. El topbar queda libre de identidad y se dedica a contexto, búsqueda, sede, notificaciones y tema.

La búsqueda global ejecuta la búsqueda existente de pacientes por nombre, teléfono o correo. La sede muestra el único consultorio local configurado y explica que la administración multi-sede aún no existe. Notificaciones muestra un estado vacío real. El tema claro/oscuro se guarda en `localStorage` bajo `sgpn-theme`; las vistas impresas siempre fuerzan fondo claro.

Los módulos sin backend aparecen como botones con `aria-disabled="true"`, distintivo **Próximamente** y mensaje contextual. No se crean enlaces falsos. Recetas es un enlace funcional **Desde consulta**: abre la lista existente con un contexto específico para localizar la consulta que contiene sus folios. Plantillas, Usuarios, Auditoría y Configuración se agrupan bajo el desplegable nativo **Administración**; Configuración continúa planificada. Esta agrupación evita convertir Configuración en un contenedor semánticamente incorrecto. `logo.png` es la marca sanitaria canónica usada en login, sidebar, impresión y favicon; `logo.ico`, derivado del mismo recurso, cubre navegadores legados y PyInstaller.

En el dashboard sólo permanecen como acciones rápidas los flujos de captura inmediata: Nuevo paciente, Agendar cita y Nueva consulta. Los accesos a Recetas y Expedientes viven exclusivamente en el sidebar. Próximas citas y Acompañamiento Intermedio comparten una fila de dos columnas y se apilan en resoluciones menores. En tema oscuro, bordes y separadores usan la gama azul petróleo en lugar de conservar líneas claras del tema base.

El foco visible se aplica a enlaces, botones, campos, selectores y `summary`. Sidebar, popovers, menú de cuenta y pestañas de gráfica responden a teclado y Escape. El cambio entre gráficas y los popovers no recarga la página; los cambios de módulo mantienen la navegación Flask tradicional para conservar seguridad y contratos existentes.

## Pendiente para producción en red

Tailwind, Alpine, SweetAlert, Font Awesome y fuentes aún se consumen por CDN para preservar el diseño. Deben empaquetarse localmente antes de retirar excepciones CSP como `unsafe-inline`.
