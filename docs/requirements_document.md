# Documento de Requerimientos
Sistema de Gestión de Pacientes Nutriológicos (SGPN)

## 1. Introducción

### 1.1 Propósito
Desarrollar un sistema web que permita la gestión integral de pacientes en un consultorio nutricional, facilitando el seguimiento de valoraciones antropométricas y control de historiales clínicos.

### 1.2 Alcance
El sistema debe permitir el registro y seguimiento de pacientes, incluyendo sus valoraciones antropométricas, historial clínico y control de pagos.

## 2. Requerimientos Funcionales

### RF-01: Gestión de Pacientes
- Alta de nuevos pacientes con datos personales
- Edición de información de pacientes
- Cambio de estado (activo/inactivo)
- Búsqueda y filtrado de pacientes
- Visualización separada de pacientes activos e inactivos

### RF-02: Valoraciones Antropométricas
- Registro de medidas corporales completas
- Cálculo automático de IMC
- Registro de signos vitales
- Seguimiento histórico de medidas
- Importación masiva desde Excel

### RF-03: Historial Clínico
- Registro de antecedentes médicos
- Control de medicamentos y suplementos
- Seguimiento de actividad física
- Registro de hábitos alimenticios

### RF-04: Control de Pagos
- Registro de pagos por consulta
- Visualización de estado de pagos
- Historial de pagos por paciente

## 3. Requerimientos No Funcionales

### RNF-01: Usabilidad
- Interfaz intuitiva y responsiva
- Mensajes de error claros
- Tiempo de aprendizaje máximo: 2 horas

### RNF-02: Rendimiento
- Tiempo de respuesta < 3 segundos
- Soporte para múltiples usuarios
- Carga de archivos Excel < 10MB

### RNF-03: Seguridad
- Validación de datos en frontend y backend
- Protección contra inyección SQL
- Control de acceso por roles

### RNF-04: Mantenibilidad
- Código documentado
- Logs para desarrollo
- Respaldos automáticos

## 4. Reglas de Negocio

### RN-01: Pacientes
- Correo electrónico único por paciente
- Teléfono debe tener 10 dígitos
- Estado inicial siempre activo

### RN-02: Valoraciones
- IMC calculado automáticamente
- No permitir duplicados de fecha
- Número de cita auto-incrementable

### RN-03: Pagos
- Un pago por consulta
- Fecha de pago no futura
- Estado de pago visible en listado

## 5. Interfaces

### 5.1 Interfaces de Usuario
- Dashboard principal
- Listado de pacientes
- Formulario de valoración
- Historial clínico
- Carga de Excel

### 5.2 Interfaces de Hardware
- Computadora con navegador web
- Impresora para reportes

### 5.3 Interfaces de Software
- Navegadores: Chrome, Firefox, Safari
- Excel para importación de datos

## 6. Consideraciones Técnicas
- Framework: Flask
- Base de datos: SQLite
- Frontend: HTML5, CSS3, JavaScript
- Control de versiones: Git

## 7. Entregables
- Código fuente
- Manual de usuario
- Manual técnico
- Scripts de base de datos
- Ejecutable para Windows