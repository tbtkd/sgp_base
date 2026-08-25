# Escenarios demo de Pagos 1.10

Todos los registros son ficticios. Cárgalos únicamente en una base de validación:

```powershell
$env:SGPN_DEMO_PASSWORD = "DemoLocal!2026-Segura"
python seed_demo.py --confirm
Remove-Item Env:SGPN_DEMO_PASSWORD
```

La carga crea cinco cuentas (`demo_admin`, `demo_medico`, `demo_dentista`, `demo_nutricion` y `demo_recepcion`), seis pacientes, siete citas y dieciocho pagos. Es idempotente: repetirla no duplica los escenarios.

## Matriz esperada

| Escenario | Dato para localizarlo | Resultado esperado |
| --- | --- | --- |
| Búsqueda por nombre completo | Patricia Ramírez Soto | **Ver en Pagos** y el filtro completo muestran sus movimientos |
| Cita programada relacionada | Consulta demostrativa | Se muestra la fecha/hora de la cita seleccionada |
| Cita atendida relacionada | Consulta respiratoria demostrativa | El pago conserva el vínculo con una cita Atendida |
| Cita no asistida relacionada | Orientación alimentaria demostrativa | El vínculo es visible y no cambia el estado del pago |
| Cita cancelada relacionada | Pago cancelado demostrativo | El pago y la cita conservan estados independientes |
| Cita existente sin relación | Cobro sin cita aunque existe una programada | Se muestra **Sin cita relacionada** porque no se seleccionó una cita al cobrar |
| Cancelación trazable | Pago cancelado demostrativo | Estado Cancelado, motivo y movimiento original visibles; no suma en totales |
| Registro legado | Pago legado incompleto para revisión | Estado Requiere revisión, importe no disponible y exclusión de totales |
| Seguridad CSV | `=PRUEBA_CSV_NEUTRALIZADA` | La exportación antepone un apóstrofo al contenido interpretable como fórmula |
| Reporte mensual | Pago de otro periodo para reporte mensual | Aparece al ampliar el rango y agrupar por mes |
| Responsables distintos | Pagos de recepción, admin y perfiles clínicos | La columna Registró conserva al usuario real de la captura |
| Desglose de caja | Efectivo, tarjeta, transferencia y otro | Cada método aparece separado; no determina si se factura |

Conteos de referencia tras una carga nueva:

- citas: 4 Programadas, 1 Atendida, 1 No Asistió y 1 Cancelada;
- pagos: 16 Vigentes, 1 Cancelado y 1 Requiere revisión;
- métodos: existen casos de efectivo, tarjeta, transferencia y otro.

## Validaciones manuales clave

1. Inicia como `demo_recepcion`, abre Patricia Ramírez Soto y pulsa **Ver en Pagos**. El nombre completo debe localizar sus movimientos.
2. Comprueba que el cobro “Cobro sin cita aunque existe una programada” diga **Sin cita relacionada**. Es correcto: el sistema no debe inferir qué cita originó un cobro.
3. Inicia como `demo_admin`, filtra por **Vigente** y cancela un pago. La pantalla debe volver al folio cancelado, mantenerlo visible y resaltar su renglón.
4. Confirma que Recepción no vea el control de cancelación y que Medicina no pueda abrir el módulo global.
5. Exporta el rango que contiene el concepto de prueba CSV y verifica que Excel lo trate como texto, no como fórmula.

Al terminar, desactiva las cuentas demo o descarta por completo la base de validación.
