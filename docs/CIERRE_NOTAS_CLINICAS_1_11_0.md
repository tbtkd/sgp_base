# Cierre de notas clínicas — versión 1.11.0

## Finalidad

Una consulta se guarda inicialmente como **Borrador** para permitir su revisión. Cuando el profesional confirma que está completa, la acción **Cerrar nota** protege el contenido original. El cierre no es una firma electrónica ni sustituye los requisitos legales aplicables; es un control de integridad y trazabilidad dentro del sistema local.

## Flujo para el usuario

1. Registra y revisa la consulta.
2. En el detalle, confirma **Cerrar nota**.
3. La pantalla muestra quién la cerró y cuándo; desaparece la opción Editar.
4. Si surge información posterior, usa **Agregar aclaración** e indica el motivo y el dato nuevo.
5. La impresión muestra el estado, cierre y aclaraciones en orden.

Cerrar una nota no puede deshacerse. Tampoco se reemplaza el texto original. Cada aclaración queda numerada, fechada y asociada con su autor.

## Reglas técnicas

- Sólo Administración o el profesional que registró la consulta puede cerrar y aclarar la nota.
- Las notas antiguas quedan en Borrador porque no existe evidencia de un cierre previo.
- `nota_cierres_clinicos.valoracion_id` es único y usa `ON DELETE RESTRICT`.
- `operation_key` evita duplicados de cierre y de aclaración.
- Las aclaraciones usan consecutivo único por cierre y no admiten edición o eliminación desde la aplicación.
- Los eventos `CERRAR_NOTA_CLINICA` y `AGREGAR_ACLARACION_NOTA`, incluidos rechazos, quedan en Auditoría sin copiar el texto clínico al registro de auditoría.
- El cierre y las aclaraciones exitosas activan un respaldo posterior a la operación crítica.

## Escenarios de prueba

- Correctos: cierre del autor, cierre administrativo, aclaración válida, impresión y doble envío idempotente.
- Incorrectos: solicitud sin CSRF, identificador de operación inválido, otro profesional, aclaración antes del cierre, campos demasiado cortos, edición y eliminación directa de una nota cerrada.

Los datos demo incluyen una nota cerrada y una aclaración ficticia. Ningún dato demo debe usarse como indicación clínica real.
