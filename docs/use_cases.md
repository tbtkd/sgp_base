# Casos de uso

## UC-01 — Administrar pacientes

Recepción o personal clínico registra, busca, actualiza y cambia el estado de un paciente, incluyendo su contacto de emergencia. La búsqueda acepta fragmentos y no distingue mayúsculas ni acentos.

## UC-02 — Gestionar el expediente

Un médico o administrador registra antecedentes, alergias, medicación y hábitos. Recepción no puede consultar esta información.

## UC-03 — Registrar una consulta

El profesional captura el motivo, síntomas, signos vitales, diagnóstico, plan e indicaciones. El IMC se calcula en el servidor. Al guardar, el sistema asigna el siguiente turno global de la fecha e ignora cualquier número alterado en el navegador. Sólo el perfil Nutrición puede capturar antropometría.

## UC-04 — Agendar una cita

Desde el KPI Citas de hoy, el usuario escribe al menos dos caracteres del nombre, expediente o teléfono de un paciente activo. El sistema no precarga el padrón, devuelve hasta ocho coincidencias y, al elegir una, conserva sólo su ficha. Después consulta 21 días de disponibilidad, puede elegir otra fecha, selecciona un horario libre y revisa el resumen antes de confirmar. El servidor revalida paciente y espacio y audita la creación. Si el paciente ya tiene una cita programada, el flujo rápido no la sobrescribe y dirige al detalle para reagendarla. El modal del detalle permanece disponible para el flujo individual previo.

## UC-05 — Registrar un pago

Desde el detalle del paciente, Administración, Medicina o Recepción captura fecha, importe MXN, concepto, método y una cita opcional del mismo paciente. El servidor convierte a centavos, asigna folio/responsable y rechaza fechas futuras, importes no positivos, más de dos decimales, catálogos manipulados, citas ajenas y claves de operación repetidas.

## UC-05A — Consultar pagos

El detalle muestra el último pago vigente y hasta cincuenta movimientos del paciente. Administración y Recepción abren además el módulo global, filtran un rango de hasta 366 días, paciente/folio/concepto, método y estado, y consultan total vigente, desglose y movimientos paginados.

## UC-05B — Cancelar un pago

Administración captura un motivo y confirma la cancelación. El sistema conserva importe, folio, fecha, concepto, método y registrador originales, añade responsable/momento/motivo, excluye el pago de totales y audita éxito o intento duplicado. Recepción y Medicina no pueden ejecutar esta operación.

## UC-05C — Generar reporte de pagos

Administración filtra hasta 366 días, elige resumen por día o mes y exporta el resultado global a CSV. También puede descargar el historial de cobros de un paciente. El servidor limita 10,000 filas, neutraliza fórmulas de hoja de cálculo, impide acceso a otros roles y audita alcance y cantidad exportada. El reporte no calcula saldos ni adeudos.

## UC-06 — Contactar por WhatsApp

El sistema construye un enlace `wa.me` con teléfono y mensaje codificado, además de conservar una bitácora de seguimiento.

## UC-07 — Imprimir nota clínica

El profesional abre la consulta y usa “Imprimir nota / PDF”. La hoja conserva la identidad histórica de la consulta, pero se identifica expresamente como nota clínica y no como receta.

## UC-08 — Emitir receta ordinaria

Un usuario de Medicina general u Odontología abre una consulta, verifica paciente y datos profesionales, estructura uno o más medicamentos y confirma competencia y alcance ordinario. Cada alta de medicamento aparece arriba para mantener accesible el control, pero el sistema valida y conserva el orden real de captura antes de generar la receta `1..n`. El sistema bloquea cédula/domicilio faltantes, conserva una instantánea, audita la emisión y genera una hoja A4 con la identidad profesional completa en el encabezado y una única línea centrada que debe firmarse de forma autógrafa.

## UC-08A — Emitir receta adicional

El profesional abre una consulta que ya tiene folios y emite otro documento independiente. El nuevo folio no altera la vigencia de los anteriores.

## UC-08B — Sustituir una receta

El profesional selecciona una receta vigente, captura un motivo y revisa la información precargada. El sistema emite un folio nuevo, enlaza ambos documentos y marca el anterior como “no entregar ni surtir”; ningún dato histórico se sobrescribe.

## UC-09 — Asignar perfil profesional

El administrador conserva el rol de permisos y asigna por separado Medicina general, Odontología/Dentista o Nutrición. El perfil es obligatorio para el rol Médico / Profesional clínico. Si el propio administrador atiende, mantiene Administración y selecciona su perfil; no necesita rebajar su acceso.

## UC-10 — Consultar auditoría

El administrador filtra hasta 500 eventos por acción, módulo y resultado.

## UC-11 — Recuperar acceso

El usuario cambia su contraseña con la credencial actual. Si la olvidó, otro administrador reautenticado genera una temporal que invalida sesiones y obliga a cambiarla. Si nadie puede ingresar pero la cuenta sigue siendo administradora, el responsable del equipo restablece su contraseña localmente. Si una instalación anterior no conserva ningún administrador activo, recupera una cuenta existente con `--recover-admin`; el comando sólo funciona en ese estado y obliga a definir una contraseña definitiva.
