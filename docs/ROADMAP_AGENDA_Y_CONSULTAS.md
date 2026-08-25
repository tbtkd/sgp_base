# Estado de Agenda y roadmap del listado de consultas

## 1. Alcance de esta revisión

La versión 1.9.0 conserva la Agenda operativa 1.8.0, implementa el índice simplificado de Consultas y mantiene la columna **% Grasa** del grid **Historial de consultas** exclusivamente para usuarios cuyo perfil profesional efectivo sea `nutricion`. Medicina general y Odontología conservan Fecha, Peso, IMC, Tensión arterial, Frecuencia cardíaca y Acciones.

La regla se basa en el perfil autenticado, no en el autor de la consulta, y se aplica tanto al encabezado como a todas las celdas para no dejar una columna vacía. No se modifican los datos almacenados, la impresión de notas ni la captura antropométrica existente.

La Agenda y la simplificación de Consultas clínicas descritas a continuación están **implementadas**. El siguiente trabajo se concentra en pruebas de navegador real, medición con bases de mayor volumen y filtros futuros por profesional.

## 2. Diagnóstico de Agenda y citas

El problema del enlace a `#agenda-hoy` quedó resuelto: el sidebar abre `/agenda` y el Dashboard conserva sólo su resumen.

El sistema ya dispone de piezas que deben reutilizarse:

- agenda rápida con búsqueda privada de pacientes activos;
- calendario de 21 días y consulta de horarios disponibles;
- alta y reagenda con validación de conflictos;
- estados de cita y acciones desde la agenda del día;
- auditoría y protección contra doble envío.

Crear una segunda lógica de citas duplicaría validaciones y aumentaría el riesgo de inconsistencias. La mejora debe orquestar esas capacidades en una sola vista.

## 3. Agenda y citas — implementada en 1.8.0

### 3.1 Objetivo

El acceso del sidebar abre `/agenda`, mientras el Dashboard conserva el resumen de hoy.

### 3.2 Vista inicial recomendada

- Vista **Día** por defecto y alternativa **Semana**.
- Controles Anterior, Hoy y Siguiente.
- Fecha seleccionada visible y navegable con teclado.
- Listado de citas con estados Programada, Atendida, Cancelada y No Asistió.
- Estado vacío con acción **Agendar cita**, sin redirigir al padrón completo.
- Búsqueda bajo demanda del paciente previamente registrado.

### 3.3 Acciones útiles

- Agendar en un horario libre reutilizando el formulario y validaciones actuales.
- Abrir, reagendar o cancelar una cita existente.
- Marcar atención, cancelación o inasistencia mediante transiciones permitidas.
- Iniciar una consulta desde una cita para perfiles clínicos autorizados.
- Abrir el expediente del paciente sin exponer contenido clínico a Recepción.
- Mostrar el siguiente espacio disponible sin obligar a revisar manualmente todos los días.

### 3.4 Separación de responsabilidades

| Superficie | Responsabilidad propuesta |
| --- | --- |
| Dashboard | Resumen de citas de hoy y acceso rápido a una nueva cita |
| Agenda y citas | Operación diaria/semanal, disponibilidad y cambios de estado |
| Detalle del paciente | Próxima cita individual y reagenda contextual |

### 3.5 Reglas de seguridad e integridad

- Mantener autenticación, CSRF, validación de paciente activo y `Cache-Control: no-store`.
- Revalidar disponibilidad dentro de la transacción antes de guardar.
- No aceptar desde el navegador paciente, fecha, hora o estado sin validación de servidor.
- Definir una máquina de estados para impedir transiciones inválidas, por ejemplo Atendida → Programada.
- Auditar alta, reagenda, cancelación, inasistencia e inicio de consulta con usuario e IP.
- Recepción puede gestionar agenda, pero no leer diagnósticos, recetas o notas clínicas.
- Evitar incluir motivo clínico sensible en listados de agenda cuando no sea necesario.

### 3.6 Evolución posterior

Después de validar la primera versión pueden añadirse horarios por profesional, duración variable, días inhábiles, bloqueos y sedes. No conviene habilitarlos hasta definir responsables, reglas de solapamiento y migración de citas existentes.

## 4. Consultas clínicas — implementada en 1.9.0

### 4.1 Problema actual

La pantalla lista una fila por consulta. Un paciente con varias atenciones aparece repetido y las columnas Motivo/Diagnóstico convierten el índice en una vista clínica densa cuando su función principal debería ser localizar la nota más reciente.

### 4.2 Lista simplificada implementada

- Mostrar una sola fila por paciente con consulta registrada.
- Columnas: **Paciente**, **Fecha más reciente** y **Acción**.
- **Ver nota** abre el detalle de la consulta más reciente de ese paciente.
- El resultado se ordena por fecha descendente de forma predeterminada.
- El encabezado Fecha alterna descendente/ascendente y expone `aria-sort`.
- Un filtro por nombre busca sin distinguir mayúsculas y admite nombres/apellidos.
- Paginar a 25 pacientes para evitar cargar todo el historial al crecer la base.

### 4.3 Consulta de datos implementada

La consulta debe obtener la última nota por paciente de forma determinista, ordenando por `fecha`, `numero_cita` e `id`. No debe resolver duplicados en la plantilla ni cargar todas las filas para filtrarlas en JavaScript.

Parámetros sugeridos:

```text
/valoraciones/?q=laura&orden=fecha_desc&page=1
```

Los valores de `orden` se limitarán a una lista permitida; cualquier valor desconocido volverá al orden predeterminado.

### 4.4 Privacidad y permisos

- Mantener acceso exclusivo de `admin` y `medico`.
- No exponer motivo, diagnóstico ni prescripción en el índice.
- Escapar el texto buscado y parametrizar la consulta SQL/ORM.
- No incorporar endpoints JSON salvo que la navegación sin recarga aporte una mejora comprobable.

## 5. Pruebas de aceptación

### Agenda — implementadas

1. El sidebar abre una ruta dedicada y el Dashboard mantiene su resumen.
2. Día/semana muestran únicamente citas autorizadas y ordenadas.
3. Un espacio ocupado nunca puede confirmarse desde dos solicitudes concurrentes.
4. Paciente inactivo, fecha pasada, hora inválida y transición de estado inválida se rechazan.
5. Recepción administra la cita sin acceder a la nota clínica.
6. Reagenda, cancelación, inasistencia y atención generan auditoría; el inicio clínico conserva su auditoría al guardar la consulta.
7. Teclado, foco, estados vacíos/carga/error y tema oscuro funcionan sin depender sólo del color.

### Consultas clínicas

1. Cada paciente aparece una sola vez.
2. **Ver nota** abre la consulta más reciente correcta.
3. Empates de fecha se resuelven por turno e ID de forma determinista.
4. Búsqueda por nombre/apellidos admite mayúsculas, minúsculas y acentos esperados.
5. Fecha alterna ascendente/descendente y comunica `aria-sort`.
6. Parámetros inválidos no alteran SQL ni provocan error 500.
7. Paginación no repite ni omite pacientes entre páginas.
8. Anónimo y Recepción no acceden al listado clínico.

## 6. Siguiente orden recomendado

1. Ejecutar pruebas de navegador real para Agenda y Consultas en las resoluciones utilizadas por el consultorio.
2. Medir la consulta agregada con una copia anonimizada de mayor volumen antes de modificar índices.
3. Evaluar filtros por profesional únicamente cuando existan agendas separadas por responsable.
4. Definir horarios, bloqueos y duración antes de ampliar la Agenda a múltiples profesionales o sedes.
