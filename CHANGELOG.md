# CHANGELOG

## [1.0.0] - 2026-07-23

### Auditoría y Limpieza
- Eliminación de carpeta `output/` que contenía artefactos de compilación y respaldos innecesarios.

### Refactorización
- Creación de `app/utils/` para centralizar lógica reutilizable.
- Creación de `app/utils/helpers.py` con funciones:
    - `safe_float(val, default)`: Conversión segura a float.
    - `safe_int(val, default)`: Conversión segura a int.
    - `validar_campos(form, campos_requeridos)`: Validación centralizada de campos obligatorios.
- Refactorización de `app/controllers/valoracion_antropometrica.py`:
    - Eliminación de funciones `safe_float` y `safe_int` locales.
    - Uso de `validar_campos` para validación de formularios.
- Refactorización de `app/controllers/historial_clinico.py`:
    - Uso de `validar_campos` para validación de formularios.

### Limpieza Adicional
- Eliminación de dependencias de Node.js (`node_modules/`, `package.json`, `package-lock.json`) al no ser requeridas para el proyecto.

### Documentación
- Actualización de `README.md` para reflejar la nueva estructura de carpetas.
