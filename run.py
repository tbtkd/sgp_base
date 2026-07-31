import os
import sys
import socket
import traceback
import webbrowser
from threading import Timer
from app import create_app
from app.__init__ import get_database_path

def is_port_in_use(port, host='127.0.0.1'):
    """Verifica si el puerto especificado ya se encuentra en uso por otro proceso."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

def open_browser(port):
    """Abre el navegador predeterminado en la URL de la aplicación."""
    try:
        webbrowser.open(f'http://127.0.0.1:{port}/')
    except Exception as e:
        print(f"[ADVERTENCIA] No se pudo abrir el navegador automáticamente: {e}")

def show_stylized_error_window():
    """Abre la plantilla HTML estilizada de error de inicio en el navegador o mediante archivo local."""
    try:
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.abspath(os.path.dirname(__file__))
        
        html_path = os.path.join(base_dir, 'app', 'templates', 'errors', 'error_inicio.html')
        if not os.path.exists(html_path):
            # Ruta alternativa si se ejecuta desde la raíz
            html_path = os.path.abspath('app/templates/errors/error_inicio.html')
        
        if os.path.exists(html_path):
            webbrowser.open(f'file:///{os.path.abspath(html_path)}')
    except Exception as e:
        print(f"[ADVERTENCIA] No se pudo abrir la ventana estilizada de error: {e}")

def show_error_dialog(title, message):
    """Muestra una ventana emergente de error en Windows si la consola está oculta o falla stdin."""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x10) # 0x10 = Icono de Error (MB_ICONERROR)
    except Exception:
        pass

def safe_input(prompt="Presiona ENTER para salir..."):
    """Espera la entrada del usuario de forma segura sin fallar si no hay consola (stdin)."""
    try:
        if sys.stdin and sys.stdin.isatty():
            input(prompt)
    except (EOFError, RuntimeError):
        pass

if __name__ == '__main__':
    try:
        print("========================================================")
        print("   INICIANDO SISTEMA DE GESTION DE PACIENTES Y NUTRICION ")
        print("========================================================")
        
        if not getattr(sys, 'frozen', False):
            db_activa = get_database_path()
            print(f"[MODO DEV] Base de datos activa: {db_activa}")
            print("--------------------------------------------------------")
        
        port = int(os.getenv('PORT', 5000))

        # 1. Validacion de Puerto Ocupado
        if is_port_in_use(port):
            error_msg = f"El puerto {port} ya se encuentra ocupado. Es posible que la aplicación ya esté ejecutándose en segundo plano."
            print(f"\n[ERROR CRITICO] {error_msg}")
            show_stylized_error_window()
            safe_input()
            sys.exit(1)

        # 2. Inicializar la app de Flask
        app = create_app()
        
        # 3. Programa la apertura del navegador (usando hilos daemon)
        timer = Timer(1.5, open_browser, args=[port])
        timer.daemon = True  # Permite que el hilo muera si la app se cierra antes
        timer.start()
        
        print(f"[INFO] Servidor corriendo en http://127.0.0.1:{port}/")
        
        # 4. Iniciar servidor Flask
        app.run(
            host='127.0.0.1',
            port=port,
            debug=False,
            use_reloader=False
        )

    except Exception as e:
        # Obtener el traceback formateado
        error_details = traceback.format_exc()

        # Guardar en un archivo físico crash_log.txt para diagnosticar si el cliente no tiene consola
        try:
            exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(".")
            crash_path = os.path.join(exe_dir, "crash_log.txt")
            with open(crash_path, "a", encoding="utf-8") as f:
                f.write(f"\n=== FALLO CRITICO [{os.times()}] ===\n{error_details}\n")
        except Exception:
            pass

        print("\n========================================================")
        print("[ERROR CRITICO] Ocurrio un fallo al iniciar la aplicacion:")
        print("========================================================")
        print(error_details)
        print("\n")

        # Notificar mediante plantilla estilizada y diálogo de respaldo
        show_stylized_error_window()
        show_error_dialog("Error Crítico de Ejecución", f"Ocurrió un error al iniciar la aplicación:\n\n{e}\n\nRevisa el archivo crash_log.txt para más detalles.")

        safe_input()
        sys.exit(1)
