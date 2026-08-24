# Firma única y favicon vigente — versión 1.7.4

## Decisión sobre la firma

Para la receta ordinaria de una sola hoja es correcto imprimir nombre completo, perfil, cédula, domicilio profesional y fecha una sola vez en el encabezado y reservar al pie únicamente el espacio de firma autógrafa.

El artículo 29 del Reglamento de Insumos para la Salud exige que la receta contenga impresos el nombre, domicilio completo y cédula de quien prescribe, además de fecha y firma autógrafa. No exige repetir nombre o cédula debajo de la firma ni incorporar un segundo campo “Fecha y sello”.

La aplicación conserva:

- identificación profesional completa en el encabezado;
- fecha de emisión generada por el servidor;
- línea centrada y rotulada para firma autógrafa;
- folio, vigencia, paciente, alergias y tratamiento;
- advertencia de que el PDF sin firma no sustituye el documento firmado.

Este formato continúa limitado a receta ordinaria. Medicamentos sujetos a receta especial requieren un flujo distinto.

## Ajuste visual

- La firma pasa de dos columnas a un único segmento centrado.
- Se retiran nombre, cédula y “Fecha y sello” del pie porque ya están representados en el encabezado.
- El espacio posterior al último medicamento aumenta a 44 px.
- En recetas de seis o más medicamentos, el modo denso conserva 36 px antes de la firma.
- El bloque completo evita dividirse entre páginas.

## Favicon

`logo.png` y `logo.ico` ya corresponden al icono sanitario vigente. La inconsistencia provenía de dos condiciones:

1. la vista independiente de receta no declaraba un favicon;
2. los navegadores almacenan agresivamente `/favicon.ico`.

La versión 1.7.4 declara el icono en el shell y en la receta con `ASSET_VERSION` como parámetro de URL. La ruta de compatibilidad `/favicon.ico` responde con revalidación obligatoria. No se agrega ni conserva un segundo icono.

## Pruebas

`tests/test_prescriptions.py` verifica que:

- la identidad y la cédula aparecen una sola vez;
- “Fecha y sello” ya no se renderiza;
- existe una única firma centrada;
- la receta carga el favicon versionado;
- la ruta de compatibilidad impide reutilizar una caché obsoleta.

## Referencia oficial

- Reglamento de Insumos para la Salud, artículos 28 a 31: https://salud.gob.mx/unidades/cdi/nom/compi/ris.html
