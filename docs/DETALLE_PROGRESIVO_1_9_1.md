# Detalle progresivo y contraste de pendientes — versión 1.9.1

## Objetivo

Reducir ruido visual sin confundir “dato no capturado” con “dato eliminado”, y corregir los textos de bajo contraste del Dashboard en tema oscuro.

## Criterio de visualización del paciente

| Grupo | Comportamiento | Motivo |
| --- | --- | --- |
| Nombre, género, nacimiento, teléfono, ciudad y estatus | Siempre visible | Identidad y contexto administrativo básico |
| Último pago y siguiente cita | Siempre visible, incluso sin registro | La ausencia tiene valor operativo |
| Correo, ocupación, dirección y contacto/teléfono de emergencia | Visible sólo si fue capturado | Evita una cuadrícula dominada por marcadores vacíos |
| Todos los complementarios vacíos | Un único aviso con **Completar datos** | Comunica la ausencia y ofrece una acción clara |
| Formularios y persistencia | Sin cambios | Ningún dato se borra ni se vuelve inaccesible |

No conviene ocultar indiscriminadamente toda ausencia. Deben permanecer visibles los faltantes que puedan cambiar una decisión clínica u operativa. Esta fase sólo colapsa campos complementarios opcionales en una vista de lectura; el formulario de edición conserva todos los controles.

## Contraste del Dashboard

El panel oscuro usa `#10262d` como fondo. Los renglones de pendientes aplican:

- texto principal `#d8ebea`;
- texto secundario `#b9d2d3`;
- hover/foco `#173a42` con texto `#f0fdfa`;
- texto secundario en hover/foco `#99f6e4`.

Cada combinación se valida automáticamente con una relación mínima de 4.5:1. El foco visible global permanece activo y el estado no depende sólo del color.

## Pruebas

- Dashboard: presencia de selectores oscuros para reposo, hover y foco, además del cálculo WCAG de las cuatro combinaciones.
- Detalle vacío: estado único, acceso a edición y conservación de Último pago/Siguiente cita.
- Detalle parcial: render de los campos presentes y omisión de etiquetas opcionales ausentes.

La fase no cambia rutas, permisos, base de datos, requisitos ni dependencias.
