# Shell, navegación y tema — versión 1.6.4

> Documento base del shell. La ubicación vigente de la cuenta y la simplificación del dashboard se documentan en `AJUSTE_VISUAL_1_6_5.md`.

## Decisión de alcance

Esta fase moderniza la navegación sin crear módulos de negocio que todavía no existen. La aplicación continúa siendo Flask con renderizado del servidor: cambiar entre rutas recarga el contenido de manera controlada, mientras que sidebar móvil, popovers, selector de tema y pestañas de gráfica funcionan localmente sin recarga.

## Mapa de navegación

| Opción | Estado | Destino o comportamiento | Permiso |
| --- | --- | --- | --- |
| Dashboard | Operativo | `main.index` | Cualquier sesión |
| Pacientes | Operativo | Lista activa y búsqueda | Cualquier sesión |
| Agenda y citas | Operativo/contextual | Sección `#agenda-hoy` del dashboard | Cualquier sesión |
| Consultas | Operativo | Lista de consultas | Admin/Médico |
| Expedientes clínicos | Operativo | Lista de historiales | Admin/Médico |
| Recetas | Contextual | Mensaje “desde consulta”; no inventa índice global | Admin/Médico |
| Plantillas de mensajes | Operativo | Gestión de plantillas | Admin/Médico |
| Usuarios y permisos | Operativo | Gestión de usuarios | Admin |
| Auditoría | Operativo | Bitácora | Admin |
| Laboratorio | Planificado | Botón sin ruta | Admin/Médico |
| Hospitalización | Planificado | Botón sin ruta | Admin/Médico |
| Facturación | Planificado | Botón sin ruta | Cualquier sesión |
| Inventario | Planificado | Botón sin ruta | Cualquier sesión |
| Reportes | Planificado | Botón sin ruta | Cualquier sesión |
| Configuración | Planificado | Botón sin ruta | Cualquier sesión |
| Portal del paciente | Planificado | Botón sin ruta | Cualquier sesión |

Los botones planificados usan texto visible, `aria-disabled="true"` y un mensaje anunciado por `role="status"`; el estado no depende sólo del color.

## Top bar

- El buscador envía `busqueda` a la ruta existente de pacientes y acepta nombre, teléfono o correo.
- El selector de sede muestra **Consultorio principal** porque no existe un modelo multi-sede. Su panel explica el alcance en lugar de simular sedes.
- Notificaciones muestra conteo cero y un estado vacío hasta que exista un backend autorizado.
- El breadcrumb se determina por endpoint y no admite texto enviado por el usuario.
- El avatar abre un menú nativo cerrado con `hidden`; Escape restaura el foco.
- El tema se guarda como `sgpn-theme` en `localStorage`. Si el almacenamiento está bloqueado, la aplicación usa tema claro sin interrumpir el arranque.

## Tema y accesibilidad

El tema oscuro utiliza fondos azul petróleo (`#07191f`, `#10262d`), bordes teal grisáceos (`#24434b`) y acentos teal (`#2dd4bf`, `#5eead4`). La impresión fuerza tema claro. Los controles interactivos tienen `:focus-visible` de tres píxeles, nombres accesibles y estados `aria-expanded`/`aria-selected` sincronizados.

El sidebar móvil:

1. se abre desde un botón con `aria-controls`;
2. mueve el foco al primer elemento;
3. se cierra mediante X, fondo o Escape;
4. restaura el foco al disparador;
5. bloquea el desplazamiento del documento mientras está abierto.

## Dashboard integrado

- Saludo y fecha local.
- Acciones rápidas conectadas a rutas existentes; **Crear receta** dirige a consultas porque la receta depende de una consulta guardada.
- KPIs: pacientes registrados, citas de hoy y consultas pendientes para el día.
- Gráfica SVG local de siete días para citas/consultas y gráfica secundaria de altas de pacientes.
- Agenda del día, próximas citas ordenadas, pacientes recientes, tareas, alertas y actividad real.
- Bloque **Acompañamiento Intermedio (14-15 Días)** conservado con sus acciones.
- Recepción no recibe datos ni accesos clínicos restringidos.
- No existe KPI de ingresos ni tareas inventadas de laboratorio/inventario.

## Estados de interfaz

- Vacíos: agenda, próximas citas, notificaciones, pacientes, actividad y acompañamiento explican por qué no hay contenido.
- Carga: una barra superior aparece al iniciar una navegación o envío de formulario.
- Confirmación: se conservan mensajes flash tipados y confirmaciones específicas de las acciones existentes.
- Módulo planificado: mensaje local sin petición al servidor.

## Siguiente roadmap

1. Diseñar modelos, permisos y casos de uso antes de habilitar cualquiera de los módulos planificados.
2. Sustituir los recursos CDN restantes por archivos locales y endurecer CSP.
3. Incorporar pruebas de navegador para contraste calculado, recorridos de teclado y responsive real.
4. Evaluar navegación parcial sólo después de definir contratos de caché, CSRF, historial del navegador y manejo de errores; no convertir el sistema en SPA por apariencia.
5. Diseñar multi-sede con aislamiento de datos y permisos antes de convertir el selector informativo en un control mutable.

## Validación

La aceptación automatizada comprueba shell, tema, controles ARIA, módulos planificados, permisos del dashboard, orden de próximas citas y conservación de la marca. Comando oficial:

```bash
python -m pytest -q
```

Resultado esperado: `67 passed`.
