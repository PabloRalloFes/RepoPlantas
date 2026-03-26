#!/usr/bin/env python3
"""
Script para ejecutar el servidor Flask del proyecto.

Uso:
  python run_server.py              # HTTP en localhost:5001
  python run_server.py --https      # HTTPS en localhost:5001 (recomendado)
  python run_server.py --port 8000  # Cambiar puerto
  
Ejemplos:
  python run_server.py --https --port 5001
"""

import argparse
import subprocess
import sys
from pathlib import Path

def generate_certificates_if_needed():
    """Genera certificados SSL si no existen."""
    project_root = Path(__file__).parent
    cert_dir = project_root / "ssl_certs"
    cert_file = cert_dir / "server.crt"
    key_file = cert_dir / "server.key"
    
    # Si ya existen, no hacer nada
    if cert_file.exists() and key_file.exists():
        print(f"✓ Usando certificados SSL existentes en {cert_dir}")
        return True
    
    # Generar certificados
    print("Generando certificados SSL...")
    generate_script = project_root / "server" / "generate_certificates.py"
    
    try:
        result = subprocess.run([sys.executable, str(generate_script)], 
                              capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"✗ Error al generar certificados: {e}")
        return False

def run_flask_server(host="0.0.0.0", port=5001, use_https=False, debug=False):
    """Ejecuta el servidor Flask."""
    
    # Importar la app de main.py
    try:
        from main import app
    except ImportError as e:
        print(f"✗ Error al importar main.py: {e}")
        print("Asegúrate de estar en la raíz del proyecto.")
        sys.exit(1)
    
    # Configurar SSL si se requiere
    ssl_context = None
    if use_https:
        print("🔒 Modo HTTPS activado")
        if not generate_certificates_if_needed():
            print("✗ No se pudieron generar los certificados SSL.")
            print("Ejecuta sin --https para usar HTTP simple.")
            sys.exit(1)
        
        project_root = Path(__file__).parent
        cert_dir = project_root / "ssl_certs"
        cert_file = cert_dir / "server.crt"
        key_file = cert_dir / "server.key"
        ssl_context = (str(cert_file), str(key_file))
    
    # Mostrar información
    protocol = "https" if use_https else "http"
    mode_text = "Desarrollo (auto-recarga activado)" if debug else "Producción (sin auto-recarga)"
    print("=" * 70)
    print(f"🚀 Servidor Flask iniciado")
    print(f"📍 URL: {protocol}://{host}:{port}")
    print(f"🔧 Modo: {mode_text}")
    if not debug:
        print("   💡 Usa --dev para activar modo desarrollo con auto-recarga")
    print("=" * 70)
    print()
    print("Presiona Ctrl+C para detener el servidor")
    print()
    
    # Ejecutar Flask
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug,
            ssl_context=ssl_context
        )
    except KeyboardInterrupt:
        print("\n✓ Servidor detenido")
    except Exception as e:
        print(f"\n✗ Error al ejecutar el servidor: {e}")
        sys.exit(1)

def run_waitress_server(host="0.0.0.0", port=5001):
    """Ejecuta la API con Waitress (WSGI) para un entorno de producción sencillo."""
    try:
        from main import app
    except ImportError as e:
        print(f"✗ Error al importar main.py: {e}")
        sys.exit(1)

    try:
        from waitress import serve
    except ImportError:
        print("✗ Falta waitress. Instala dependencias con: pip install -r requirements.txt")
        sys.exit(1)

    print("=" * 70)
    print("🚀 Servidor Waitress iniciado")
    print(f"📍 URL: http://{host}:{port}")
    print("🔧 Modo: Producción WSGI")
    print("=" * 70)
    print()
    print("Presiona Ctrl+C para detener el servidor")
    print()

    try:
        serve(app, host=host, port=port, threads=8)
    except KeyboardInterrupt:
        print("\n✓ Servidor detenido")
    except Exception as e:
        print(f"\n✗ Error al ejecutar Waitress: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Ejecuta el servidor Flask del proyecto",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python run_server.py                              # HTTP en localhost:5001
  python run_server.py --https                      # HTTPS en localhost:5001 (recomendado)
  python run_server.py --https --port 8000          # HTTPS en puerto 8000
  python run_server.py --https --dev                # HTTPS con auto-recarga (desarrollo)
  python run_server.py --https --dev --port 8000    # HTTPS con auto-recarga en puerto 8000
        """
    )
    
    parser.add_argument(
        "--https",
        action="store_true",
        help="Usar HTTPS con certificados autofirmados (recomendado)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=5001,
        help="Puerto del servidor (default: 5001)"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host del servidor (default: 0.0.0.0 - accesible desde red local)"
    )
    
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Activar modo desarrollo con auto-recarga (desactiva por defecto para evitar reinicios durante entrenamientos)"
    )

    parser.add_argument(
        "--prod",
        action="store_true",
        help="Ejecutar con servidor WSGI de producción (Waitress)"
    )
    
    args = parser.parse_args()
    
    if args.prod:
        if args.https:
            print("✗ --prod y --https no se usan juntos. Usa HTTPS en proxy inverso (Nginx/Caddy).")
            sys.exit(1)
        run_waitress_server(host=args.host, port=args.port)
        return

    # Ejecutar servidor Flask integrado (desarrollo/local)
    run_flask_server(host=args.host, port=args.port, use_https=args.https, debug=args.dev)

if __name__ == "__main__":
    main()
