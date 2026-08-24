# KPI accionables y topbar persistente — versión 1.6.7

## Objetivo

Simplificar la parte superior del dashboard unificando información y captura, y mantener visibles las herramientas globales durante el desplazamiento sin modificar permisos, iconos, rutas clínicas o datos.

## KPI accionables

La fila independiente de Acciones rápidas fue retirada. Cada tarjeta se divide en dos controles hermanos:

| KPI | Enlace informativo | Acción explícita |
| --- | --- | --- |
| Pacientes registrados | Lista de pacientes | Nuevo paciente |
| Citas de hoy | Agenda del día dentro del dashboard | Agendar cita |
| Consultas pendientes | Lista de consultas | Nueva consulta |

No se utiliza una tarjeta completa como enlace que contenga otro botón, porque anidar controles interactivos produciría HTML inválido y una experiencia ambigua para teclado y lectores de pantalla.

Los estados informativos se adaptan a los datos:

- sin citas: **Sin citas programadas para hoy**;
- sin consultas pendientes: **Atención clínica al día**;
- pacientes del mes: singular o plural según el conteo;
- recepción: **Acceso clínico restringido**, sin enlace ni acción de Nueva consulta.

## Topbar persistente

El topbar sigue dentro del flujo del shell, pero deja de depender del desplazamiento general del documento:

1. `.shell-layout` y `.shell-main-wrapper` se limitan a `100dvh` con respaldo `100vh`;
2. el contenedor principal conserva `overflow-y-auto` y es la única región vertical desplazable;
3. el topbar usa `flex: 0 0 auto`, por lo que permanece visible;
4. se conserva `position: sticky` como protección adicional;
5. las vistas de impresión continúan ocultando la cabecera.

La altura mínima baja de 4.4 a 3.65 rem. Los botones globales pasan de 2.45 a 2.2 rem y se reduce el relleno del buscador. Breadcrumb, título, buscador, sede, notificaciones y tema permanecen disponibles.

## Navegación interna

Los enlaces a secciones del mismo documento, como **Ver agenda de hoy**, se reconocen como anclas locales. No activan el indicador de carga porque no existe una solicitud ni cambio real de página.

## Pruebas

La cobertura comprueba:

- ausencia de la fila Acciones rápidas;
- presencia exacta de tres acciones en una sesión clínica autorizada;
- enlaces informativos y etiquetas accesibles;
- shell limitado al viewport y área principal desplazable;
- altura compacta del topbar;
- exclusión de anclas locales del indicador de carga.

Resultado de aceptación esperado: **68 pruebas `pytest`**, incluyendo 15 casos compatibles con `unittest`.
