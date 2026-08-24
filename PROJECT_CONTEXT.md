# Contexto vivo del proyecto

## Estado actual

La versión 1.6.3 es un expediente clínico general para servicios médicos, dentales, nutricionales u otras áreas de salud. La tabla y el blueprint de `valoracion` conservan el nombre histórico por compatibilidad, pero la interfaz usa “consulta clínica”. La receta ordinaria es un documento separado de la nota y mantiene un historial de folios.

## Reglas que deben preservarse

1. El diseño actual, basado en Tailwind/Alpine y paleta esmeralda, se mantiene hasta una futura renovación.
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
20. La identidad de la cuenta y el cierre de sesión viven en el top bar; el sidebar se reserva para navegación.
21. `app/static/img/logo.png` es la identidad canónica y `logo.ico` es su derivado para Windows.
22. Todo cambio/restablecimiento de contraseña incrementa `auth_version`; ninguna bitácora o log puede contener la credencial.
23. La recuperación local sólo restablece administradores y siempre obliga a crear una contraseña definitiva.
24. La cabecera compacta muestra `username`; el menú rotula por separado nombre registrado, rol de acceso, área clínica y cédula para evitar confundir identidad con permisos.
25. Las actualizaciones sobre una carpeta existente deben ejecutar `scripts/cleanup_project.py`; la limpieza nunca debe tocar `.venv`, `instance` o `backups`.
26. El Panel Clínico muestra un título de módulo, no un segundo nombre de cuenta; el detalle de cuenta inicia con el atributo nativo `hidden` y sólo se abre por acción explícita.
27. La visibilidad del menú de cuenta no debe depender de Alpine o de otro recurso CDN; el fallo seguro es permanecer cerrado.
28. El dashboard sólo presenta métricas derivadas de la base: pacientes activos, citas de hoy y consultas del mes; no muestra ingresos ni módulos inexistentes.
29. El top bar, sidebar, `logo.png` y `logo.ico` quedan fuera del alcance del rediseño 1.6.3.
30. Recepción puede ver la operación de citas y pacientes, pero no conteos, pendientes, actividad o acciones clínicas.

## Próximas fases

- Cifrado en reposo y administración de llaves.
- Firma electrónica jurídicamente evaluada y cierre/versionado de notas clínicas.
- Flujos regulatorios separados para medicamentos controlados, sólo tras revisión jurídica y operativa.
- Recursos frontend autocontenidos.
- Reportes y métricas configurables por especialidad.
- Multi-consultorio únicamente después de incorporar aislamiento por tenant.
