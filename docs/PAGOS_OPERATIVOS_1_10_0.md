# Pagos operativos — versión 1.10.0

## Objetivo

La versión 1.10.0 transforma el registro mínimo de cobros en un módulo operativo trazable. Mantiene el sistema como herramienta local y no pretende sustituir contabilidad, facturación CFDI, cuentas por cobrar ni un corte formal de caja.

## Modelo monetario

- `monto_centavos` es la fuente autoritativa para validaciones, sumas y presentación.
- `monto` permanece como espejo `Float` únicamente para compatibilidad con instalaciones anteriores.
- La moneda vigente es `MXN`.
- Todo pago nuevo debe ser mayor que cero, admitir máximo dos decimales y no exceder $10,000,000.00.
- Cada movimiento recibe `folio` único y `operation_key` único.
- `operation_key` impide que un doble clic o reintento del mismo formulario inserte dos movimientos.
- Se conserva el usuario que registró el pago y, cuando se selecciona explícitamente, la cita relacionada.

El **método de pago** describe cómo ingresó el dinero —efectivo, tarjeta, transferencia u otro— y sirve para desglose y conciliación operativa. No decide si debe emitirse una factura. Una futura integración fiscal necesita un indicador independiente como `requiere_factura`, datos fiscales, conceptos tributarios y el flujo CFDI correspondiente.

## Estados e inmutabilidad

| Estado | Uso | Se incluye en totales |
| --- | --- | --- |
| `vigente` | Pago confirmado y operativo | Sí |
| `cancelado` | Movimiento invalidado por Administración, conservando el original | No |
| `requiere_revision` | Registro legado incompleto o monetariamente no confiable | No |

### Cómo entra un pago a “Requiere revisión”

Este estado no se asigna a un pago nuevo. El formulario actual rechaza importes vacíos, en cero, negativos, excesivos o con más de dos decimales, así como conceptos vacíos y métodos no permitidos.

Sólo aparece en dos situaciones:

1. Durante la actualización desde una base anterior, cuando un pago guardado previamente no tiene importe válido, concepto, método reconocido o moneda MXN confiable.
2. En los datos de demostración, donde se crea deliberadamente un caso incompleto para validar la pantalla.

### Cómo se revisa actualmente

La aplicación no puede reconstruir un importe o concepto que nunca quedó guardado. Por eso la revisión es administrativa y debe basarse en un comprobante, terminal bancaria, transferencia, recibo interno u otra evidencia disponible:

1. Administración amplía el rango de fechas y filtra el estado **Requiere revisión**.
2. Identifica paciente y folio, y compara el movimiento con la evidencia disponible.
3. Si se confirma el cobro y se conocen sus datos correctos, cancela el registro incompleto con un motivo claro y registra un pago nuevo completo.
4. Si se confirma que el movimiento no representa un cobro válido, lo cancela y documenta el motivo.
5. Si todavía no existe evidencia suficiente, lo deja en **Requiere revisión**. No se inventan importes ni se incluye el movimiento en los totales.

No existe una acción de “aprobar” o editar el registro anterior: cambiarlo directamente eliminaría la evidencia de qué información recibió realmente la actualización. La cancelación conserva el original y el nuevo pago, cuando corresponde, recibe su propio folio y responsable.

Los pagos no se editan ni eliminan. Si una captura es incorrecta, Administración debe cancelarla con un motivo mínimo de cinco caracteres y registrar un movimiento nuevo. La cancelación conserva importe, concepto, método, folio, fecha, autor original, responsable y momento de cancelación. La confirmación explica que el pago no se borrará, ofrece **Volver** como salida segura y rotula la acción definitiva como **Sí, cancelar pago**. Al confirmar, la interfaz vuelve al renglón por su folio y lo resalta; si el filtro anterior lo ocultaría, se retira ese filtro para no perder de vista el movimiento.

No se implementa todavía el estado **Reembolsado**. Un reembolso futuro deberá representarse como un movimiento separado enlazado con el pago original, después de definir reglas de caja y responsabilidades.

## Permisos

| Operación | Administración | Medicina | Recepción |
| --- | --- | --- | --- |
| Registrar desde el paciente | Sí | Sí | Sí |
| Ver historial del paciente | Sí | Sí | Sí |
| Abrir módulo global | Sí | No | Sí |
| Consultar totales y desglose | Sí | No | Sí |
| Resumen diario/mensual | Sí | No | No |
| Exportar CSV global/individual | Sí | No | No |
| Cancelar movimiento | Sí | No | No |

La autorización reside en el servidor. Ocultar un control en la plantilla no sustituye `roles_required`.

## Flujos de interfaz

### Detalle del paciente

1. Captura fecha, monto, concepto y método.
2. Opcionalmente relaciona una de las últimas veinte citas del mismo paciente. Tener una cita no crea el vínculo: el usuario debe seleccionar la atención que originó el cobro.
3. El servidor verifica CSRF, UUID de operación, fecha no futura, importe exacto, catálogo, paciente y pertenencia de la cita.
4. Se crea el pago y su auditoría dentro de la misma transacción.
5. El detalle muestra el último pago vigente con monto, fecha y folio.
6. El historial conserva hasta los cincuenta movimientos más recientes.

### Módulo global

`GET /pagos/` inicia con el día actual y ofrece:

- total vigente del filtro;
- número de movimientos;
- conteo de cancelados y pendientes de revisión;
- desglose vigente por efectivo, tarjeta, transferencia y otro;
- búsqueda normalizada por términos de nombre completo, apellidos, folio o concepto; cada palabra puede coincidir en una columna distinta;
- filtros por rango máximo de 366 días, método y estado;
- paginación de 25 movimientos.

Los agregados excluyen cualquier pago que no esté `vigente`.

### Reportes administrativos

Administración puede elegir **Por día** o **Por mes**. El resumen muestra periodo, movimientos, cancelados y total vigente usando exactamente el filtro activo. No es un corte de caja: no contiene apertura, retiros, diferencias o conciliación.

Las dos salidas disponibles son:

- **Exportar filtro CSV**, con búsqueda, fechas, método y estado vigentes;
- **Exportar historial CSV**, desde el detalle de un paciente y con todos sus movimientos conservados.

Ambas rutas son exclusivas de Administración, limitan el resultado a 10,000 filas, usan UTF-8 con BOM para Excel, responden `Cache-Control: no-store` y neutralizan celdas cuyo primer carácter sea `=`, `+`, `-`, `@`, tabulador o retorno de carro. Cada descarga genera `EXPORTAR_PAGOS` con alcance y número de filas, sin copiar el importe a la metadata.

## Migración de bases anteriores

La migración `payments_v110` se ejecuta después del respaldo de arranque y antes de la migración aditiva general:

1. Inicia `BEGIN IMMEDIATE` y crea `pagos_migration_v110`.
2. Convierte importes válidos mediante `Decimal` y redondeo `ROUND_HALF_UP`.
3. Conserva identificadores, paciente, fecha y marcas de tiempo.
4. Genera folios y claves de operación deterministas para filas legadas.
5. Normaliza métodos desconocidos a `otro` y marca la fila para revisión.
6. Marca como `requiere_revision` cualquier importe nulo, cero, negativo, excesivo o cualquier fila sin concepto/método confiable.
7. Cambia la llave del paciente de `ON DELETE CASCADE` a `ON DELETE RESTRICT`.
8. Establece `ON DELETE SET NULL` para usuarios y citas opcionales.
9. Recrea índices y unicidad de folio/operación.
10. Ejecuta `foreign_key_check` e `integrity_check` antes del `commit`.
11. Reactiva `PRAGMA foreign_keys=ON` antes de devolver la conexión al pool.

La migración falla de forma segura si la integridad no puede demostrarse. No borra filas para forzar el arranque.

## Auditoría

- `REGISTRAR_PAGO`: pago confirmado, paciente, folio y cita opcional.
- `RECHAZAR_PAGO_DUPLICADO`: reintento con una clave de operación ya utilizada.
- `CANCELAR_PAGO`: éxito o denegación, responsable, paciente y estado anterior.
- `EXPORTAR_PAGOS`: descarga global o por paciente, periodo y cantidad de filas.

La auditoría no guarda credenciales ni copia información clínica. El monto completo no se replica en `metadata_json`.

## Pruebas específicas

`tests/test_payments.py` valida:

- centavos exactos y formatos monetarios rechazados;
- folio, responsable, cita y doble envío;
- rechazo de una cita perteneciente a otro paciente;
- historial, último pago vigente e inmutabilidad tras cancelar;
- permisos de Administración, Medicina y Recepción;
- filtros, búsqueda sin acentos y por nombre completo, y totales;
- resumen diario/mensual, RBAC de exportación y CSV neutralizado contra fórmulas;
- cancelación duplicada y retorno visible al movimiento aun cuando el filtro previo lo ocultaría;
- rangos invertidos o mayores de 366 días;
- migración de filas válidas e incompletas;
- `ON DELETE RESTRICT`, tema oscuro y contrato de interfaz.

## Evolución posterior

La siguiente fase financiera debe diseñar, por separado:

- exportación XLSX nativa, si se requiere además del CSV seguro disponible;
- recibo imprimible no fiscal;
- reembolsos como movimientos relacionados;
- catálogo de servicios, cargos, descuentos, adeudos y aplicaciones;
- corte de caja con apertura, cierre, diferencias, retiros y responsable;
- comparativos entre periodos y tableros configurables, sin confundirlos con contabilidad.

Hasta contar con cargos y aplicaciones, el historial de pagos no debe llamarse **estado de cuenta**. Hasta definir apertura y conciliación, el resumen diario no debe llamarse **corte de caja**.

Un asistente masivo para pagos anteriores incompletos sólo debe considerarse si una instalación real presenta un volumen significativo. Para los casos aislados, el filtro, la cancelación motivada y el alta de un nuevo pago ya proporcionan un tratamiento seguro.
