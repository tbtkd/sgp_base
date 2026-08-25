# Legibilidad del sidebar y contraste — versión 1.7.6

## Objetivo

Corregir tres detalles de presentación sin modificar datos, permisos, rutas o reglas clínicas:

1. Simplificar a **Domicilio** el rótulo impreso en la receta.
2. Mejorar la lectura del sidebar en pantallas de escritorio.
3. Evitar fondos blancos de bajo contraste al pasar el puntero en tema oscuro.

## Cambios aplicados

### Receta

La plantilla imprime:

```text
Domicilio: <valor conservado en la receta>
```

El modelo, la base y la instantánea continúan utilizando `domicilio_profesional`. El cambio es únicamente editorial, por lo que no requiere migración ni altera recetas ya emitidas.

### Sidebar

Se aumentaron de forma moderada:

- nombre del sistema;
- títulos General, Clínico, Gestión y Otros;
- enlaces e iconos principales;
- enlaces del grupo Administración;
- distintivos informativos;
- nombre, rol y perfil del usuario.

Se conservan el ancho, el orden, los iconos, las rutas, los permisos, el desplazamiento interno y el comportamiento móvil.

### Tema oscuro

Las utilidades heredadas `hover:bg-gray-*`, `hover:bg-teal-*`, `hover:bg-emerald-*`, `hover:bg-amber-*` y `hover:bg-red-*` ahora tienen equivalentes oscuros explícitos. La corrección cubre tablas, filas, tarjetas y botones que anteriormente podían cambiar a blanco mientras su texto permanecía claro.

El estado sigue comunicándose con texto, iconos y bordes; no depende únicamente del color. Los estilos de foco por teclado permanecen intactos.

## Dependencias y datos

- No se agregaron dependencias.
- `requirements.txt`, `requirements-dev.txt` y `requirements-build.txt` no requieren cambios.
- No se modificó el esquema SQLite.
- No existe migración para esta entrega.
- No cambian roles, perfiles profesionales ni autorizaciones.

## Pruebas de regresión

- La impresión contiene **Domicilio** y no contiene el rótulo anterior.
- El favicon continúa versionado con la versión vigente.
- El CSS conserva los tamaños reforzados del sidebar.
- El tema oscuro contiene estados `hover` explícitos para filas grises y acciones teal.
- La suite completa debe finalizar con 80 casos aprobados.

Consulta también [MANUAL_USUARIO.md](MANUAL_USUARIO.md), [TEST_MATRIX.md](TEST_MATRIX.md) y [ROADMAP_MODULOS_UI_CITAS.md](ROADMAP_MODULOS_UI_CITAS.md).
