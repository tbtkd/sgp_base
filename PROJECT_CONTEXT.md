# PROJECT_CONTEXT.md: Memoria Viva del Sistema

## AI INSTRUCTION
> Antes de realizar cualquier modificación al código, lee este archivo para alinearte con las decisiones arquitectónicas, reglas de UI/UX y modelos de datos ya establecidos.

---

## 1. Changelog / Historial de Logros
- **Gestión Integral de Pacientes:** CRUD completo, listados activos/inactivos, búsqueda en tiempo real, cambio de estado asíncrono y vista de detalle modular.
- **Valoraciones Antropométricas:** Módulo completo de registro por pestañas con validación defensiva en backend (try/except, flash) y validación en frontend (interceptación de submit, cambio automático de pestaña, `.focus()` en el campo con error y marcado visual).
- **Importación Masiva Excel:** Procesamiento de archivos `.xls` / `.xlsx` mediante OpenPyXL para carga de valoraciones con detección de duplicados y manejo de errores.
- **Agenda y Citas Médicas:** Programación de citas, validación de disponibilidad horaria por día y hora (9:00 AM a 7:00 PM), control de estado pendiente/completada y modales de advertencia al intentar reagendar sobre una cita pendiente existente.
- **Control Financiero y Bitácora:** Registro de pagos de pacientes y bitácora de acompañamiento por WhatsApp con línea de tiempo y acceso directo a chat.

---

## 2. Reglas Fijas de Diseño y Desarrollo
1. **Validación Defensiva Obligatoria:** Todo endpoint que reciba datos de formularios debe validar integridad, tipos de datos y restricciones de negocio dentro de bloques `try/except` con llamadas a `flash()` y rollback de SQLAlchemy.
2. **Interactividad con Alpine.js:** Los formularios complejos por pestañas y modales deben utilizar Alpine.js para la gestión de estados locales, cambio de pestañas, enfoque automático (`.focus()`) y validación previa al envío.
3. **Consistencia de Estilos:** Uso estricto de Tailwind CSS y clases modulares para tarjetas, tablas, formularios y botones.
4. **Manejo de Citas:** Las citas activas se gestionan consultando estados `pendiente` mediante métodos estáticos en el modelo `Cita`.

---

## 3. Backlog y Próximos Pasos
- **Fase 1 (Completada):** Estructura base, pacientes, valoraciones con pestañas, citas y pagos.
- **Fase 2 (Próxima):** Reportes PDF avanzados de evolución antropométrica por paciente.
- **Fase 3 (Futura):** Panel de estadísticas y métricas generales del consultorio nutricional para el Dashboard principal.
