# Agenda rápida desde el KPI — versión 1.7.0

## Decisión de experiencia

La acción **Agendar cita** de Citas de hoy ya no envía a la lista de pacientes. Abre una pantalla dedicada porque el usuario necesita resolver en una sola vista cuatro preguntas: quién, qué día, a qué hora y con qué motivo.

Este acceso se implementa sólo en el KPI. No se agrega otra entrada al sidebar y no se elimina el modal del detalle del paciente.

## Flujo

1. Buscar por nombre, expediente o teléfono y seleccionar un paciente activo.
2. Revisar los próximos 21 días; cada fecha indica cuántos horarios siguen libres.
3. Si se requiere, seleccionar otra fecha mediante el control nativo, hasta dos años en el futuro.
4. Elegir un bloque entre 09:00 y 19:00. Ocupados y transcurridos aparecen deshabilitados y rotulados.
5. Capturar un motivo opcional y revisar paciente, expediente, fecha y horario.
6. Confirmar. El servidor consulta nuevamente el espacio antes de guardar.

Si el paciente ya tiene una cita programada, se muestra la fecha/hora y un enlace a su detalle. El KPI no reemplaza esa cita: la reagenda continúa en el flujo individual existente.

## Contratos

- `GET /pacientes/agendar-cita`: pantalla y calendario inicial.
- `POST /pacientes/agendar-cita`: creación rápida con CSRF y auditoría.
- `GET /pacientes/disponibilidad_citas?fecha=YYYY-MM-DD`: lista estructurada de 21 horarios; requiere autenticación y responde `no-store`.
- `GET /pacientes/disponibilidad_horas`: contrato legado conservado para el modal del detalle.

No se agregaron tablas, columnas ni dependencias.

## Seguridad y consistencia

- Paciente entero, existente y activo.
- Fecha presente/futura y no mayor a dos años.
- Hora dentro del catálogo de media hora.
- Motivo normalizado y limitado a 500 caracteres.
- Cita previa bloqueada en el flujo rápido.
- Disponibilidad revalidada inmediatamente antes de crear.
- Validación y escritura serializadas dentro del proceso local.
- Auditoría `CREAR_CITA` con identificadores y origen, sin guardar el motivo.
- Renderizado frontend con `textContent`, `replaceChildren` y atributos DOM; no se inserta contenido del paciente con `innerHTML`.
- Solicitudes de disponibilidad cancelables, respuesta no cacheable y confirmación deshabilitada ante error.

## Pruebas

```powershell
python -m pytest -q tests/test_appointments.py
python -m pytest -q
```

Resultado global esperado: `74 passed`. Los 15 casos heredados siguen disponibles mediante `python -m unittest tests/test_sistema.py`.
