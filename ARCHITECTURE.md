# Arquitectura del Sistema (SGPN)

## 1. Arquitectura de Software
El sistema sigue un patrón modular basado en **MVC (Modelo-Vista-Controlador)** desacoplado con Flask Blueprints, promoviendo la mantenibilidad y escalabilidad del código.

- **Modelos (`app/models/`):** Entidades de ORM SQLAlchemy (`Paciente`, `ValoracionAntropometrica`, `Cita`, `Pago`, `HistorialClinico`, `BitacoraWhatsApp`, `Usuario`). Contienen lógica de negocio y métodos de consulta estáticos.
- **Controladores / Rutas (`app/controllers/` y `app/routes/`):** Gestionan las peticiones HTTP, validaciones defensivas de formularios, llamadas a modelos y renderizado de vistas o respuestas JSON.
- **Vistas (`app/templates/`):** Plantillas Jinja2 organizadas por dominios (`pacientes/`, `valoraciones/`, `citas/`, `auth/`, `base/`, `dashboard/`), utilizando subcarpetas `partials/` y `tabs/` para componentes reutilizables.

## 2. Esquema de Base de Datos y ORM
- **Base de datos:** SQLite (`instance/sgpn_nutricion.db`).
- **ORM:** Flask-SQLAlchemy con gestión explícita de sesiones (`db.session.add`, `commit`, `rollback` en bloques `try/except`).
- **Relaciones principales:**
  - `Paciente` (1) -> (N) `ValoracionAntropometrica`
  - `Paciente` (1) -> (N) `Cita`
  - `Paciente` (1) -> (N) `Pago`
  - `Paciente` (1) -> (N) `BitacoraWhatsApp`

## 3. Estándares de Frontend y UI/UX
- **Contenedores y Layout:** Uso de contenedores fluidos (`max-w-7xl` / `max-w-8xl`), barra lateral colapsable y diseño responsivo.
- **Interactividad:** Alpine.js para gestión de estado local en modales, pestañas de formularios y validaciones dinámicas en cliente.
- **Validación de Formularios por Pestañas:**
  - Intercepción de eventos de submit.
  - Auditoría de campos requeridos distribuidos en múltiples pestañas.
  - Navegación automática a la pestaña oculta que contenga el primer error, aplicación de `.focus()` en el input afectado y marcado visual con clases de error.
- **Estilos:** Tailwind CSS complementado con componentes modulares en `app/static/css/components/`.
