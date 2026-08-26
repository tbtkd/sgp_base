# Análisis de etapa y roadmap visual — versión 1.6.2

> Estado 1.12.0: la Fase 1 quedó completada. Los recursos son locales, Alpine/CDN fueron retirados, la CSP no usa `unsafe-inline`, las copias usan cifrado autenticado y existe una prueba E2E Playwright opcional. Los hallazgos siguientes se conservan como registro histórico de la decisión.

## 1. Alcance del ajuste

La cabecera superior se conserva porque concentra el contexto de la página y la cuenta autenticada. Lo que debía permanecer oculto era el panel detallado de la cuenta; además, el saludo del dashboard duplicaba innecesariamente la identidad ya visible a la derecha.

### Causa raíz verificada

1. Para `main.index`, `_header.html` asignaba `titulo_modulo = none`. El fallback no ocultaba el contenido: renderizaba deliberadamente `Bienvenido, <nombre>`.
2. El panel de cuenta dependía de `x-show="open"`. Ese atributo no tiene significado para el navegador sin Alpine; cuando el recurso CDN no se inicializaba o lo hacía tarde, el contenido podía aparecer como HTML normal.
3. `x-cloak` reducía el destello sólo mientras su regla CSS estuviera disponible, pero no convertía el estado cerrado en una propiedad nativa del elemento.

### Corrección aplicada

- El dashboard muestra **Panel clínico** y su subtítulo; no vuelve a mostrar el nombre de la cuenta a la izquierda.
- El detalle se entrega con el atributo HTML `hidden`, por lo que inicia cerrado antes de ejecutar JavaScript.
- Un controlador local abre el panel únicamente al pulsar la cuenta, lo cierra con Escape o clic exterior y sincroniza `aria-expanded`.
- Si JavaScript falla, el estado seguro es cerrado. La identidad resumida continúa en el botón derecho y el sidebar permanece dedicado a navegación.

## 2. Dictamen de la etapa actual

La base funcional está madura para pruebas y para un piloto de una sola estación local controlada. Autenticación, roles, CSRF, validación de servidor, auditoría, respaldos, migraciones, citas, consultas, perfiles profesionales y receta ordinaria tienen cobertura automatizada. No es todavía una plataforma clínica de red ni multi-consultorio.

### Fortalezas

- Separación clara entre rol de acceso y perfil clínico.
- Autorización autoritativa en backend para contenido clínico, receta y antropometría.
- Persistencia compatible con PyInstaller, respaldos verificados y migraciones conservadoras.
- Recetas emitidas inmutables, con adicionales y sustituciones trazables.
- Recuperación local de administradores sin enviar contraseñas a logs o auditoría.
- Vistas de impresión clínica separadas del shell de la aplicación.
- Suite unificada y controles estáticos ejecutables sin tocar la base real.

### Riesgos y deuda técnica

| Prioridad | Hallazgo | Impacto | Tratamiento recomendado |
| --- | --- | --- | --- |
| Alta | Tailwind, Alpine, FontAwesome y SweetAlert aún tienen dependencias CDN en el shell | Un ejecutable local puede perder estilos o interacción sin red; la CSP requiere excepciones | Compilar y empaquetar todos los recursos localmente |
| Alta | La CSP todavía admite `unsafe-inline` y orígenes externos | Aumenta superficie frente a inyección y dificulta una política estricta | Retirar scripts/estilos inline y cerrar la CSP tras autocontener el frontend |
| Alta | No existen pruebas E2E con navegador real | Flask verifica HTML y permisos, pero no pintura, foco, zoom, impresión o eventos reales | Incorporar una sola suite Playwright para flujos visuales críticos |
| Media | Permanecen componentes Alpine legados | Comportamiento desigual ante una CDN no disponible | Migrar sidebar móvil, menús de tablas y carga XLSX a controladores locales |
| Media | CSS y patrones visuales están repartidos entre Tailwind, estilos locales y plantillas legadas | Inconsistencias de espaciado, controles y estados | Crear tokens y componentes comunes antes del rediseño |
| Media | SQLite está orientado a una estación y concurrencia limitada | No cubre operación remota o multi-consultorio segura | Mantener localhost; rediseñar arquitectura antes de exponer en red |
| Alta antes de producción | La base activa no tiene cifrado transparente; los respaldos ya se cifran en 1.12 | Exposición de datos clínicos si se pierde el equipo con la base activa | Motor SQLite cifrado, migración y rotación de llaves verificadas |

## 3. Roadmap visual propuesto

### Fase 0 — corrección de cabecera (completada en 1.6.2)

- Título del módulo sin identidad duplicada.
- Panel de cuenta cerrado por HTML nativo.
- Interacción local, accesible y con fallo seguro.
- Regresión automatizada de la estructura de la cabecera.

### Fase 1 — frontend autocontenido (completada en 1.10.1)

- Compilar Tailwind y retirar el script CDN.
- Empaquetar iconos localmente o sustituirlos por SVG internos controlados.
- Reemplazar los usos restantes de Alpine y SweetAlert por módulos locales pequeños.
- Eliminar `unsafe-inline` y orígenes CDN de la CSP cuando ya no sean necesarios.
- Confirmar funcionamiento completo sin conexión dentro del ejecutable.

### Fase 2 — sistema visual común

- Definir tokens de color, espaciado, radios, tipografía, sombras y estados de foco.
- Unificar encabezados de página, botones, campos, tablas, pestañas, modales y estados vacíos.
- Reservar rojo para error/peligro, ámbar para advertencia y teal para acción principal.
- Establecer densidades coherentes para escritorio y resoluciones pequeñas.

### Fase 3 — panel y navegación

- **Dashboard completado en 1.6.3:** cuadrícula adaptable, tarjetas operativas, agenda, gráfica local, pacientes recientes, pendientes y actividad.
- **Dashboard completado en 1.6.3:** tres indicadores reales y estados vacíos accionables, sin KPI de ingresos.
- Revisar sidebar colapsable, navegación móvil y persistencia de la sección activa.
- Mantener la identidad únicamente en el top bar y evitar cualquier dato de paciente en esa zona global.

### Fase 4 — flujos clínicos

- Aplicar la misma jerarquía visual a paciente, historial, consulta, receta, pagos y citas.
- Usar barra de progreso o secciones con resumen en formularios clínicos extensos.
- Reforzar etiquetas de requerido/opcional y errores junto al campo correspondiente.
- Normalizar badges de estado y acciones destructivas con confirmación contextual.

### Fase 5 — accesibilidad, impresión y regresión visual

- Validar teclado completo, foco visible, lectores de pantalla, contraste y zoom al 200 %.
- Probar las resoluciones de escritorio y móvil soportadas.
- Añadir pruebas de navegador para login, menú de cuenta, citas, pestañas, receta e impresión.
- Comparar capturas de las hojas A4 y verificar saltos de página en Chrome/Edge.

### Fase 6 — preparación operativa

- Cifrado en reposo y administración de llaves.
- Pruebas periódicas de restauración en otra estación.
- Política de consentimiento, retención, acceso y eliminación de expedientes.
- Firma/cierre de notas y revisión jurídica de receta y especialidad antes de producción.

## 4. Criterios de aceptación del siguiente ciclo visual

| ID | Criterio |
| --- | --- |
| VIS-01 | La aplicación inicia y opera sin acceso a Internet |
| VIS-02 | No quedan scripts o estilos funcionales servidos desde CDN |
| VIS-03 | La CSP no requiere `unsafe-inline` ni orígenes externos de interfaz |
| VIS-04 | Sidebar, cuenta, modales y pestañas operan con teclado y foco visible |
| VIS-05 | No existe identidad duplicada entre top bar y sidebar |
| VIS-06 | Las notas y recetas A4 conservan contenido y saltos de página |
| VIS-07 | Una suite de navegador cubre los flujos críticos sin duplicar las pruebas de servidor |

## 5. Próximo lote recomendado

Completado el frontend autocontenido en 1.10.1, el siguiente ciclo visual puede concentrarse en tokens/componentes comunes y regresión visual, sin reintroducir dependencias externas.
