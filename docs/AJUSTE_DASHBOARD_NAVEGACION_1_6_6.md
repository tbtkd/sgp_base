# Ajuste de dashboard y navegación — versión 1.6.6

## Objetivo

Reducir duplicidades visuales sin alterar rutas clínicas, permisos, datos ni iconos. El cambio aprovecha el espacio del dashboard, corrige el contraste del tema oscuro y ordena los accesos secundarios del sidebar.

## Cambios aplicados

1. **Próximas citas** y **Acompañamiento Intermedio (14-15 Días)** comparten una cuadrícula de dos columnas en escritorio. Debajo de 1100 px se apilan para conservar legibilidad.
2. Se retiraron **Crear receta** y **Ver expedientes** de Acciones rápidas. Sus flujos permanecen disponibles desde Recetas y Expedientes clínicos en el sidebar.
3. Recetas dejó de mostrarse como función planificada. El enlace abre la lista de consultas existente con `origen=recetas`; la cabecera explica que debe seleccionarse una consulta para gestionar sus folios.
4. Plantillas de mensajes, Usuarios y permisos, Auditoría y Configuración se agruparon bajo un `details/summary` llamado **Administración**. Los permisos Jinja existentes se mantienen: un médico no recibe administración de usuarios ni auditoría; recepción tampoco recibe accesos clínicos.
5. Configuración continúa como módulo planificado y no expone una ruta ficticia.
6. En modo oscuro, encabezados, filas, tablas, pendientes y próximas citas utilizan `#29464d` como separador. Se elimina el contraste blanco heredado del tema claro.

## Decisión de arquitectura de información

No conviene colocar Plantillas o Usuarios *dentro de Configuración*. Configuración representa preferencias del sistema; Plantillas es contenido operativo y Usuarios es administración de identidad y permisos. El grupo **Administración** reduce el número de entradas visibles sin confundir responsabilidades y admite incorporar futuras opciones administrativas de forma controlada.

## Accesibilidad y comportamiento

- El grupo Administración utiliza controles HTML nativos navegables con teclado.
- `summary` conserva foco visible y anuncia su estado expandido de forma nativa.
- La entrada activa conserva `aria-current="page"`.
- No se depende únicamente del color: títulos, distintivos y texto describen cada estado.
- No se añadió JavaScript ni una dependencia para el desplegable.

## Pruebas

La suite verifica que:

- las dos acciones duplicadas no aparecen en el dashboard;
- Próximas citas y Acompañamiento preceden a Pacientes recientes dentro de la misma fila;
- Recetas tiene URL funcional y deja de ser un módulo planificado;
- el contexto de Recetas muestra cabecera específica;
- Administración y sus estilos existen;
- el tema oscuro define separadores coherentes.

Resultado de aceptación: **68 pruebas aprobadas con `pytest`**, incluyendo los 15 casos heredados de `unittest`.
