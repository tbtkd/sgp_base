# Frontend y UI/UX

La interfaz conserva Jinja2, Tailwind CSS, Alpine.js y la paleta esmeralda del proyecto original. La generalización cambia textos y formularios, no el lenguaje visual.

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

## Navegación e identidad

El sidebar contiene únicamente marca y navegación. La vista compacta del top bar muestra el `username`, que es estable y no se confunde con el nombre o el rol. El desplegable rotula por separado nombre registrado, usuario, rol de acceso, área clínica y cédula profesional; también contiene cambio de contraseña y cierre de sesión. `logo.png` es la marca sanitaria canónica usada en login, sidebar, impresión y favicon; `logo.ico`, derivado del mismo recurso, cubre navegadores legados y PyInstaller.

## Pendiente para producción en red

Tailwind, Alpine, SweetAlert, Font Awesome y fuentes aún se consumen por CDN para preservar el diseño. Deben empaquetarse localmente antes de retirar excepciones CSP como `unsafe-inline`.
