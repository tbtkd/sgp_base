# Casos de uso

## UC-01 — Administrar pacientes

Recepción o personal clínico registra, busca, actualiza y cambia el estado de un paciente, incluyendo su contacto de emergencia.

## UC-02 — Gestionar el expediente

Un médico o administrador registra antecedentes, alergias, medicación y hábitos. Recepción no puede consultar esta información.

## UC-03 — Registrar una consulta

El profesional captura el motivo, síntomas, signos vitales, diagnóstico, plan e indicaciones. El IMC se calcula en el servidor. Sólo el perfil Nutrición puede capturar antropometría.

## UC-04 — Agendar una cita

El usuario registra fecha, hora y motivo. El sistema evita horarios duplicados y audita cambios de estado.

## UC-05 — Registrar un pago

El usuario captura fecha, monto, concepto y método de pago.

## UC-06 — Contactar por WhatsApp

El sistema construye un enlace `wa.me` con teléfono y mensaje codificado, además de conservar una bitácora de seguimiento.

## UC-07 — Imprimir nota clínica

El profesional abre la consulta y usa “Imprimir nota / PDF”. La hoja conserva la identidad histórica de la consulta, pero se identifica expresamente como nota clínica y no como receta.

## UC-08 — Emitir receta ordinaria

Un usuario de Medicina general u Odontología abre una consulta, verifica paciente y datos profesionales, estructura uno o más medicamentos y confirma competencia y alcance ordinario. El sistema bloquea cédula/domicilio faltantes, conserva una instantánea, audita la emisión y genera una hoja A4 que debe firmarse de forma autógrafa.

## UC-08A — Emitir receta adicional

El profesional abre una consulta que ya tiene folios y emite otro documento independiente. El nuevo folio no altera la vigencia de los anteriores.

## UC-08B — Sustituir una receta

El profesional selecciona una receta vigente, captura un motivo y revisa la información precargada. El sistema emite un folio nuevo, enlaza ambos documentos y marca el anterior como “no entregar ni surtir”; ningún dato histórico se sobrescribe.

## UC-09 — Asignar perfil profesional

El administrador conserva el rol de permisos y asigna por separado Medicina general, Odontología/Dentista o Nutrición. El perfil es obligatorio para el rol Médico / Profesional clínico.

## UC-10 — Consultar auditoría

El administrador filtra hasta 500 eventos por acción, módulo y resultado.

## UC-11 — Recuperar acceso

El usuario cambia su contraseña con la credencial actual. Si la olvidó, otro administrador reautenticado genera una temporal que invalida sesiones y obliga a cambiarla. Si no queda ninguna sesión administrativa, el propietario del equipo ejecuta la recuperación local para una cuenta administradora.
