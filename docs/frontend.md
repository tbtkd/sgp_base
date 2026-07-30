# Guía de Frontend y UI/UX - Sistema de Gestión de Pacientes y Nutrición (SGPN)

## 1. Arquitectura y Componentes UI/UX
El frontend utiliza **Jinja2** para plantillas modulares, **Tailwind CSS** para un diseño responsivo con la paleta verde esmeralda (`#059669`), y **Alpine.js** para la interactividad y estado local.

### Características Clave de Interfaz:
- **Tablas con Menús Flotantes (`⋮`)**: 
  - Las acciones secundarias utilizan menús desplegables con botón de tres puntos.
  - **Posicionamiento Inteligente**: Posicionamiento condicional (`top-full` por defecto y `bottom-full` en los registros finales de la tabla) para evitar desbordes visuales y barras de desplazamiento verticales.
- **Actualización Dinámica AJAX**: Contadores y tarjetas de resumen actualizados en tiempo real sin recargar la página.
- **Redirección de Usuarios**: Flujo optimizado que redirige directamente al panel de gestión tras el registro de nuevos usuarios.
- **Ventana de Alerta de Inicio**: Interfaz HTML estilizada (`error_inicio.html`) en caso de detectar el sistema abierto en otra pestaña o puerto ocupado.
