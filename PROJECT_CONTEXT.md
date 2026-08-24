# Contexto vivo del proyecto

## Estado actual

La versión 1.7.2 es un expediente clínico general para servicios médicos, dentales, nutricionales u otras áreas de salud. La tabla y el blueprint de `valoracion` conservan el nombre histórico por compatibilidad, pero la interfaz usa “consulta clínica”. La receta ordinaria es un documento separado de la nota y mantiene un historial de folios.

## Reglas que deben preservarse

1. El diseño actual conserva Tailwind; el shell 1.7.2 combina azul petróleo/teal, JavaScript local y tema claro/oscuro persistente. Alpine queda sólo por compatibilidad con vistas legadas.
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
29. El top bar y sidebar 1.7.2 usan control local accesible; `logo.png` y `logo.ico` permanecen como recursos canónicos sin modificación.
30. Recepción puede ver la operación de citas y pacientes, pero no conteos, pendientes, actividad o acciones clínicas.
31. Recetas se abre desde el sidebar como contexto de la lista de consultas; no se inventa un índice clínico nuevo.
32. Plantillas, usuarios, auditoría y configuración pertenecen al grupo desplegable Administración; Configuración permanece planificada.
33. Los KPI integran consulta y acción en controles separados; no debe volver a crearse una fila paralela de Acciones rápidas.
34. El topbar permanece fuera del desplazamiento del contenido mediante un shell limitado al viewport.
35. Las pestañas y acciones del formulario clínico deben conservar contraste oscuro propio; sus divisores no pueden heredar líneas blancas del tema claro.
36. En el detalle del paciente, Historial Médico precede a Alimentación y Actividad Física.
37. **Sin consulta reciente** es un seguimiento nutricional: sólo se consulta y renderiza cuando el perfil profesional efectivo es `nutricion`.
38. La agenda rápida sólo se enlaza desde la acción del KPI Citas de hoy; no se duplica en sidebar ni reemplaza el modal del detalle.
39. El flujo rápido sólo crea citas para pacientes activos sin cita programada; reagendar continúa siendo responsabilidad del detalle del paciente.
40. La disponibilidad visual es orientativa y siempre se revalida dentro de la operación protegida del servidor antes de confirmar.
41. La agenda rápida no precarga ni renderiza el padrón de pacientes: exige una búsqueda de al menos dos caracteres, limita las coincidencias y mantiene visible sólo la ficha elegida.
42. Agenda de hoy, Próximas citas y Pacientes recientes permanecen sin cambios funcionales en 1.7.2; cualquier simplificación propuesta requiere una decisión posterior y pruebas de Dashboard.
43. `numero_cita` representa un turno diario global: el navegador nunca lo decide, `(fecha, numero_cita)` es único y la secuencia se reinicia para cada fecha.
44. La proyección visual del turno no constituye una reserva. El servidor vuelve a calcularlo dentro del bloqueo de escritura inmediatamente antes de guardar.
45. Un turno asignado es una referencia histórica. No se renumeran notas posteriores al eliminar o mover una consulta; los totales diarios se calculan mediante `COUNT`, nunca mediante `MAX(numero_cita)`.
46. En receta, la tarjeta nueva aparece arriba por usabilidad, pero `orden_medicamento[]` debe ser consecutivo, único y autoritativamente ordenado por el servidor antes de persistir e imprimir.

## Próximas fases

- Cifrado en reposo y administración de llaves.
- Firma electrónica jurídicamente evaluada y cierre/versionado de notas clínicas.
- Flujos regulatorios separados para medicamentos controlados, sólo tras revisión jurídica y operativa.
- Recursos frontend autocontenidos.
- Reportes y métricas configurables por especialidad.
- Multi-consultorio únicamente después de incorporar aislamiento por tenant.
