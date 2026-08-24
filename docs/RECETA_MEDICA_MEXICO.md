# Nota clínica y receta ordinaria en México

Revisión funcional y normativa al 23 de agosto de 2026. Este documento sirve como guía de producto y no sustituye la revisión de un responsable sanitario o asesor jurídico del consultorio.

## Dictamen funcional de la versión 1.7.4

El sistema maneja dos documentos distintos:

1. **Nota de consulta clínica.** Registra motivo, síntomas, signos vitales, evolución, diagnóstico, plan e indicaciones. No se presenta como receta.
2. **Receta médica ordinaria.** Se genera después de guardar la consulta, con un folio propio, datos profesionales completos y medicamentos estructurados.

La receta ordinaria implementa controles alineados con los artículos 28 a 31 del Reglamento de Insumos para la Salud: emisor autorizado, nombre y domicilio completos, cédula, fecha, espacio de firma y posología estructurada. El sistema también conserva paciente, edad al emitir, expediente y alergias conocidas como datos de seguridad clínica.

| Elemento | Estado en 1.7.4 | Control operativo pendiente |
| --- | --- | --- |
| Profesional autorizado | Sólo Medicina general u Odontología | El consultorio debe verificar título, cédula y competencia real |
| Nombre completo y área | Snapshot obligatorio | Revisar antes de imprimir |
| Cédula profesional | Obligatoria para emitir | Verificar vigencia/autenticidad fuera del sistema |
| Domicilio completo | Obligatorio para emitir | El administrador debe capturarlo completo y mantenerlo actualizado |
| Fecha de emisión | Generada por el servidor | Verificar fecha/hora y zona del equipo |
| Firma | Línea única y centrada para firma autógrafa | La impresión debe firmarse físicamente antes de entregarse |
| Medicamento | Genérico obligatorio; marca opcional | El prescriptor debe verificar denominación y presentación correctas |
| Posología | Presentación, dosis, vía, frecuencia y duración obligatorias | Revisión clínica antes de emitir |
| Cantidad e indicaciones | Campos disponibles | Completar cuando corresponda |
| Trazabilidad | Folio, versión, snapshot y eventos de original/adicional/sustitución | Conservar conforme a la política del establecimiento |
| Correcciones | Nuevo folio enlazado; el anterior se marca como no vigente | Retirar copias del folio sustituido y entregar sólo el vigente |
| Recetas especiales/controlados | Expresamente fuera de alcance | Utilizar el flujo oficial independiente que resulte aplicable |

La aplicación **no certifica por sí sola la validez jurídica** de una receta, la autenticidad de la cédula, la competencia material del profesional ni la corrección clínica de una prescripción. Tampoco implementa una firma electrónica regulada. Una receta generada sólo debe entregarse después de revisión y firma autógrafa.

## Controles implementados

- Nutrición y Recepción no pueden abrir el formulario de receta ordinaria.
- Falta de cédula o domicilio bloquea la emisión en el servidor.
- El profesional confirma que prescribe dentro de su competencia.
- El profesional confirma que no utiliza el flujo para medicamentos sujetos a receta especial.
- El profesional confirma que revisará y firmará el documento antes de entregarlo.
- Se admiten hasta 10 medicamentos; se rechazan filas incompletas, manipuladas, exactamente duplicadas o con orden repetido/no consecutivo.
- Las tarjetas nuevas se insertan arriba por usabilidad, pero la receta persistida e impresa conserva el orden real de captura `1..n`.
- La salida impresa compacta conserva denominación, presentación, dosis, vía, frecuencia y duración; sólo omite cantidad e indicaciones cuando no fueron capturadas.
- Nombre, perfil, cédula, domicilio y fecha se imprimen una vez en el encabezado; el pie reserva exclusivamente una línea centrada para la firma autógrafa.
- La receta queda asociada a una consulta y no expone edición o eliminación. Una receta adicional obtiene folio propio.
- Una corrección exige motivo, genera una sustitución y conserva intacto el folio anterior con la leyenda “NO ENTREGAR NI SURTIR”.
- La consulta no puede eliminarse si ya originó cualquier receta.
- Los datos impresos son snapshots; cambios posteriores al usuario o paciente no reescriben el documento.
- La auditoría conserva identificadores y conteo, no nombres de medicamentos ni dosis.

## Diferencia por perfil profesional

La [Ley General de Salud, artículo 28 Bis](https://www.diputados.gob.mx/LeyesBiblio/pdf/LGS.pdf) incluye a médicos y cirujanos dentistas entre quienes pueden prescribir medicamentos y exige cédula profesional. El perfil Odontología debe limitarse a su competencia. Nutrición no aparece en ese catálogo; por ello el sistema muestra **Indicaciones nutricionales / plan alimentario** y no habilita receta médica.

La historia clínica sí puede contener información específica de odontólogos, psicólogos, nutriólogos y otros profesionales de la salud. La [NOM-004-SSA3-2012](https://dof.gob.mx/nota_detalle_popup.php?codigo=5272787) también exige que las notas incluyan identificación del paciente, fecha/hora, autor y firma, y que el tratamiento con medicamentos asiente al menos dosis, vía y periodicidad. La receta separada no elimina la obligación de integrar y conservar correctamente la nota clínica.

## Recomendación de uso

1. El administrador captura nombre, cédula, perfil, establecimiento y domicilio profesional completo.
2. El profesional registra y guarda la nota clínica.
3. Desde el detalle elige **Generar receta**, verifica alergias y completa cada medicamento.
4. Revisa la vista A4, imprime, firma de forma autógrafa y agrega sello cuando corresponda.
5. Si necesita otro tratamiento, elige **Receta adicional**. Si debe corregir un folio, usa **Sustituir**; nunca modifica manualmente la copia anterior.
6. Retira cualquier copia entregable del folio sustituido y entrega únicamente el documento vigente.
7. No reutiliza este formato para medicamentos controlados o cualquier supuesto de receta especial.

Antes de una operación real, el responsable del establecimiento debe validar el formato con asesoría sanitaria/jurídica aplicable a su entidad, especialidad, tipo de medicamento y modalidad de firma.

## Fuentes oficiales consultadas

- [Reglamento de Insumos para la Salud, artículos 28 a 31](https://salud.gob.mx/unidades/cdi/nom/compi/ris.html).
- [Ley General de Salud, artículo 28 Bis; texto con últimas reformas publicadas al 15 de enero de 2026](https://www.diputados.gob.mx/LeyesBiblio/pdf/LGS.pdf).
- [NOM-004-SSA3-2012, del expediente clínico](https://dof.gob.mx/nota_detalle_popup.php?codigo=5272787).
