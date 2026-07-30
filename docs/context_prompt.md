# Contexto y Requerimientos Generales (SGPN)

## 1. Resumen del Proyecto
El **Sistema de Gestión de Pacientes y Nutrición (SGPN)** optimiza la administración clínica mediante un entorno web moderno, seguro y robusto.

## 2. Características Funcionales Integradas Recientemente
1. **Módulo de Plantillas de WhatsApp:** Administración y catálogo de mensajes personalizados con soporte de variables dinámicas (`{nombre}`, `{dias}`).
2. **Selección de Plantilla Activa Única:** Restricción a nivel de base de datos y controlador para asegurar que solo una plantilla permanezca activa (`esta_activa = True`).
3. **Control de Estado de Citas (Pendiente vs Completada):** Al registrar una valoración antropométrica o historial clínico, el sistema cambia automáticamente el estado de la cita del día de `'pendiente'` a `'completada'`, actualizando la vista del Dashboard.
4. **Validación de Agenda y Horarios Ocupados:** Consulta asíncrona en tiempo real para bloquear horarios ya reservados en el `<select>`, previniendo empalmes y gestionando alertas al reagendar.
5. **Valoraciones Antropométricas Avanzadas:** Validación defensiva en backend con bloques `try/except` y flash messages, y validación en frontend con cambio automático de pestaña, `.focus()` y marcado visual.
