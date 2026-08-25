# Contexto vivo del proyecto

## Estado actual

La versión 1.10.0 es un expediente clínico general para servicios médicos, dentales, nutricionales u otras áreas de salud. La tabla y el blueprint de `valoracion` conservan el nombre histórico por compatibilidad, pero la interfaz usa “consulta clínica”. La receta ordinaria es un documento separado de la nota y mantiene un historial de folios. Agenda y citas cuenta con una superficie operativa diaria/semanal independiente; Consultas muestra la última nota de cada paciente sin repetir expedientes. Pagos conserva movimientos monetarios exactos, foliados e inmutables, con historial por paciente y módulo operativo global para Administración/Recepción.

## Reglas que deben preservarse

1. El diseño actual conserva Tailwind; el shell 1.10.0 combina azul petróleo/teal, JavaScript local, sidebar de lectura reforzada y tema claro/oscuro persistente. Alpine queda sólo por compatibilidad con vistas legadas.
2. Ninguna ruta clínica funciona sin autenticación.
3. Roles únicos: `admin`, `medico`, `recepcion`.
4. Recepción no accede a expediente, diagnóstico, tratamiento o receta.
5. Todo dato mutable se valida en `app/core/validators.py`.
6. Operación y auditoría se confirman en la misma transacción.
7. La base, secreto, logs y respaldos nunca se empaquetan.
8. `_MEIPASS` solo contiene recursos de lectura.
9. Las migraciones automáticas solo pueden añadir columnas nullable/default; nunca eliminan datos.
10. Los campos antropométricos son opcionales.
11. El modal de citas debe iniciar cerrado y su operación básica no puede depender de recursos CDN.
12. Las pestañas clínicas y la vista de impresión deben funcionar sin recursos frontend externos.
13. El rol de acceso y el perfil profesional son conceptos separados.
14. Sólo un perfil de Nutrición puede capturar o importar antropometría; el servidor es autoritativo.
15. La consulta conserva una instantánea de su autor profesional; no debe reconstruirse con el usuario que imprime.
16. Una indicación nutricional nunca debe rotularse como receta médica.
17. Sólo Medicina general y Odontología pueden emitir recetas ordinarias; además requieren cédula y domicilio profesional.
18. Una receta emitida conserva instantáneas y no se edita ni elimina; una corrección genera una sustitución enlazada y una receta adicional conserva folio independiente.
19. El módulo no debe usarse para medicamentos sujetos a receta especial.
20. La identidad detallada y las acciones de cuenta viven exclusivamente al pie del sidebar, dentro del menú `...`.
21. `app/static/img/logo.png` es la identidad canónica y `logo.ico` es su derivado para Windows.
22. Todo cambio/restablecimiento de contraseña incrementa `auth_version`; ninguna bitácora o log puede contener la credencial.
23. La recuperación local sólo restablece administradores y siempre obliga a crear una contraseña definitiva.
24. El topbar no muestra identidad de cuenta; el footer del sidebar y su menú rotulan por separado nombre, rol, área clínica y cédula para evitar confundir identidad con permisos.
25. Las actualizaciones sobre una carpeta existente deben ejecutar `scripts/cleanup_project.py`; la limpieza nunca debe tocar `.venv`, `instance` o `backups`.
26. El Panel Clínico muestra un título de módulo, no un segundo nombre de cuenta; el detalle de cuenta inicia con el atributo nativo `hidden` y sólo se abre por acción explícita.
27. La visibilidad del menú de cuenta no debe depender de Alpine o de otro recurso CDN; el fallo seguro es permanecer cerrado.
28. El dashboard sólo presenta métricas derivadas de la base: pacientes registrados, citas de hoy, consultas pendientes, series de actividad y próximas citas; **Pendientes de atención** es la única vista de alertas operativas y no muestra ingresos.
29. El top bar y sidebar 1.10.0 usan control local accesible; `logo.png` y `logo.ico` permanecen como recursos canónicos y el favicon usa una URL versionada para invalidar caché obsoleta.
30. Recepción puede ver la operación de citas y pacientes, pero no conteos, pendientes, actividad o acciones clínicas.
31. Recetas se abre desde el sidebar como contexto de la lista de consultas; no se inventa un índice clínico nuevo.
32. Plantillas, usuarios, auditoría y configuración pertenecen al grupo desplegable Administración; Configuración permanece planificada.
33. Los KPI integran consulta y acción en controles separados; no debe volver a crearse una fila paralela de Acciones rápidas.
34. El topbar permanece fuera del desplazamiento del contenido mediante un shell limitado al viewport.
35. Las pestañas y acciones del formulario clínico deben conservar contraste oscuro propio; sus divisores no pueden heredar líneas blancas del tema claro.
36. En el detalle del paciente, Historial Médico precede a Alimentación y Actividad Física.
37. **Sin consulta reciente** es un seguimiento nutricional: sólo se consulta y renderiza cuando el perfil profesional efectivo es `nutricion`.
38. El KPI Citas de hoy conserva la creación rápida; el sidebar abre `/agenda`, que concentra navegación diaria/semanal, seguimiento y cierre administrativo sin sustituir el modal del detalle.
39. El flujo rápido sólo crea citas para pacientes activos sin cita programada. La reagenda operativa se realiza desde Agenda, conserva el ID y paciente originales y vuelve a comprobar disponibilidad.
40. La disponibilidad visual es orientativa y siempre se revalida dentro de la operación protegida del servidor antes de confirmar.
41. La agenda rápida no precarga ni renderiza el padrón de pacientes: exige una búsqueda de al menos dos caracteres, limita las coincidencias y mantiene visible sólo la ficha elegida.
42. Agenda de hoy, Próximas citas y Pacientes recientes permanecen como resúmenes del Dashboard; la gestión completa se deriva a Agenda y cualquier simplificación adicional requiere pruebas específicas del panel.
43. `numero_cita` representa un turno diario global: el navegador nunca lo decide, `(fecha, numero_cita)` es único y la secuencia se reinicia para cada fecha.
44. La proyección visual del turno no constituye una reserva. El servidor vuelve a calcularlo dentro del bloqueo de escritura inmediatamente antes de guardar.
45. Un turno asignado es una referencia histórica. No se renumeran notas posteriores al eliminar o mover una consulta; los totales diarios se calculan mediante `COUNT`, nunca mediante `MAX(numero_cita)`.
46. En receta, la tarjeta nueva aparece arriba por usabilidad, pero `orden_medicamento[]` debe ser consecutivo, único y autoritativamente ordenado por el servidor antes de persistir e imprimir.
47. La receta impresa presenta medicamentos como una lista compacta sin tarjetas; no omite datos obligatorios, oculta sólo opcionales vacíos, preserva `1..n` y evita partir un medicamento entre páginas.
48. La identificación profesional se imprime una sola vez en el encabezado de la receta; el pie conserva únicamente una línea centrada para firma autógrafa y no duplica nombre, cédula, fecha o sello.
49. La receta usa cajas de margen CSS vacías para sustituir metadatos automáticos de Chromium, conserva margen A4 de 14/12 mm y oculta temporalmente el título al invocar la impresión.
50. En la impresión de receta el dato histórico continúa llamándose `domicilio_profesional`, pero el rótulo visible es **Domicilio**; no cambies el esquema por una decisión puramente editorial.
51. Los tamaños reforzados del sidebar y los overrides oscuros de `hover:bg-*` forman parte de la accesibilidad visual. No reintroduzcas fondos claros al pasar el puntero sobre contenido con texto adaptado al tema oscuro.
52. Sólo una cita `Programada` puede cerrarse o cancelarse; los estados terminales no se reabren. `Atendida` y `No Asistió` exigen que el horario haya transcurrido, y `Cancelada` exige un motivo administrativo.
53. Recepción puede operar identidad, horario y estado de una cita, pero Agenda no debe mostrarle motivo clínico ni habilitar el inicio de consulta.
54. Consultas muestra una sola fila por paciente y abre su nota más reciente; Recetas conserva todas las consultas específicas para mantener accesibles documentos históricos.
55. Importar Excel sólo se renderiza para Nutrición. El backend debe rechazar y auditar cualquier solicitud forjada antes de revelar si el paciente existe.
56. `seed_demo.py` es una utilidad explícita de validación: nunca se ejecuta al arrancar, no reemplaza datos y debe permanecer idempotente.
57. En el detalle de paciente, los datos principales y el seguimiento operativo se muestran siempre. Los campos complementarios vacíos no se listan individualmente; un único estado vacío debe conducir a edición. Nunca ocultes una ausencia clínicamente relevante ni elimines el dato del formulario o del modelo.
58. Los renglones desplegados de Pendientes de atención deben conservar contraste AA en tema oscuro tanto en reposo como en hover y foco; el texto secundario no puede reutilizar grises del tema claro.
59. `pagos.monto_centavos` es la única fuente autoritativa de cálculo; `pagos.monto` se conserva sólo como espejo de compatibilidad y no se usa en agregados nuevos.
60. Un pago nuevo debe ser positivo, MXN, foliado, ligado al usuario que lo registró y protegido por una clave de operación única contra doble envío.
61. Los pagos no se editan ni eliminan. Administración puede cancelarlos con motivo, responsable y fecha, conservando íntegro el movimiento original.
62. `requiere_revision` preserva registros legados incompletos sin sumarlos. Nunca inventes un importe para convertirlos en vigentes.
63. Pagos usa `ON DELETE RESTRICT` hacia Paciente y `SET NULL` para usuarios/cita; una eliminación nunca debe borrar el historial financiero en cascada.
64. Administración y Recepción acceden al módulo global; Medicina conserva registro e historial desde el paciente. Sólo Administración cancela.
65. El total y el desglose por método incluyen únicamente movimientos `vigente`; cancelados y pendientes de revisión permanecen visibles pero no alteran la suma.
66. Pagos no equivale a CFDI, contabilidad, cuentas por cobrar, estado de cuenta ni corte de caja. No uses esos rótulos sin incorporar las entidades y reglas correspondientes.
67. Los reportes de pagos son exclusivos de Administración: resumen diario/mensual y CSV global o por paciente. La exportación conserva el filtro, limita 10,000 filas, neutraliza prefijos de fórmula y se audita; no calcula saldos.
68. Una cita existente no se enlaza automáticamente con un pago. `cita_id` es opcional y sólo se establece cuando el operador identifica la atención que originó el cobro.
69. `metodo_pago` sirve para desglose operativo y conciliación; nunca se usa para inferir si se requiere CFDI. La solicitud de factura y los datos fiscales pertenecen a un flujo separado aún no implementado.
70. La búsqueda global de Pagos aplica todos los términos normalizados aunque nombre y apellidos vivan en columnas distintas. **Ver en Pagos** debe funcionar con el nombre completo.
71. Tras cancelar, el pago original debe permanecer visible. El retorno sólo admite rutas internas autorizadas, ancla el folio y elimina filtros que ocultarían el nuevo estado.
72. Hospitalización no forma parte del producto dirigido a consultorios y no debe reaparecer en la navegación actual.

## Próximas fases

- Cifrado en reposo y administración de llaves.
- Firma electrónica jurídicamente evaluada y cierre/versionado de notas clínicas.
- Flujos regulatorios separados para medicamentos controlados, sólo tras revisión jurídica y operativa.
- Recursos frontend autocontenidos.
- Reportes y métricas configurables por especialidad.
- Recibos no fiscales, exportación XLSX, reembolsos como movimientos separados y caja formal después de definir cargos, conciliación y responsables.
- Multi-consultorio únicamente después de incorporar aislamiento por tenant.
