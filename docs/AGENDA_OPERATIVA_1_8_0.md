# Agenda operativa — versión 1.8.0

## Objetivo

La opción **Agenda y citas** deja de ser un ancla hacia el Dashboard y abre `/agenda`, una superficie de trabajo independiente. El Dashboard conserva el resumen del día y la acción rápida, mientras Agenda concentra navegación, disponibilidad, reagenda y cierre administrativo.

La implementación reutiliza `Cita`, la búsqueda privada de pacientes, el calendario de 21 días, los horarios configurados y la validación final bajo bloqueo. No crea una segunda fuente de datos ni agrega dependencias.

## Funciones disponibles

- Vista **Día** y **Semana**.
- Navegación Anterior, Hoy, Siguiente y fecha directa.
- Conteos del periodo por Programada, Atendida, No Asistió y Cancelada.
- Alta de cita con origen Agenda y regreso al día seleccionado.
- Reagenda del mismo registro y paciente.
- Consulta de disponibilidad excluyendo sólo el espacio de la cita editada.
- Cancelación con motivo obligatorio.
- Registro de atención o inasistencia cuando la fecha/hora ya ocurrió.
- Inicio de consulta para perfiles clínicos durante el día de la cita.
- Acceso al paciente desde cada fila.
- Estados vacíos accionables, tema oscuro y disposición adaptable.

## Responsabilidades por superficie

| Superficie | Responsabilidad |
| --- | --- |
| Dashboard | Resumen breve de citas de hoy y acceso rápido a alta |
| Agenda y citas | Operación diaria/semanal y cambios de estado |
| Detalle del paciente | Contexto individual y alternativa de reagenda |

## Permisos y privacidad

Todos los roles autenticados pueden consultar y administrar citas. El contenido se ajusta al principio de mínimo privilegio:

- `admin` y `medico`: identidad, motivo registrado e inicio de consulta.
- `recepcion`: identidad, horario, estado y acciones administrativas; el motivo clínico se sustituye por **Cita programada**.
- Recepción no recibe enlaces de inicio de consulta, notas, diagnósticos o recetas.

El servidor aplica los permisos; ocultar un control en la plantilla no sustituye las rutas clínicas protegidas.

## Máquina de estados

La única transición de cierre admitida parte de `Programada`:

```text
Programada ──> Atendida
           ├─> No Asistió
           └─> Cancelada
```

Reglas:

- Atendida y No Asistió requieren que la fecha/hora ya haya ocurrido.
- Cancelada requiere un motivo.
- Una cita terminal no vuelve a Programada y no admite otro cierre.
- Los estados terminales usan `estado = completada`.
- Los intentos inválidos responden HTTP 400 y se auditan como `denied`.

El registro de auditoría almacena cita, paciente, estado anterior/nuevo y presencia de observación; no replica el texto clínico completo.

## Reagenda

La ruta `/agenda/citas/<id>/reagendar`:

1. comprueba que la cita siga Programada;
2. comprueba que el paciente siga activo;
3. fija la identidad del paciente;
4. consulta horarios excluyendo el ID editado;
5. revalida fecha/hora dentro del bloqueo antes de guardar;
6. conserva el mismo ID y registra valores anterior/nuevo en auditoría.

Si otra solicitud ocupa el horario entre la consulta visual y el envío, el servidor rechaza la operación sin modificar la cita original.

## Pruebas incorporadas

- autenticación de `/agenda`;
- vista Día/Semana y parámetros inválidos;
- privacidad de Recepción e inicio clínico restringido;
- alta con origen Agenda;
- reagenda preservando ID y conflicto de último momento;
- rechazo de reagenda para una cita cerrada;
- cierre válido de una cita pasada;
- bloqueo de reapertura;
- bloqueo de cierre futuro;
- motivo obligatorio de cancelación;
- estado inválido y auditoría de denegación;
- JavaScript local sin inserción HTML y estilos de tema oscuro.

Resultado de aceptación: **89 pruebas pytest**, incluidas las 15 pruebas heredadas compatibles con `unittest`.

## Límites pendientes

La versión 1.8.0 usa un solo calendario general con bloques de 30 minutos entre 09:00 y 19:00. Todavía no implementa:

- horario distinto por profesional;
- duración variable;
- bloqueos, vacaciones o días inhábiles configurables;
- agenda por sede;
- recordatorios automáticos;
- sincronización con calendarios externos.

Estas funciones requieren definir primero reglas de asignación, solapamiento y migración; no deben agregarse como datos simulados.

