import os
import zipfile
from datetime import datetime

def crear_respaldo_codigo():
    """
    Empaqueta el código fuente del proyecto SistemaPacientes en un archivo ZIP con timestamp,
    excluyendo carpetas virtuales, bases de datos y archivos binarios/temporales.
    """
    # Directorio raíz del proyecto
    root_dir = os.path.abspath(os.path.dirname(__file__))
    
    # Generar nombre del ZIP con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    zip_filename = f"CodigoFuente_SistemaPacientes_{timestamp}.zip"
    zip_path = os.path.join(root_dir, zip_filename)

    # Extensiones permitidas (código fuente y documentación)
    allowed_extensions = ('.py', '.html', '.js', '.css', '.json', '.md', '.bat', '.spec', '.sh')

    # Directorios y archivos a ignorar explícitamente
    ignored_dirs = {'venv', '__pycache__', '.git', 'instance', 'dist', 'build', '.vscode', 'logs', 'migrations'}
    ignored_extensions = ('.db', '.sqlite', '.exe', '.pyc', '.zip')

    archivos_incluidos = []

    print("========================================================")
    print("      CREANDO RESPALDO DE CÓDIGO FUENTE - SGPN          ")
    print("========================================================")

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for foldername, subfolders, filenames in os.walk(root_dir):
            # Modificar subfolders in-place para evitar que os.walk entre en directorios ignorados
            subfolders[:] = [d for d in subfolders if d not in ignored_dirs and not d.startswith('.')]

            # Verificar si la carpeta actual está dentro de un directorio ignorado
            rel_path = os.path.relpath(foldername, root_dir)
            if rel_path != '.':
                path_parts = rel_path.split(os.sep)
                if any(part in ignored_dirs for part in path_parts):
                    continue

            for filename in filenames:
                # Omitir archivos con extensiones no deseadas o el propio zip que se está creando
                if filename.endswith(ignored_extensions) or filename == zip_filename:
                    continue

                # Verificar extensión permitida
                if not filename.lower().endswith(allowed_extensions):
                    # Permitir algunos archivos sin extensión si es necesario, pero requerimos fuentes conocidas
                    if not any(filename.endswith(ext) for ext in allowed_extensions):
                        continue

                file_path = os.path.join(foldername, filename)
                arcname = os.path.relpath(file_path, root_dir)
                
                try:
                    zipf.write(file_path, arcname)
                    archivos_incluidos.append(arcname)
                    print(f"[INCLUIDO] {arcname}")
                except Exception as e:
                    print(f"[ADVERTENCIA] No se pudo incluir {arcname}: {e}")

    print("========================================================")
    print(f"[EXITO] Respaldo generado correctamente en:")
    print(f"        {zip_path}")
    print(f"        Total de archivos incluidos: {len(archivos_incluidos)}")
    print("========================================================")

if __name__ == '__main__':
    crear_respaldo_codigo()
