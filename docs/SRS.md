# Especificación de requisitos — Sistema de Expediente Clínico

## Alcance

Aplicación local para gestionar pacientes y expedientes en consultorios médicos, dentales, nutricionales u otros servicios de salud. La versión 1.6.3 no implementa multi-tenancy ni operación directa por Internet.

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
22. Identidad de cuenta en top bar sin duplicarla en sidebar e iconografía institucional unificada.
23. Recetas originales, adicionales y sustituciones con folios independientes e historial inmutable.
24. Folios sustituidos marcados como no vigentes y enlazados al reemplazo.
25. Cambio propio, restablecimiento administrativo y recuperación local de contraseñas para administradores.
26. Identidad compacta mediante nombre de usuario y detalle rotulado de nombre, rol, área clínica y cédula en el menú de cuenta.
27. Limpieza segura y explícita de recursos obsoletos al actualizar sobre una carpeta existente.

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
