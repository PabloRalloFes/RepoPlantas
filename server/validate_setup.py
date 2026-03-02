#!/usr/bin/env python3
"""
Valida que el ambiente tiene todas las dependencias y configuración
necesarias para ejecutar la API con HTTPS.

Ubicado en: config/validate_setup.py

Ejecutar desde la raíz del proyecto:
  python config/validate_setup.py
"""

import sys
import subprocess
from pathlib import Path
from packaging import version
import shutil

def check_python_version():
    """Verifica que Python >= 3.8."""
    print("1. Verificando versión de Python...")
    py_version = version.parse(f"{sys.version_info.major}.{sys.version_info.minor}")
    required = version.parse("3.8")
    
    if py_version >= required:
        print(f"   ✓ Python {sys.version_info.major}.{sys.version_info.minor} "
              f"({sys.executable})")
        return True
    else:
        print(f"   ✗ Requerido Python 3.8+, tienes {py_version}")
        return False

def check_package(package_name, module_name=None):
    """Verifica si un paquete está instalado."""
    if module_name is None:
        module_name = package_name
    
    try:
        mod = __import__(module_name)
        version_str = getattr(mod, "__version__", "unknown")
        return True, version_str
    except ImportError:
        return False, None

def check_packages():
    """Verifica dependencias del proyecto."""
    print("\n2. Verificando paquetes Python...")
    
    required_packages = {
        "flask": "flask",
        "gunicorn": "gunicorn",
        "httpx": "httpx",
        "pymongo": "pymongo",
        "torch": "torch",
    }
    
    all_ok = True
    for package, module in required_packages.items():
        installed, ver = check_package(package, module)
        if installed:
            print(f"   ✓ {package:<15} v{ver}")
        else:
            print(f"   ✗ {package:<15} NO INSTALADO")
            all_ok = False
    
    return all_ok

def check_main_file():
    """Verifica que existe main.py en la raíz del proyecto."""
    print("\n3. Verificando archivos del proyecto...")
    
    project_root = Path(__file__).parent.parent
    main_file = project_root / "main.py"
    
    if main_file.exists():
        print(f"   ✓ main.py encontrado")
        return True
    else:
        print(f"   ✗ main.py NO encontrado en {project_root}")
        return False

def check_ssl_tools():
    """Verifica que OpenSSL está disponible."""
    print("\n4. Verificando herramientas SSL...")
    
    if shutil.which("openssl"):
        result = subprocess.run(
            ["openssl", "version"],
            capture_output=True,
            text=True
        )
        version_str = result.stdout.strip()
        print(f"   ✓ OpenSSL: {version_str}")
        return True
    else:
        print(f"   ✗ OpenSSL no encontrado en PATH")
        print(f"     Instálalo desde: https://slproweb.com/products/Win32OpenSSL.html")
        return False

def check_certificates():
    """Verifica que existen los certificados SSL."""
    print("\n5. Verificando certificados SSL...")
    
    project_root = Path(__file__).parent.parent
    cert_dir = project_root / "ssl_certs"
    cert_file = cert_dir / "server.crt"
    key_file = cert_dir / "server.key"
    
    if cert_file.exists() and key_file.exists():
        print(f"   ✓ Certificados encontrados en {cert_dir}")
        return True
    else:
        print(f"   ⚠ Certificados NO encontrados (se generarán automáticamente)")
        return None  # No es un error, se generan automáticamente

def check_scripts():
    """Verifica que existen los scripts necesarios."""
    print("\n6. Verificando scripts de configuración...")
    
    config_dir = Path(__file__).parent
    project_root = config_dir.parent
    
    scripts = {
        "run_server.py": config_dir / "run_server.py",
        "generate_certificates.py": config_dir / "generate_certificates.py",
    }
    
    all_ok = True
    for name, path in scripts.items():
        if path.exists():
            print(f"   ✓ {name}")
        else:
            print(f"   ✗ {name} NO encontrado en {path}")
            all_ok = False
    
    return all_ok

def check_mongodb():
    """Verifica si MongoDB está disponible."""
    print("\n7. Verificando MongoDB...")
    
    try:
        import pymongo
        # Simplemente verificar que se puede importar
        print(f"   ✓ PyMongo instalado (v{pymongo.__version__})")
        print(f"   ⚠ Conexión a MongoDB se verifica al iniciar server")
        return True
    except ImportError:
        print(f"   ✗ PyMongo no instalado")
        return False

def main():
    """Ejecuta todas las validaciones."""
    print("="*70)
    print("VALIDACIÓN DE SETUP - API HTTPS")
    print("="*70)
    
    results = {
        "Python": check_python_version(),
        "Paquetes": check_packages(),
        "Archivos": check_main_file(),
        "OpenSSL": check_ssl_tools(),
        "Certificados": check_certificates(),
        "Scripts": check_scripts(),
        "MongoDB": check_mongodb(),
    }
    
    print("\n" + "="*70)
    print("RESUMEN")
    print("="*70)
    
    all_ok = True
    for check, result in results.items():
        if result:
            status = "✓ OK"
        elif result is None:
            status = "⚠ Opcional"
        else:
            status = "✗ FALLA"
            all_ok = False
        
        print(f"{check:<20} {status}")
    
    print("="*70)
    
    if all_ok:
        print("\n✓ Setup validado correctamente.\n")
        print("Para iniciar el servidor:")
        print("  python config/run_server.py --dev --https\n")
        return 0
    else:
        print("\n✗ Hay problemas en el setup. Por favor revisa los errores arriba.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
