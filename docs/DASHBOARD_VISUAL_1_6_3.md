# Dashboard clínico — especificación visual 1.6.3

> Documento histórico. El shell y las ampliaciones vigentes del dashboard se documentan en `SHELL_NAVEGACION_1_6_4.md`.

## Alcance

El cambio afecta únicamente el contenido central de `dashboard/index.html`. El top bar, sidebar, logotipo PNG, icono ICO y sus clases permanecen idénticos a 1.6.2. La referencia visual se adapta a la paleta clara vigente para evitar un tema oscuro aislado dentro de la aplicación.

## Composición implementada

1. Fecha local, saludo contextual y acceso a **Nuevo paciente**.
2. Tres KPIs: pacientes activos, citas de hoy y consultas del mes.
3. Agenda diaria con hora, paciente, motivo, estado y acciones autorizadas.
4. Resumen SVG de altas de pacientes durante seis meses.
5. Tabla de pacientes recientes con expediente y última consulta.
6. Pendientes expandibles: agendar, consulta vencida y expediente sin historial.
7. Actividad reciente de altas y consultas.
8. Bloque completo de **Acompañamiento Intermedio (14-15 Días)**.

No se implementa el KPI de ingresos ni se inventan tareas de laboratorio, inventario o módulos que todavía no existen.

## Datos y permisos

| Elemento | Fuente | Recepción |
| --- | --- | --- |
| Pacientes activos y altas | `pacientes` | Visible |
| Citas y progreso del día | `citas` | Visible |
| Consultas del mes | `valoracion_antropometrica` | Sólo muestra acceso restringido |
| Sin consulta / historial pendiente | Expediente clínico | Oculto |
| Actividad de consultas | Consultas clínicas | Oculto |
| Iniciar consulta | Ruta clínica protegida | Oculto |

Las listas están limitadas y la gráfica se construye en servidor. No se agregó una dependencia de gráficos ni solicitudes de red adicionales.

## Comportamiento responsivo

- Tres KPIs en escritorio y una columna en móvil.
- Agenda y resumen se apilan por debajo de 1100 px.
- Tablas conservan desplazamiento horizontal sin deformar el shell.
- Actividad pasa de dos columnas a una.
- Se respeta `prefers-reduced-motion`.

## Criterios de aceptación

- El texto **Ingresos del mes** no existe en el HTML.
- Los tres KPIs coinciden con registros persistidos.
- Los seis bloques principales y Acompañamiento se renderizan con y sin datos.
- Recepción no recibe contenido clínico restringido.
- Las acciones de cita conservan CSRF mediante el interceptor local existente.
- Los hashes de header, sidebar, PNG e ICO permanecen sin cambios.
- La suite completa mantiene 65 pruebas aprobadas.
