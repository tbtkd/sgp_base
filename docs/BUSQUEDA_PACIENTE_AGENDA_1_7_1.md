# Búsqueda de paciente en agenda y análisis del Dashboard — versión 1.7.1

## Cambio implementado

La agenda rápida ya no carga ni renderiza todos los pacientes activos. Al abrir, muestra únicamente el campo de búsqueda. Después de escribir al menos dos caracteres consulta en servidor por nombre, expediente o teléfono y devuelve como máximo ocho coincidencias.

Al seleccionar una coincidencia:

- se oculta la lista temporal;
- queda visible una sola ficha con nombre, expediente y teléfono;
- se conserva el identificador en un campo oculto para el envío;
- una cita programada se advierte sólo con fecha y hora, sin exponer su motivo;
- editar nuevamente el texto invalida la selección anterior para evitar confirmar sobre otro paciente;
- el servidor vuelve a validar existencia, estado activo, cita previa y disponibilidad.

La respuesta requiere sesión, usa `Cache-Control: no-store` y no contiene historial, alergias, diagnóstico, prescripción, pagos ni otros datos clínicos. La interacción admite flechas, Enter y Escape y construye los resultados mediante APIs DOM seguras.

## Análisis funcional del Dashboard

### Agenda de hoy

Es la vista operativa del día actual. Incluye todas las citas del día, su hora y estado, y permite iniciar consulta, abrir expediente, marcar inasistencia o cancelar cuando corresponde. Responde a la pregunta: **¿qué debe atenderse hoy y qué acción debo realizar?**

Recomendación: conservarla. No es equivalente al KPI **Citas de hoy**: el KPI resume y abre el agendamiento; esta tarjeta ejecuta el trabajo diario.

### Próximas citas

Es una vista de continuidad que lista únicamente citas `Programada`, ordenadas por fecha y hora. Responde a: **¿qué atención está programada después del momento actual?**

Actualmente `Cita.obtener_proximas()` también incluye las citas de hoy cuya hora no ha transcurrido. Por ello, una cita programada para hoy puede aparecer simultáneamente en **Agenda de hoy** y **Próximas citas**. Ésta sí es una duplicidad funcional visible.

Recomendación propuesta, no implementada: hacer que **Próximas citas** comience mañana (`fecha > hoy`) y cambiar su enlace secundario a una futura vista completa de agenda. Así, Agenda de hoy queda para operación inmediata y Próximas citas para planeación futura.

### Pacientes recientes

Es una vista de altas recientes. Ordena por fecha de registro y muestra expediente, última consulta, estado y acceso al detalle. Responde a: **¿qué pacientes se incorporaron recientemente y requieren completar su expediente o primera atención?**

No duplica funcionalmente la agenda: un paciente puede aparecer en ambos bloques, pero uno representa una cita y el otro un alta. Sin embargo, la primera alta también se repite dentro de **Actividad reciente**, que muestra de nuevo al paciente más recientemente registrado. Esa es la duplicidad más clara de este bloque.

Recomendación propuesta, no implementada:

1. Renombrar **Pacientes recientes** como **Altas recientes**.
2. Sustituir la columna **Última consulta** por **Fecha de alta** o agregar una señal **Expediente pendiente/completo**, porque describe mejor el propósito del bloque.
3. Mantener aquí el detalle de 3–5 altas y retirar de **Actividad reciente** el evento redundante de “Paciente registrado”.
4. Reservar **Actividad reciente** para eventos distintos: consultas concluidas, citas canceladas/no asistidas, recetas emitidas o cambios administrativos autorizados.

## Simplificación recomendada

| Segmento | Decisión sugerida | Motivo |
| --- | --- | --- |
| KPI Citas de hoy | Conservar | Resumen y acceso rápido al agendamiento |
| Agenda de hoy | Conservar | Operación detallada del día y acciones por cita |
| Próximas citas | Conservar, excluyendo hoy | Evita repetir las citas de la agenda diaria |
| Pacientes recientes | Conservar como Altas recientes | Aporta seguimiento de incorporación, no de agenda |
| Actividad reciente | Depurar | Repite el paciente más reciente; debe concentrar eventos distintos |

La versión 1.7.1 no modifica estas consultas ni retira bloques del Dashboard. El cambio se limita a la privacidad y usabilidad de la búsqueda de pacientes en la agenda; las recomendaciones anteriores quedan como decisión de una fase posterior.

## Validación

- Pantalla inicial sin nombres, teléfonos ni expedientes de pacientes registrados.
- Endpoint de búsqueda protegido por login.
- Búsqueda por nombre y por `EXP-####`.
- Máximo de ocho coincidencias.
- Exclusión de pacientes no coincidentes y de contenido clínico/motivo de cita.
- Respuesta `no-store`.
- Teclado, cancelación de solicitudes, APIs DOM seguras y bloqueo de selección obsoleta.
- Creación, conflicto de horario, cita previa y auditoría del flujo original conservados.

Resultado: **75 pruebas `pytest` aprobadas**, incluidas las 15 pruebas heredadas compatibles con `unittest`.
