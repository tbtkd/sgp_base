# Software Requirements Specification (SRS) - Sistema de Gestión de Pacientes y Nutrición (SGPN)

## 1. Introducción y Propósito
### 1.1 Propósito
Desarrollar un sistema web que permita la gestión integral de pacientes en un consultorio nutricional, facilitando el seguimiento de valoraciones antropométricas y control de historiales clínicos, agendamiento de citas, control de pagos y comunicaciones con pacientes.

### 1.2 Alcance
El sistema debe permitir el registro y seguimiento de pacientes, gestión de usuarios, valoraciones antropométricas avanzadas, historial clínico, control de pagos, plantillas de mensajes de WhatsApp y una estricta máquina de estados de citas.

---

## 2. Requerimientos Funcionales

### RF-01: Gestión de Pacientes
- Alta de nuevos pacientes con datos personales.
- Edición de información de pacientes.
- Cambio de estado (activo/inactivo/inhabilitación lógica).
- Búsqueda y filtrado de pacientes.
- Visualización separada de pacientes activos e inactivos.
- Carga masiva de pacientes e historiales desde archivos Excel.

### RF-02: Valoraciones Antropométricas
- Registro de medidas corporales completas (peso, estatura, perímetros, pliegues cutáneos, bioimpedancia).
- Cálculo automático de IMC, % grasa, masa magra y somatotipo.
- Registro de signos vitales (tensión arterial, frecuencia cardiaca).
- Seguimiento histórico de medidas.

### RF-03: Historial Clínico
- Registro de antecedentes médicos, heredofamiliares y patológicos.
- Control de medicamentos y suplementos.
- Seguimiento de actividad física y recordatorio de 24 horas.
- Registro de hábitos alimenticios.

### RF-04: Control de Pagos y Citas
- Registro de pagos por consulta y estatus de adeudos.
- Agendamiento de citas con validación de horarios disponibles en tiempo real.
- Máquina de estados de citas (Programada, Asistido, No Asistió, Cancelada) con registro de motivos.

---

## 3. Requerimientos No Funcionales

### RNF-01: Usabilidad
- Interfaz intuitiva y responsiva con Tailwind CSS y Alpine.js.
- Mensajes de error claros y modales estilizados en lugar de alertas nativas.
- Menús desplegables inteligentes con posicionamiento condicional anti-desborde (`top-full` / `bottom-full`).

### RNF-02: Rendimiento
- Tiempo de respuesta óptimo con SQLite y SQLAlchemy.
- Soporte para múltiples usuarios y control de instancia única para evitar bloqueos por concurrencia (`database is locked`).

### RNF-03: Seguridad
- Validación de datos en frontend y backend.
- Control de acceso por roles (`nutriologa`, `administrador`) y estatus de usuario (activo/inhabilitado).

---

## 4. Reglas de Negocio

### RN-01: Pacientes y Usuarios
- Correo electrónico único por paciente; teléfono de 10 dígitos; estado inicial siempre activo.
- Los usuarios inhabilitados tienen el acceso denegado inmediatamente mediante validaciones en `Flask-Login` y `@login_required`.

### RN-02: Valoraciones y Citas
- IMC calculado automáticamente; prohibido duplicar valoraciones en la misma fecha.
- Al registrar una valoración antropométrica o historial clínico, el sistema actualiza automáticamente el estado de la cita asociada del día a `'Asistido'` / `'completada'`.

### RN-03: Plantillas de WhatsApp
- Restricción de **Plantilla Activa Única** (`esta_activa = True`). Al activar una plantilla, el sistema desactiva automáticamente las demás.
