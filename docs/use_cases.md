# Catálogo de Casos de Uso (SGPN)

## UC-01: Gestión de Pacientes
* **Descripción:** Registro, consulta y actualización de datos de pacientes en la clínica.

## UC-02: Agendamiento de Citas con Validación de Horarios
* **Descripción:** Programación de citas verificando disponibilidad horaria en tiempo real y previniendo empalmes o sobreescritura sin confirmación.

## UC-03: Cierre Automático de Cita del Día
* **Descripción:** Al capturar una valoración antropométrica o historial clínico, el sistema actualiza el estado de la cita asociada de `'pendiente'` a `'completada'`.

## UC-04: Administración del Catálogo de Plantillas de WhatsApp
* **Descripción:** Creación, edición y activación de plantillas de mensajes con la regla de **Plantilla Activa Única** (`esta_activa = True`).

## UC-05: Envío de Mensaje Personalizado por WhatsApp
* **Descripción:** Selección del paciente, inyección automática de variables (`{nombre}`, `{dias}`) sobre la plantilla activa, apertura de WhatsApp Web y registro en la bitácora de contacto.

## UC-06: Valoración Antropométrica Avanzada por Pestañas
* **Descripción:** Registro de mediciones corporales con validación defensiva en backend (Flask) y validación interactiva en frontend con cambio automático de pestaña y enfoque (`.focus()`) en caso de errores.
