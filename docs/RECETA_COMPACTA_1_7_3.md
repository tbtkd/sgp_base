# Receta impresa compacta — versión 1.7.3

## Objetivo

Reducir la altura de recetas con varios medicamentos sin perder información clínica, alterar el orden de captura ni convertir el documento en una tabla difícil de leer.

## Composición

Cada medicamento se imprime como un bloque breve, sin borde ni fondo:

1. Número, denominación genérica, marca opcional y presentación.
2. Vía de administración y cantidad a surtir, si fue capturada.
3. Dosis, frecuencia y duración.
4. Indicaciones adicionales en cursiva, únicamente cuando existen.

La receta conserva en todos los casos folio, vigencia, fecha, profesional, cédula, domicilio, paciente, alergias, firma y advertencia de alcance ordinario.

## Densidad y paginación

- Márgenes A4 y espacios verticales se reducen de forma moderada.
- No hay tarjetas, cuadrículas ni etiquetas repetidas dentro de cada medicamento.
- Desde seis medicamentos se activa `sheet--dense`, que reduce ligeramente tipografía y separación.
- `break-inside: avoid` y `page-break-inside: avoid` mantienen las instrucciones de cada medicamento en la misma página cuando el navegador lo permite.
- La cantidad y las indicaciones son opcionales: si están vacías no se imprime un marcador artificial.
- Los campos obligatorios —presentación, dosis, vía, frecuencia y duración— nunca se ocultan.

## Seguridad y trazabilidad

El cambio es exclusivamente visual. El servidor continúa validando un máximo de diez medicamentos, filas completas, duplicados, competencia profesional y orden consecutivo `1..n`. No cambia modelos, base de datos, folios, sustituciones, auditoría ni permisos.

## Prueba de aceptación

`tests/test_prescriptions.py` comprueba con seis medicamentos que una captura visual invertida se persiste e imprime `1..n`, que se activa la densidad adicional, que la salida utiliza la lista compacta y que la cuadrícula farmacológica anterior ya no se genera.
