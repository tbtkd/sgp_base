# Impresión de receta limpia — versión 1.7.5

## Problema identificado

La fecha y hora, el título “Receta RX-…”, la URL y el número de página que pueden aparecer en los extremos de la hoja no pertenecen al documento clínico. Son encabezados y pies generados por el navegador en el área de margen.

## Solución aplicada

La plantilla de receta usa `@page` con:

- margen superior de 14 mm;
- márgenes laterales e inferior de 12 mm;
- cajas `@top-left`, `@top-center`, `@top-right`, `@bottom-left`, `@bottom-center` y `@bottom-right` con contenido vacío.

Chromium 131 o posterior utiliza estas cajas definidas por la aplicación en lugar de sus encabezados y pies integrados. Como defensa adicional, `printPrescription()` deja temporalmente vacío el título del documento, invoca `window.print()` y lo restaura con `afterprint` y un respaldo temporizado.

La fecha de emisión clínica dentro del encabezado de la receta permanece visible. Sólo se retira la fecha/hora técnica agregada por el navegador.

## Compatibilidad

Opera, Chrome y Edge basados en Chromium moderno soportan las cajas de margen de página. Firefox todavía puede depender de su preferencia **Encabezados y pies de página**; una aplicación web no puede imponer esa configuración del navegador. En ese caso debe desactivarse desde el diálogo de impresión.

## Alcance

El ajuste sólo afecta la plantilla `app/templates/recetas/imprimir_receta.html`. No cambia:

- datos clínicos o profesionales;
- folios, versiones o vigencia;
- orden y contenido de medicamentos;
- firma autógrafa;
- base de datos, auditoría o permisos;
- impresión de la nota clínica.

## Pruebas

`tests/test_prescriptions.py` verifica los seis márgenes vacíos, la medida 14/12 mm, la invocación dedicada de impresión, el título temporal vacío y la conservación de las pruebas previas de receta.

## Referencias técnicas

- MDN, impresión con CSS y `@page`: https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Media_queries/Printing
- Chrome 131, cajas de margen `@page`: https://developer.chrome.com/release-notes/131
