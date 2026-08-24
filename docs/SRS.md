# Especificación de requisitos — Sistema de Expediente Clínico

## Alcance

Aplicación local para gestionar pacientes y expedientes en consultorios médicos, dentales, nutricionales u otros servicios de salud. La versión 1.7.3 no implementa multi-tenancy ni operación directa por Internet.

## Requisitos funcionales

1. Alta, búsqueda, edición y activación/desactivación de pacientes.
2. Datos generales, ocupación, dirección y contacto de emergencia.
3. Expediente con antecedentes, alergias, medicación y hábitos.
4. Consultas con signos vitales, síntomas, impresión diagnóstica, plan e indicaciones clínicas.
5. Antropometría opcional sin bloquear consultas generales.
6. Citas con fecha, hora, motivo y estado.
7. Pagos con fecha, monto, concepto y método.
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
28. Agenda rápida sin precarga del padrón: búsqueda autenticada y limitada por nombre, expediente o teléfono, con una sola ficha seleccionada visible.
28. Búsqueda global conectada al buscador autorizado de pacientes, breadcrumb y selector informativo de sede local.
29. Tema claro/oscuro persistente, foco visible y navegación de shell operable con teclado.
30. Los módulos no implementados deben identificarse como planificados y no deben exponer rutas ficticias.
31. Dashboard con tres KPI informativos y accionables, agenda, próximas citas, gráfica de citas/consultas, actividad, una sola vista de pendientes y Acompañamiento Intermedio.
32. Estados vacíos, indicador de carga de navegación y mensajes de confirmación sin inventar información clínica.
33. Recetas y Expedientes deben permanecer en el sidebar y no duplicarse como acciones rápidas del dashboard.
34. Plantillas, Usuarios, Auditoría y Configuración deben agruparse bajo Administración sin modificar la autorización de cada destino.
35. El topbar debe permanecer visible mientras se desplaza el contenido y mantener comportamiento adaptable en resoluciones pequeñas.
36. Pestañas, botones secundarios y divisores del formulario clínico deben conservar contraste suficiente en tema oscuro.
37. El detalle debe presentar Historial médico antes de Alimentación y Actividad física.
38. El pendiente de pacientes sin consulta reciente debe mostrarse sólo a perfiles de Nutrición.
39. La acción Agendar cita del KPI debe permitir seleccionar un paciente activo registrado y consultar visualmente disponibilidad sin navegar a su detalle.
40. El calendario rápido debe mostrar 21 días, permitir una fecha posterior y distinguir horarios disponibles, ocupados y transcurridos.
41. La disponibilidad mostrada debe revalidarse al confirmar; el flujo rápido no puede sobrescribir una cita programada existente.
42. La agenda rápida no debe duplicarse en el sidebar ni retirar el agendamiento/reagendamiento existente en el detalle del paciente.
43. Cada consulta debe recibir en servidor un turno global consecutivo por fecha; el primer turno de cada día es `1`.
44. El turno enviado por el navegador no debe aceptarse como autoridad y `(fecha, turno)` debe ser único en SQLite.
45. La migración debe preservar todas las consultas legadas y normalizar su turno de forma determinista.
46. Agregar un medicamento debe insertar la nueva tarjeta arriba sin alterar el orden de captura persistido e impreso `1..n`.
47. El servidor debe rechazar órdenes de medicamentos incompletos, repetidos o no consecutivos.
48. La receta impresa debe usar una lista compacta sin tarjetas por medicamento, omitir sólo campos opcionales vacíos, mantener juntos los datos de cada medicamento al paginar y conservar todos los datos obligatorios.

## Requisitos de seguridad

- Autenticación para toda ruta funcional.
- Roles `admin`, `medico`, `recepcion` aplicados en servidor.
- CSRF, cookies protegidas, secreto persistente y bloqueo por intentos.
- Validación autoritativa de todos los datos mutables.
- Registro de eventos críticos sin contraseñas ni contenido clínico completo.
- Invalidación de sesiones tras cambios de credencial y cambio obligatorio para contraseñas temporales.
- Escucha exclusiva en localhost.

## Requisitos no funcionales

- Python 3.10+.
- SQLite y dependencias instalables mediante ruedas/paquetes Python sin Cython.
- PyInstaller en Windows sin guardar datos en `_MEIPASS`.
- Conservación del diseño visual existente.
- Suite unificada ejecutable mediante `python -m pytest -q`; incluye los casos heredados de `unittest`.
