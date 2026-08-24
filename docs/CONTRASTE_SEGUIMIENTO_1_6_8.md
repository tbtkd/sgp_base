# Contraste clínico y seguimiento por especialidad — versión 1.6.8

## Objetivo

Corregir los controles claros que rompían la paleta oscura, mejorar la jerarquía del historial del paciente y evitar que un seguimiento propio de Nutrición aparezca a Medicina general u Odontología.

## Ajustes visuales

- Las pestañas del formulario clínico usan las clases estables `clinical-tablist` y `clinical-tab`.
- Una pestaña inactiva en tema oscuro usa fondo azul petróleo, texto claro y borde visible; la activa conserva el acento teal.
- Los botones Cancelar y Guardar tienen estados secundarios/primarios independientes, incluido foco visible.
- Los divisores de pestañas y acciones usan `#29464d` en modo oscuro; no heredan el blanco de las utilidades de Tailwind.
- Las utilidades `bg-gray-100` y `bg-gray-200` reciben una equivalencia oscura para controles legados que aún las utilicen.

## Orden del historial

Las tarjetas del detalle del paciente se presentan en este orden:

1. Historial Médico.
2. Alimentación.
3. Actividad Física.

El cambio es sólo de presentación; conserva campos, valores, modelo y permisos existentes.

## Seguimiento por especialidad

`main.index()` determina `can_view_nutrition_followup` a partir del permiso clínico y de `current_user.puede_capturar_antropometria`. Sólo en ese caso consulta `Paciente.obtener_sin_valoracion_reciente(30)` y entrega el bloque **Sin consulta reciente** a la plantilla.

- Nutrición: ve el indicador y sus pacientes, si existen.
- Medicina general y Odontología: no reciben ni renderizan ese segmento.
- Recepción: conserva su restricción clínica previa.
- Pendientes por agendar y expedientes pendientes mantienen el comportamiento existente.

## Regresiones cubiertas

- Clases y reglas de contraste oscuro presentes en el formulario.
- Orden exacto de las tres tarjetas del historial.
- Visibilidad positiva para Nutrición y negativa para Medicina general/Odontología.
- Navegación por teclado y activación de pestañas permanecen intactas.

La suite oficial es:

```powershell
python -m pytest -q
```

Resultado esperado: `69 passed`. El comando heredado `python -m unittest tests/test_sistema.py` continúa ejecutando sus 15 casos compatibles.
