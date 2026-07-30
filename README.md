# Sistema de Gestión de Pacientes y Nutrición (SGPN)

Plataforma web integral desarrollada para profesionales de la salud y nutriólogos, optimizada para la gestión de expedientes clínicos, valoraciones antropométricas avanzadas, agendamiento de citas, control de pagos, plantillas de WhatsApp y empaquetado como aplicación de escritorio en Windows.

## 1. Stack Tecnológico y Arquitectura
- **Backend**: Python 3.10+, Flask, Flask-SQLAlchemy, SQLite.
- **Frontend**: HTML5, Tailwind CSS, Alpine.js, Jinja2.
- **Arquitectura**: Patrón Modular por Blueprints con separación estricta de responsabilidades (SoC), auto-migración en caliente y control de instancia única.

## 2. Guía de Instalación y Desarrollo
1. Clonar el repositorio y crear el entorno virtual:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```
2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecutar la aplicación en desarrollo:
   ```bash
   python run.py
   ```

## 3. Empaquetado de Ejecutable (Windows)
Para generar el archivo ejecutable `.exe` independiente mediante PyInstaller:
- Ejecutar el script automatizado:
  ```cmd
  build_exe.bat
  ```

## 4. Respaldo de Código Fuente
Para generar un respaldo comprimido en ZIP de todo el código fuente con marca temporal:
```bash
python respaldar_codigo.py
```
