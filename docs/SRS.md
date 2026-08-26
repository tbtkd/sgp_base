# Especificación de requisitos — Sistema de Expediente Clínico

## Alcance

Aplicación local para gestionar pacientes y expedientes en consultorios médicos, dentales, nutricionales u otros servicios de salud. La versión 1.10.1 no implementa multi-tenancy ni operación directa por Internet.

## Requisitos funcionales

1. Alta, búsqueda, edición y activación/desactivación de pacientes.
2. Datos generales, ocupación, dirección y contacto de emergencia.
3. Expediente con antecedentes, alergias, medicación y hábitos.
4. Consultas con signos vitales, síntomas, impresión diagnóstica, plan e indicaciones clínicas.
5. Antropometría opcional sin bloquear consultas generales.
6. Citas con fecha, hora, motivo y estado.
7. Pagos con importe exacto en centavos, moneda MXN, fecha, concepto, método, folio, responsable y cita opcional.
8. WhatsApp directo y bitácora de contacto.
9. Impresión limpia y separada de notas y recetas mediante `window.print()`.
10. Administración de usuarios y consulta de auditoría.
11. Respaldo automático y migración aditiva sin pérdida de datos.
12. Vista de impresión A4 independiente para cada nota clínica.
13. Navegación local y accesible entre secciones de la consulta.
14. Perfil profesional separado del rol: Medicina general, Odontología/Dentista o Nutrición.
15. Antropometría disponible exclusivamente para usuarios con perfil Nutrición.
16. Instantánea de nombre, perfil y cédula del profesional en cada consulta nueva.
17. Cédula omitida de la impresión cuando no se encuentre registrada.
18. Receta ordinaria restringida a Medicina general/Odontología con cédula y domicilio completos.
19. Hasta 10 medicamentos estructurados con genérico, presentación, dosis, vía, frecuencia y duración.
20. Instantánea inmutable de los datos de paciente y profesional al emitir una receta.
21. Rechazo explícito del módulo para recetas especiales/controladas.
22. Identidad y menú de cuenta en el footer del sidebar, topbar reservado a herramientas globales e iconografía institucional unificada.
23. Recetas originales, adicionales y sustituciones con folios independientes e historial inmutable.
24. Folios sustituidos marcados como no vigentes y enlazados al reemplazo.
25. Cambio propio, restablecimiento administrativo y recuperación local de contraseñas para administradores.
26. Identidad compacta mediante nombre de usuario y detalle rotulado de nombre, rol, área clínica y cédula en el menú de cuenta.
27. Limpieza segura y explícita de recursos obsoletos al actualizar sobre una carpeta existente.
28. Listado de Consultas con un paciente por fila, acceso a su nota más reciente, búsqueda por nombre y orden/paginación de servidor.
29. Contexto de Recetas separado que conserva el acceso a consultas históricas específicas.
30. Importación antropométrica visible y autorizada únicamente para el perfil profesional Nutrición.
31. Carga demostrativa opcional, explícita e idempotente que nunca se ejecuta durante el arranque.
32. Agenda rápida sin precarga del padrón: búsqueda autenticada y limitada por nombre, expediente o teléfono, con una sola ficha seleccionada visible.
33. Búsqueda global conectada al buscador autorizado de pacientes, breadcrumb y selector informativo de sede local.
34. Tema claro/oscuro persistente, foco visible y navegación de shell operable con teclado.
35. Los módulos no implementados deben identificarse como planificados y no deben exponer rutas ficticias.
36. Dashboard con tres KPI informativos y accionables, agenda, próximas citas, gráfica de citas/consultas, actividad, una sola vista de pendientes y Acompañamiento Intermedio.
37. Estados vacíos, indicador de carga de navegación y mensajes de confirmación sin inventar información clínica.
38. Recetas y Expedientes deben permanecer en el sidebar y no duplicarse como acciones rápidas del dashboard.
39. Plantillas, Usuarios, Auditoría y Configuración deben agruparse bajo Administración sin modificar la autorización de cada destino.
40. El topbar debe permanecer visible mientras se desplaza el contenido y mantener comportamiento adaptable en resoluciones pequeñas.
41. Pestañas, botones secundarios y divisores del formulario clínico deben conservar contraste suficiente en tema oscuro.
42. El detalle debe presentar Historial médico antes de Alimentación y Actividad física.
43. El pendiente de pacientes sin consulta reciente debe mostrarse sólo a perfiles de Nutrición.
44. La acción Agendar cita del KPI debe permitir seleccionar un paciente activo registrado y consultar visualmente disponibilidad sin navegar a su detalle.
45. El calendario rápido debe mostrar 21 días, permitir una fecha posterior y distinguir horarios disponibles, ocupados y transcurridos.
46. La disponibilidad mostrada debe revalidarse al confirmar; el flujo rápido no puede sobrescribir una cita programada existente.
47. La agenda rápida no debe duplicarse en el sidebar ni retirar el agendamiento/reagendamiento existente en el detalle del paciente.
48. Cada consulta debe recibir en servidor un turno global consecutivo por fecha; el primer turno de cada día es `1`.
49. El turno enviado por el navegador no debe aceptarse como autoridad y `(fecha, turno)` debe ser único en SQLite.
50. La migración debe preservar todas las consultas legadas y normalizar su turno de forma determinista.
51. Agregar un medicamento debe insertar la nueva tarjeta arriba sin alterar el orden de captura persistido e impreso `1..n`.
52. El servidor debe rechazar órdenes de medicamentos incompletos, repetidos o no consecutivos.
53. La receta impresa debe usar una lista compacta sin tarjetas por medicamento, omitir sólo campos opcionales vacíos, mantener juntos los datos de cada medicamento al paginar y conservar todos los datos obligatorios.
54. La receta debe imprimir la identidad profesional completa una sola vez en el encabezado, reservar una línea centrada para la firma autógrafa y declarar el favicon institucional vigente con invalidación de caché.
55. La impresión de receta debe sustituir los metadatos automáticos de margen en Chromium moderno, ocultar temporalmente el título como respaldo y conservar un margen A4 moderado.
56. La receta debe mostrar el rótulo abreviado **Domicilio** sin renombrar ni perder el dato histórico `domicilio_profesional`.
57. El sidebar debe mantener tamaños legibles en marca, secciones, navegación, submenús e identidad sin alterar rutas ni permisos.
58. Los estados de puntero en tema oscuro no deben utilizar fondos claros que reduzcan el contraste del texto.
59. La columna de porcentaje de grasa del historial debe mostrarse únicamente a perfiles de Nutrición.
60. **Agenda y citas** debe abrir una ruta operativa dedicada con vistas Día/Semana y navegación por periodo.
61. El alta y la reagenda desde Agenda deben reutilizar búsqueda privada, disponibilidad y validación transaccional existentes.
62. Una cita cerrada no puede volver a Programada; una cita futura no puede cerrarse como Atendida o No Asistió.
63. Cancelación, inasistencia, atención y reagenda deben generar auditoría sin almacenar el motivo clínico completo.
64. Recepción puede administrar citas, pero la Agenda no debe mostrarle motivos clínicos ni acciones de inicio de consulta.
65. El detalle del paciente debe mantener visibles los datos principales y el seguimiento operativo, mostrar sólo los campos complementarios capturados y resumir su ausencia conjunta en un estado accionable.
66. Los detalles desplegados de pendientes deben cumplir contraste WCAG AA en tema oscuro para texto principal, secundario, hover y foco visible.
67. Todo pago nuevo debe usar `monto_centavos`, ser positivo, incluir como máximo dos decimales y recibir moneda MXN, folio y clave de operación únicos.
68. El registro debe conservar al usuario responsable y aceptar una cita opcional sólo cuando pertenezca al mismo paciente.
69. Un pago no debe editarse ni eliminarse; Administración puede cancelarlo con motivo, fecha y responsable sin alterar el original.
70. Los pagos legados incompletos deben conservarse como `requiere_revision` y quedar fuera de los totales.
71. La eliminación del paciente debe restringirse cuando existan pagos; eliminar usuarios o citas opcionales sólo debe retirar la referencia.
72. El módulo global debe permitir búsqueda, rango máximo de 366 días, método, estado, total vigente, desglose y paginación.
73. Administración y Recepción pueden abrir el módulo global; Medicina registra y consulta sólo desde el paciente; únicamente Administración cancela.
74. Los totales deben sumar exclusivamente movimientos `vigente` y nunca depender del campo `Float` legado.
75. El módulo no debe presentarse como CFDI, contabilidad, estado de cuenta ni corte de caja formal.
76. Administración debe poder agrupar el periodo filtrado por día o mes y exportar el filtro o el historial de un paciente en CSV.
77. Las exportaciones deben ser exclusivas de Administración, limitarse a 10,000 filas, neutralizar fórmulas de hoja de cálculo, usar `no-store` y quedar auditadas.
78. Los reportes de pagos sólo informan cobros vigentes/cancelados; no deben calcular saldos, cargos, adeudos o conciliaciones inexistentes.
79. La búsqueda de Pagos debe localizar un nombre completo aunque sus componentes estén almacenados en campos separados y el acceso **Ver en Pagos** debe conservar el rango y la identidad buscada.
80. La relación con cita debe ser explícita, opcional y limitada al mismo paciente; el sistema no debe inferirla por la mera existencia de una cita.
81. Después de cancelar, el movimiento original debe permanecer visible mediante un retorno interno validado, búsqueda por folio y ancla cuando el filtro anterior lo ocultaría.
82. El método de pago debe utilizarse para desglose operativo y no para decidir facturación. Hospitalización queda fuera del alcance de la edición para consultorios.
83. Todos los recursos de presentación deben estar empaquetados localmente y funcionar sin Internet.
84. La CSP no debe usar `unsafe-inline`, permitir CDN ni aceptar atributos ejecutables/de estilo; los bloques internos autorizados deben usar nonce por respuesta.
85. Una mutación crítica confirmada debe intentar un respaldo consistente; una operación rechazada no debe crearlo.
86. Sólo Administración puede crear, verificar, descargar o restaurar respaldos internos.
87. Restaurar debe exigir reautenticación y frase explícita, validar integridad/esquema, crear una copia previa, reemplazar atómicamente y cerrar la sesión.
88. Un respaldo corrupto, un nombre no interno, CSRF ausente o una confirmación incorrecta no debe modificar la base activa.
89. Las búsquedas de Pacientes, Agenda, Consultas y Pagos deben aceptar términos parciales sin distinguir mayúsculas ni acentos, incluso cuando nombre y apellidos estén en campos distintos.
90. El texto de búsqueda debe mantenerse parametrizado; los caracteres `%` y `_` proporcionados por el usuario no deben convertirse en comodines SQL.
91. Una cuenta de Administración no debe poder cambiar su propio rol ni desactivarse; un administrador clínico conserva Administración y configura su área mediante el perfil profesional.
92. Ninguna operación debe dejar al sistema sin un administrador activo. Un cambio de rol o estado hecho por otro administrador debe invalidar las sesiones anteriores de la cuenta afectada.
93. La recuperación local de un rol administrativo sólo debe habilitarse cuando no quede ninguna cuenta de Administración activa; debe operar sobre una cuenta existente, exigir contraseña segura, invalidar sesiones y quedar auditada sin guardar la credencial.
94. El tema oscuro debe utilizar superficies suaves, texto secundario legible y bordes decorativos discretos, sin eliminar el foco visible requerido para operar con teclado.
95. La acción **Sustituir** de una receta vigente debe distinguirse de **Ver / imprimir**, conservar contraste suficiente en tema claro y oscuro e incluir una etiqueta accesible que identifique el folio.

## Requisitos de seguridad

- Autenticación para toda ruta funcional.
- Roles `admin`, `medico`, `recepcion` aplicados en servidor.
- CSRF, cookies protegidas, secreto persistente y bloqueo por intentos.
- Validación autoritativa de todos los datos mutables.
- Registro de eventos críticos sin contraseñas ni contenido clínico completo.
- Invalidación de sesiones tras cambios de credencial, rol o estado y cambio obligatorio para contraseñas temporales.
- Escucha exclusiva en localhost.
- CSP autocontenida con nonce y bloqueo de atributos ejecutables.
- Respaldo y restauración SQLite verificables, auditados y restringidos a Administración.

## Requisitos no funcionales

- Python 3.10+.
- SQLite y dependencias instalables mediante ruedas/paquetes Python sin Cython.
- PyInstaller en Windows sin guardar datos en `_MEIPASS`.
- Conservación del diseño visual existente.
- Suite unificada ejecutable mediante `python -m pytest -q`; incluye los casos heredados de `unittest`.
