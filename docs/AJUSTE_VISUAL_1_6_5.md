# Ajuste visual y eliminación de duplicidades — versión 1.6.5

## Diagnóstico

### Pendientes duplicados

**Alertas clínicas y administrativas** y **Pendientes de atención** consumían exactamente las mismas colecciones:

- `pendientes_por_agendar`;
- `pacientes_sin_historial`;
- `pacientes_sin_valoracion`.

La diferencia era únicamente de presentación. Mantener ambos bloques aumentaba la densidad del dashboard y podía hacer creer que existían dos procesos independientes.

### Acción duplicada

**Nuevo paciente** aparecía como acción principal junto al saludo y nuevamente dentro de **Acciones rápidas**. Se conserva sólo la acción de la cuadrícula, junto al resto de operaciones frecuentes.

### Identidad global

La identidad ocupaba el extremo derecho del topbar y el sidebar sólo contenía un cierre de sesión separado. La referencia solicitada concentra la cuenta en el footer del sidebar, liberando el topbar para herramientas globales.

## Implementación

- Se retira **Alertas clínicas y administrativas**.
- **Pendientes de atención** conserva conteos, detalles expandibles, permisos y progreso de citas.
- **Próximas citas** aprovecha el ancho disponible con una cuadrícula adaptable.
- El saludo permanece, pero se elimina su botón duplicado y se reduce el espacio vertical.
- El sidebar cambia a fondo `#061f26`, bordes `#163b43`, hover `#10333b` y activo `#1d6c69`.
- El footer muestra avatar, nombre completo, rol/perfil y el disparador `...`.
- El menú de cuenta abre hacia arriba y conserva cédula condicional, cambio de contraseña y POST de cierre de sesión con CSRF.
- El topbar no contiene nombre, avatar ni menú de usuario.

## Controles preservados

- No cambian rutas, modelos, migraciones ni permisos.
- El menú inicia cerrado mediante `hidden`.
- Clic exterior y Escape lo cierran; Escape restaura el foco.
- Recepción continúa sin recibir información clínica protegida.
- El logotipo y los iconos canónicos no cambian.
- **Acompañamiento Intermedio (14-15 Días)** permanece completo.

## Validación

- Una sola aparición de **Nuevo paciente**.
- Ausencia de **Alertas clínicas y administrativas**.
- Una sola aparición de **Cerrar Sesión** dentro del shell autenticado.
- Identidad presente en `_sidebar.html` y ausente de `_header.html`.
- Resultado esperado: `67 passed` con `python -m pytest -q`.
