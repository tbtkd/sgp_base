# Orden de receta y turno diario — versión 1.7.2

## Objetivo

Esta entrega resuelve dos problemas operativos sin cambiar roles, perfiles, sidebar, dashboard ni el formato regulatorio de la receta ordinaria:

1. Evitar que el profesional tenga que regresar al inicio de una receta larga para agregar otro medicamento.
2. Identificar la secuencia de atenciones del día con un turno global que no pueda manipularse desde el navegador.

## Medicamentos

Al pulsar **Agregar**, la tarjeta nueva se inserta en la parte superior y el foco pasa a **Denominación genérica**. La tarjeta conserva el siguiente número de captura aunque visualmente quede antes que las existentes. Por ejemplo, después de capturar 1 y 2, la nueva tarjeta superior se identifica como 3.

El formulario envía `orden_medicamento[]` en paralelo con las columnas de cada medicamento. El servidor verifica que:

- exista el mismo número de órdenes y filas;
- sean enteros entre 1 y 10;
- no se repitan;
- formen exactamente la secuencia `1..n`;
- cada medicamento conserve campos obligatorios y no duplique otra fila.

Antes de crear `RecetaMedicamento`, el servidor ordena por ese valor. La relación persiste en dicho orden y la hoja A4 usa `loop.index`, por lo que la salida muestra 1, 2, 3 aunque el formulario haya mostrado arriba la tarjeta más reciente. Los formularios anteriores que no envían el nuevo campo siguen siendo compatibles y se interpretan en su orden original.

## Turno diario

El rótulo **Número de consulta** cambia a **Turno diario**. Es un ordinal global para todas las consultas de una fecha:

| Fecha | Paciente | Turno |
| --- | --- | ---: |
| 24/08/2026 | Paciente A | 1 |
| 24/08/2026 | Paciente B | 2 |
| 24/08/2026 | Paciente C | 3 |
| 25/08/2026 | Paciente D | 1 |

El campo es de sólo lectura. Al cambiar la fecha, el navegador solicita una proyección a `/valoraciones/siguiente-numero`; la respuesta exige autenticación, valida que la fecha no sea futura y se marca `no-store`. Esa cifra no reserva el turno.

Al guardar, el controlador descarta cualquier número recibido, vuelve a consultar el siguiente valor dentro de un bloqueo compartido por los hilos de Waitress y confirma consulta/auditoría en la misma transacción. SQLite impone además la unicidad `(fecha, numero_cita)`. Un conflicto no sobrescribe datos y devuelve un mensaje recuperable.

La importación XLSX aplica la misma regla por cada fecha del archivo. Si una consulta se edita y cambia de fecha, conserva su ID pero recibe el siguiente turno del día destino; la bitácora registra fecha/turno anterior y nuevo.

## Migración de instalaciones existentes

Después del respaldo de arranque, `init_db()` detecta si falta la unicidad diaria. En una transacción `BEGIN IMMEDIATE`:

1. ordena las consultas por fecha, `created_at` e ID;
2. asigna valores temporales sin eliminar filas;
3. reconstruye `1..n` para cada fecha;
4. crea el índice único diario;
5. ejecuta `PRAGMA integrity_check` antes de confirmar.

La restricción legada por paciente puede permanecer físicamente en SQLite porque no contradice la nueva unicidad global. No se cambia ningún dato clínico, paciente, fecha o receta.

## Trazabilidad y conteo

Un turno ya asignado no se recicla. Si una nota sin receta se elimina o cambia de fecha, puede quedar un hueco. Renumerar notas posteriores cambiaría referencias históricas y afectaría auditoría; por eso no se realiza.

El número de pacientes atendidos se obtiene contando consultas de la fecha. `MAX(numero_cita)` sirve como último turno emitido, pero no como total definitivo cuando existen huecos. Si en el futuro se requiere distinguir pacientes únicos de consultas múltiples del mismo paciente, el reporte debe ofrecer ambos valores: `COUNT(*)` y `COUNT(DISTINCT paciente_id)`.

## Pruebas

```powershell
python -m pytest -q tests/test_prescriptions.py
python -m pytest -q tests/test_daily_consultation_sequence.py
python -m pytest -q
```

La suite cubre inserción superior, foco, orden manipulado/repetido, persistencia e impresión 1..n, asignación global, reinicio por fecha, autenticación/no-cache de la proyección, auditoría y migración sin pérdida.
