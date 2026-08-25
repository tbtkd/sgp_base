# Consultas simplificadas y datos demo — versión 1.9.0

## Objetivo

Esta versión reduce la densidad del módulo **Consultas**, conserva el acceso histórico requerido por **Recetas** y permite validar el sistema con información completamente ficticia sin cargarla automáticamente.

## Consultas clínicas

La ruta `/valoraciones/` muestra una sola fila por paciente con:

- nombre y expediente;
- fecha de la nota más reciente;
- acción **Ver nota**.

La consulta más reciente se decide por `fecha DESC`, `numero_cita DESC` e `id DESC`. Esto evita resultados ambiguos cuando un paciente tiene más de una atención en el mismo día.

El filtro `q` se normaliza en servidor con una función Unicode local para buscar nombres y apellidos sin depender de mayúsculas o acentos. `orden` sólo acepta `fecha_desc` y `fecha_asc`; cualquier otro valor vuelve al orden descendente. La página se limita a 25 pacientes y un número inválido se normaliza sin provocar error 500.

El índice no expone motivo, diagnóstico ni prescripción. Recepción y usuarios anónimos continúan sin acceso.

## Compatibilidad con Recetas

`/valoraciones/?origen=recetas` conserva todas las consultas específicas. Esta separación es intencional: una receta existente o adicional puede estar asociada con una nota anterior, por lo que deduplicar ese contexto ocultaría documentos clínicos válidos.

## Importación antropométrica

El botón **Importar Excel**, el formulario de archivo y el modal de resultado sólo se renderizan cuando `current_user.puede_capturar_antropometria` es verdadero.

La protección principal permanece en el servidor. Un usuario de Medicina general u Odontología que construya manualmente el POST recibe HTTP 403 antes de que el sistema confirme si el paciente existe. El intento queda en auditoría como `IMPORTAR_CONSULTAS`, resultado `denied`, sin copiar datos clínicos o el contenido del archivo.

## Carga de demostración

La carga es opcional y nunca se ejecuta con `run.py`. Antes de usarla, respalda la base o utiliza una instalación separada:

```powershell
python seed_demo.py --confirm
```

Crea, sólo cuando no existen:

- `demo_medico`, `demo_dentista`, `demo_nutricion` y `demo_recepcion`;
- seis pacientes con correos `example.test` y teléfonos identificables;
- seis historiales, nueve consultas —incluyendo varias del mismo paciente—, cuatro citas y tres pagos;
- una receta ficticia con tres medicamentos en orden;
- `demo_data/expediente_antropometrico_demo.xlsx` con tres mediciones históricas.

La contraseña robusta compartida por las cuentas creadas se muestra una sola vez. Puede establecerse previamente mediante `SGPN_DEMO_PASSWORD`. Si una cuenta ya existe, su contraseña no se reemplaza. Ejecutar el comando nuevamente no duplica el conjunto.

Para validar la restricción Excel:

1. Inicia como `demo_medico` o `demo_dentista`: **Importar Excel** no debe aparecer.
2. Inicia como `demo_nutricion`: la opción debe aparecer en el detalle del paciente.
3. Carga `demo_data/expediente_antropometrico_demo.xlsx`.
4. Confirma que se agreguen tres consultas antropométricas y que el turno diario sea asignado por el servidor.

Los datos demo no deben convivir con información clínica real. Desactiva las cuentas o descarta la base de pruebas al terminar.

## Pruebas añadidas

`tests/test_consultation_index.py` cubre ocho escenarios:

1. paciente único y nota más reciente determinista;
2. búsqueda normalizada, orden y parámetros inválidos;
3. paginación sin repeticiones;
4. conservación del contexto histórico de Recetas;
5. visibilidad de Excel sólo para Nutrición;
6. rechazo y auditoría de solicitudes forjadas;
7. idempotencia de la carga demo, receta ordenada y generación XLSX.
8. importación real del XLSX demostrativo usando el perfil de Nutrición.

Resultado acumulado: **97 pruebas aprobadas**, incluidas las 15 pruebas heredadas compatibles con `unittest`.
