#!/usr/bin/env python3
"""
Genera certificados SSL autofirmados para uso local.

Ubicado en: config/generate_certificates.py
Los certificados se guardan en: ../ssl_certs/

Ejecutar desde la raíz del proyecto:
  python config/generate_certificates.py
"""

import subprocess
import sys
from pathlib import Path

def generate_certificates():
    """Genera certificados SSL autofirmados usando OpenSSL."""
    
    # Obtener la carpeta raíz (padre de config/)
    config_dir = Path(__file__).parent
    project_root = config_dir.parent
    cert_dir = project_root / "ssl_certs"
    
    # Crear carpeta si no existe
    cert_dir.mkdir(exist_ok=True)
    
    cert_file = cert_dir / "server.crt"
    key_file = cert_dir / "server.key"
    
    # Verificar si ya existen
    if cert_file.exists() and key_file.exists():
        print(f"✓ Certificados ya existen en {cert_dir}")
        print(f"  - {cert_file}")
        print(f"  - {key_file}")
        return True
    
    print(f"Generando certificados SSL en {cert_dir}...")
    print(f"  - private key: {key_file}")
    print(f"  - certificate: {cert_file}")
    print("")
    
    # Comando OpenSSL para generar certificado autofirmado
    cmd = [
        "openssl",
        "req",
        "-x509",
        "-newkey", "rsa:4096",
        "-keyout", str(key_file),
        "-out", str(cert_file),
        "-days", "365",
        "-nodes",
        "-subj", "/C=ES/ST=Madrid/L=Madrid/O=Universidad/CN=localhost"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ Certificados generados exitosamente")
            print(f"")
            print(f"Archivos creados:")
            print(f"  - Clave privada: {key_file}")
            print(f"  - Certificado: {cert_file}")
            print(f"")
            print(f"Validez: 365 días")
            print(f"Algoritmo: RSA 4096-bit")
            print(f"")
            print(f"⚠ Advertencia: Este es un certificado autofirmado.")
            print(f"  Los navigadores mostrarán una advertencia de seguridad.")
            print(f"  Esto es normal para desarrollo/testing en redes internas.")
            return True
        else:
            print(f"✗ Error al generar certificados:")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print(f"✗ Error: OpenSSL no encontrado en el sistema.")
        print(f"")
        print(f"Por favor instala OpenSSL:")
        print(f"  Windows: Descargalo de https://slproweb.com/products/Win32OpenSSL.html")
        print(f"  Linux:   sudo apt-get install openssl")
        print(f"  macOS:   brew install openssl")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False

if __name__ == "__main__":
    success = generate_certificates()
    sys.exit(0 if success else 1)
