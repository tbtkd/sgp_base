# Manual de usuario — Sistema Clínico 1.10.1

## 1. Propósito

Este manual explica el uso cotidiano del sistema para:

- personal médico o dental;
- personal de Nutrición;
- administradores;
- asistentes o recepción.

En el sistema, un **asistente** debe utilizar normalmente el rol **Recepción**. Este rol administra pacientes, citas y pagos, pero no puede consultar antecedentes, diagnósticos, recetas ni otra información clínica restringida.

El sistema está diseñado para operar localmente en una computadora del consultorio mediante `http://127.0.0.1:5000/`.

## 2. Iniciar y cerrar el sistema

### Iniciar desde Python

1. Abre PowerShell en la carpeta del proyecto.
2. Activa el entorno virtual:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

3. Ejecuta:

   ```powershell
   python run.py
   ```

4. Abre `http://127.0.0.1:5000/` si el navegador no se abre automáticamente.

### Iniciar desde el ejecutable

Abre `SistemaPacientes.exe`. La base, los respaldos y los registros se crean junto al ejecutable, dentro de sus carpetas correspondientes.

### Cerrar sesión

1. En la parte inferior del sidebar, pulsa el botón `...` de tu cuenta.
2. Selecciona **Cerrar Sesión**.
3. Cierra el navegador cuando termines de trabajar.

No cierres únicamente la pestaña si otras personas pueden utilizar el equipo: la sesión podría permanecer activa durante algunos minutos.

## 3. Roles y áreas profesionales

El permiso de acceso y la especialidad son conceptos distintos.

| Rol | Uso recomendado | Acceso principal |
| --- | --- | --- |
| Administrador | Responsable del sistema | Todo el sistema, usuarios y auditoría |
| Médico | Profesional que atiende pacientes | Expedientes, consultas y funciones clínicas |
| Recepción | Asistente o recepcionista | Pacientes, citas, pagos y comunicación operativa |

Los usuarios clínicos pueden tener uno de estos perfiles:

- **Medicina general**: consultas y receta ordinaria cuando cuenta con cédula y domicilio.
- **Dentista/Odontología**: consultas y receta ordinaria cuando cuenta con cédula y domicilio.
- **Nutrición**: consultas, historial y antropometría; no utiliza la receta médica ordinaria del sistema.

No asignes el rol Médico a recepción sólo para habilitar más pantallas. Los permisos deben corresponder con las responsabilidades reales de cada persona.

## 4. Navegación principal

### Sidebar

El menú lateral agrupa las funciones por área:

- **Dashboard**: resumen operativo del consultorio.
- **Pacientes**: búsqueda, alta y expediente administrativo.
- **Agenda y citas**: abre la agenda operativa con vistas por día o semana.
- **Consultas**: notas clínicas registradas.
- **Expedientes clínicos**: antecedentes, alergias, medicación y hábitos.
- **Recetas**: localiza consultas que contienen o pueden generar recetas.
- **Administración**: plantillas, usuarios, auditoría y opciones planificadas, según permisos.

Las opciones marcadas **Próximamente** son informativas y todavía no tienen una función operativa. No contienen datos simulados.

### Barra superior

- El buscador localiza pacientes por nombre, teléfono o correo.
- La sede indica el consultorio local activo; todavía no permite administrar varias clínicas.
- Notificaciones muestra el estado disponible del módulo.
- El botón de tema cambia entre modo claro y oscuro.
- El título y breadcrumb indican la sección actual.

La barra superior permanece visible mientras recorres una pantalla larga.

### Uso con teclado

- Usa `Tab` y `Shift + Tab` para recorrer controles.
- Pulsa `Enter` o `Espacio` para activar botones y enlaces.
- Pulsa `Escape` para cerrar menús, paneles o modales compatibles.
- En pestañas clínicas utiliza las flechas izquierda/derecha.

## 5. Flujo recomendado para recepción o asistente

1. Inicia sesión con una cuenta de Recepción.
2. Busca al paciente antes de crear uno nuevo para evitar duplicados.
3. Si no existe, selecciona **Nuevo paciente** desde el KPI de Pacientes registrados.
4. Captura los datos administrativos y el contacto de emergencia.
5. Abre **Agenda y citas** en el sidebar o usa **Agendar cita** en el KPI Citas de hoy.
6. Busca al paciente, elige una fecha y selecciona un horario disponible.
7. Desde el detalle del paciente registra el pago cuando corresponda.
8. Utiliza WhatsApp únicamente después de verificar el número y el mensaje.
9. Cierra sesión al terminar.

Recepción no debe poder abrir historiales, diagnósticos, consultas ni recetas. Si una pantalla clínica aparece disponible para esta cuenta, informa al administrador y evita utilizarla hasta revisar el rol.

## 6. Registrar y buscar pacientes

### Antes del alta

Busca por:

- nombre o apellidos;
- teléfono;
- correo electrónico.

### Alta

1. En el Dashboard, localiza **Pacientes registrados**.
2. Pulsa **Nuevo paciente**.
3. Captura los campos requeridos.
4. Verifica especialmente teléfono, correo, fecha de nacimiento y contacto de emergencia.
5. Pulsa **Registrar paciente**.

Los teléfonos deben contener exactamente 10 dígitos. La fecha de nacimiento no puede ser futura ni anterior a 1900.

### Leer el detalle del paciente

El detalle está organizado para evitar una lista extensa de marcadores vacíos:

- **Datos principales** siempre muestra identidad, nacimiento, teléfono, ciudad y estatus.
- **Información complementaria** muestra únicamente correo, ocupación, dirección y contactos de emergencia que sí fueron capturados.
- Si no existe ningún dato complementario, aparece un solo aviso con **Completar datos**; esto no significa que se hayan eliminado campos.
- **Seguimiento operativo** conserva Último pago y Siguiente cita incluso cuando no existe un registro, porque su ausencia es útil para la operación.

Selecciona **Editar datos** para agregar o corregir la información omitida. No inventes valores sólo para eliminar el aviso: es preferible dejar un campo opcional vacío que registrar información no confirmada.

### Paciente inactivo

Un paciente inactivo conserva su historial. No debe crearse nuevamente como otro registro. Solicita al personal autorizado reactivarlo cuando corresponda.

## 7. Agendar una cita

### Agenda operativa

1. Selecciona **Agenda y citas** en el sidebar.
2. Alterna entre **Día** y **Semana**.
3. Usa Anterior, Hoy, Siguiente o el selector de fecha para cambiar de periodo.
4. Revisa el resumen de Programadas, Atendidas, No asistieron y Canceladas.
5. Abre el menú `...` de una cita programada para reagendar, cancelar o registrar inasistencia.
6. Cuando la fecha/hora ya ocurrió, la cita puede cerrarse como Atendida o No Asistió.
7. El personal clínico puede seleccionar **Iniciar consulta** en las citas del día.

Una cita cerrada no se reabre. Si el estado se registró incorrectamente, informa al administrador; no crees otra cita sin confirmar primero el historial operativo.

Recepción ve la identidad del paciente y el estado necesario para trabajar, pero la Agenda oculta el motivo clínico y no ofrece acceso a la nota.

### Agendar desde Dashboard o Agenda

1. En el KPI **Citas de hoy**, pulsa **Agendar cita**.
2. Escribe al menos dos caracteres del nombre, expediente o teléfono.
3. Selecciona el resultado correcto. Después de elegirlo sólo quedará visible su ficha.
4. Revisa el calendario de 21 días o selecciona otra fecha válida.
5. Elige un horario marcado como disponible.
6. Captura el motivo.
7. Revisa el resumen y confirma.

El sistema vuelve a comprobar la disponibilidad al guardar. Si otra persona ocupó el horario, se mostrará un error y deberás elegir otro.

### Reagendar o cancelar

Desde el menú `...` de una cita programada selecciona **Reagendar**. El sistema conserva al paciente, libera únicamente el espacio actual para la consulta de disponibilidad y vuelve a validar el nuevo horario al guardar. Para cancelar, el motivo es obligatorio. La opción del detalle del paciente permanece disponible como alternativa contextual.

## 8. Expediente clínico

Disponible para administradores y personal médico autorizado.

1. Abre **Expedientes clínicos** o entra al detalle del paciente.
2. Selecciona **Ver / editar**.
3. Registra antecedentes, cirugías, padecimientos, alergias, medicación y hábitos.
4. Guarda los cambios.

Las alergias deben revisarse antes de emitir cualquier receta. Evita utilizar abreviaturas ambiguas o registrar información no confirmada como un diagnóstico definitivo.

## 9. Registrar una consulta

### Localizar la última nota

1. Abre **Consultas** en el sidebar.
2. Cada paciente aparece una sola vez, con la fecha de su nota más reciente.
3. Busca por nombre o apellidos; no es necesario respetar mayúsculas o acentos.
4. Pulsa **Fecha más reciente** para alternar entre orden descendente y ascendente.
5. Selecciona **Ver nota** para abrir la consulta más reciente de ese paciente.

El acceso **Recetas** conserva todas las consultas, incluidas las anteriores, porque un folio puede pertenecer a una nota histórica. No confundas ambos listados.

### Capturar una consulta

1. Abre el paciente correcto.
2. Selecciona **Nueva consulta**.
3. Completa las pestañas:
   - **Consulta**: fecha, motivo, síntomas y evolución.
   - **Signos vitales**: tensión arterial, frecuencia cardiaca, frecuencia respiratoria, temperatura, SpO₂, estatura y peso.
   - **Evolución e indicaciones**: impresión diagnóstica, plan e indicaciones.
   - **Antropometría opcional**: visible únicamente para Nutrición.
4. Revisa la información.
5. Pulsa **Guardar consulta**.

El **Turno diario** es informativo y lo asigna el servidor. Se reinicia cada fecha y no debe editarse manualmente.

Si un campo es inválido, el sistema abre la pestaña que contiene el problema. Corrige el dato antes de intentar guardar nuevamente.

La opción **Importar Excel** sólo se muestra al personal con perfil Nutrición. Medicina general, Odontología y Recepción no pueden utilizarla aunque intenten enviar directamente la solicitud.

## 10. Generar una receta ordinaria

Disponible únicamente para Medicina general u Odontología con:

- cédula profesional registrada;
- domicilio completo;
- paciente activo;
- consulta previamente guardada.

### Crear la receta

1. Abre el detalle de la consulta.
2. Pulsa **Generar receta**.
3. Confirma que se trata de medicamentos permitidos para receta ordinaria.
4. Captura por medicamento:
   - denominación genérica;
   - marca, cuando aplique;
   - presentación y concentración;
   - dosis;
   - vía;
   - frecuencia;
   - duración;
   - cantidad e indicaciones adicionales cuando sean necesarias.
5. Pulsa **Agregar** para otro medicamento. La tarjeta nueva aparece arriba; la impresión conservará el orden real `1, 2, 3…`.
6. Revisa y emite.

### Corregir o ampliar

- **Receta adicional** crea otro folio para la misma consulta.
- **Sustituir** corrige una receta vigente y marca la anterior como no válida.

Una receta emitida no se edita directamente. Nunca entregues un documento marcado **NO ENTREGAR NI SURTIR**.

El módulo no debe utilizarse para medicamentos controlados, psicotrópicos, estupefacientes o cualquier supuesto que requiera receta especial.

## 11. Imprimir una nota o receta

### Nota clínica

1. Abre la consulta.
2. Selecciona **Imprimir nota / PDF**.
3. Revisa la hoja.
4. Pulsa **Imprimir / guardar PDF**.

### Receta

1. Abre el folio correcto y confirma que esté vigente.
2. Verifica paciente, alergias, medicamentos, dosis, folio, fecha y profesional.
3. Pulsa **Imprimir / PDF**.
4. Selecciona la impresora o **Guardar como PDF**.
5. Mantén escala en 100 %.
6. Firma de forma autógrafa antes de entregar.

En Opera, Chrome y Edge modernos no deben aparecer la fecha, URL o título automáticos del navegador. Si un navegador antiguo todavía los muestra, desactiva **Encabezados y pies de página** en sus opciones de impresión.

La receta muestra los datos profesionales en la parte superior. El campo de ubicación aparece como **Domicilio** y la parte inferior conserva únicamente la línea centrada para firma.

## 12. Pagos y WhatsApp

### Pago

Desde el detalle del paciente:

1. Verifica la identidad del paciente.
2. Captura una fecha igual o anterior al día actual.
3. Ingresa el importe en MXN con máximo dos decimales. Debe ser mayor que cero.
4. Describe el concepto real del cobro.
5. Selecciona efectivo, tarjeta, transferencia u otro. Este método sirve para el desglose operativo de caja; no indica si el paciente requiere factura.
6. Si corresponde, relaciona una cita del mismo paciente. La existencia de una cita no la enlaza automáticamente: selecciona sólo la atención que originó el cobro.
7. Pulsa una sola vez **Registrar pago** y espera el folio de confirmación.

El movimiento queda en **Historial de pagos** con fecha, folio, importe, método, responsable y estado. El bloque **Último pago vigente** omite pagos cancelados.

### Módulo Pagos

Administración y Recepción pueden abrir **Gestión → Pagos**. La pantalla inicia con el día actual y permite:

- buscar por nombre completo, términos parciales, folio o concepto;
- elegir un rango máximo de 366 días;
- filtrar método y estado;
- consultar total vigente y desglose por método;
- recorrer resultados en páginas de 25 movimientos.

Los movimientos cancelados y los registros legados que requieren revisión permanecen visibles, pero no se suman.

### Reportes y CSV

Sólo Administración puede usar estas acciones:

1. Ajusta búsqueda, fechas, método y estado.
2. En **Resumen**, elige **Por día** o **Por mes** y aplica los filtros.
3. Revisa el bloque **Reporte administrativo**.
4. Pulsa **Exportar filtro CSV** para descargar exactamente ese conjunto.
5. Para un solo paciente, abre su detalle y pulsa **Exportar historial CSV**.

El archivo abre en Excel y conserva folio, paciente, concepto, método, importe, responsables, cita y cancelación. La aplicación limita cada descarga a 10,000 filas. El reporte sólo refleja cobros: no calcula saldo, adeudo ni conciliación.

### Cancelar un pago

Sólo Administración puede cancelar:

1. Abre el menú rojo del movimiento.
2. Captura un motivo específico de al menos cinco caracteres.
3. Revisa el aviso: el pago no se eliminará, quedará como **Cancelado** y la operación no se puede deshacer. Elige **Volver** si necesitas revisar los datos o **Sí, cancelar pago** para continuar.
4. Comprueba que el estado cambió a **Cancelado**. La pantalla vuelve al mismo folio y resalta el renglón; si estaba activo el filtro Vigente, lo sustituye por la búsqueda del folio para conservarlo visible.

Cancelar no elimina ni edita el pago original. Si el cobro correcto es diferente, registra después un pago nuevo. No utilices la cancelación para representar un reembolso; esa operación todavía no está implementada.

El módulo es un control operativo local. No genera CFDI, cargos, adeudos, estados de cuenta, contabilidad o cortes formales de caja. Cuando se diseñe Facturación deberá capturarse por separado la solicitud de factura y la información fiscal; nunca se deducirá del método de pago.

### WhatsApp

El enlace abre WhatsApp con el número del paciente. Antes de enviar:

- confirma que el teléfono pertenezca al paciente;
- revisa el texto completo;
- evita incluir diagnósticos o información clínica innecesaria;
- registra únicamente comunicaciones relacionadas con la atención.

## 13. Administración de usuarios

Disponible únicamente para administradores.

### Alta de usuario

1. Abre **Administración → Usuarios y permisos**.
2. Selecciona **Registrar usuario**.
3. Captura identidad, usuario, correo, rol y contraseña inicial.
4. Para personal clínico, selecciona el perfil profesional correcto.
5. Captura cédula y domicilio completo cuando emitirá recetas.
6. Guarda y entrega la credencial por un canal seguro.

### Restablecer una contraseña

1. Abre la lista de usuarios.
2. Selecciona **Restablecer contraseña**.
3. Confirma tu propia contraseña de administrador.
4. Comunica la contraseña temporal una sola vez.

El usuario deberá cambiarla al iniciar. La contraseña temporal no queda visible en registros ni auditoría.

### Si ningún administrador puede ingresar

En la computadora que contiene los datos ejecuta:

```powershell
python run.py --reset-password NOMBRE_USUARIO
```

Con el ejecutable:

```powershell
SistemaPacientes.exe --reset-password NOMBRE_USUARIO
```

Este procedimiento sólo funciona para administradores y obliga a cambiar la contraseña posteriormente.

## 14. Auditoría, respaldos y registros

### Auditoría

**Administración → Auditoría** muestra accesos y operaciones críticas. Utilízala para investigar cambios, no como sustituto del expediente clínico.

### Respaldos

El sistema mantiene hasta 10 respaldos verificados en `backups/`: crea uno al iniciar y después de operaciones críticas aceptadas. Administración puede abrir **Administración → Respaldos** para:

1. crear una copia inmediata;
2. comprobar su integridad;
3. descargarla como archivo SQLite;
4. restaurarla cuando sea necesario.

Para restaurar, selecciona una copia, captura tu contraseña y escribe exactamente `RESTAURAR`. SGPN valida el archivo, crea una copia del estado vigente, reemplaza la base y cierra la sesión. Si la contraseña, frase, integridad o esquema no son válidos, la base activa permanece sin cambios. Practica el flujo primero con datos de demostración.

### Registros técnicos

Si el sistema no inicia, revisa:

```powershell
Get-Content .\instance\logs\startup.log -Tail 80
Get-Content .\instance\logs\app.log -Tail 80
```

No edites la base con herramientas externas mientras la aplicación está abierta.

## 15. Buenas prácticas de seguridad

- Usa una cuenta individual; no compartas usuarios.
- Bloquea Windows cuando te alejes del equipo.
- Activa BitLocker o Cifrado de dispositivo y resguarda la clave de recuperación fuera del equipo.
- Mantén Windows, navegador y protección antimalware actualizados.
- No envíes bases, respaldos o recetas por canales públicos.
- No guardes contraseñas en notas pegadas al monitor o archivos sin protección.
- Verifica siempre al paciente antes de modificar datos o iniciar una consulta.
- Revisa folio y vigencia antes de imprimir una receta.
- Conserva respaldos cifrados en otro medio, mantén una copia desconectada y prueba que pueda restaurarse antes de usar información real.
- No expongas el puerto de la aplicación a Internet.
- Cierra sesión cuando otra persona vaya a utilizar la computadora.

## 16. Problemas frecuentes

| Problema | Acción recomendada |
| --- | --- |
| No aparece un paciente | Busca por teléfono/correo y revisa la pestaña de inactivos |
| No aparece Antropometría | Confirma que el usuario tenga perfil Nutrición |
| No aparece Generar receta | Confirma perfil Medicina/Odontología, cédula, domicilio y paciente activo |
| El horario dejó de estar disponible | Actualiza la disponibilidad y selecciona otro |
| Una receta tiene un error | Usa Sustituir; no modifiques ni entregues el folio anterior |
| El PDF muestra encabezados del navegador | Desactiva Encabezados y pies en navegadores sin soporte moderno |
| El sistema no inicia | Revisa `instance/logs/startup.log` y confirma que el puerto 5000 esté libre |
| Olvidé la contraseña | Solicita restablecimiento al administrador o usa recuperación local para el administrador único |

## 17. Límites actuales

Laboratorio, Facturación, Inventario, el módulo general de Reportes, Configuración multi-sede y Portal del paciente todavía están planificados. Hospitalización queda fuera del alcance actual porque esta edición está dirigida a consultorios. Pagos sí incluye su resumen y CSV administrativos dentro del propio módulo. El sistema está preparado para una estación local controlada y no debe publicarse directamente en Internet.

Para instalación, pruebas y mantenimiento técnico consulta [../README.md](../README.md), [EJECUCION_PRUEBAS.md](EJECUCION_PRUEBAS.md), [RECUPERACION_ACCESO.md](RECUPERACION_ACCESO.md) y [RECETA_MEDICA_MEXICO.md](RECETA_MEDICA_MEXICO.md).
