# 🖥️ Servidor / Backend API - Guía de Configuración

Esta carpeta contiene la configuración y scripts para ejecutar el **servidor API HTTPS** que potencia la aplicación de escritorio (`main_app.py`).

> **Nota:** La mayoría de usuarios interactuarán con este servidor a través de la aplicación de escritorio. El acceso directo al servidor es principalmente para desarrolladores y administradores.

---

## ⚡ Inicio Rápido (3 Pasos)

### 1️⃣ Instala las dependencias (una sola vez)
```bash
pip install -r requirements.txt
```

### 2️⃣ Elige cómo iniciar

**Opción A - Menú Interactivo (Más Fácil):**
- **Windows**: Doble clic en `server/run_server.cmd`
- **Linux/Mac**: `chmod +x server/run_server.sh && ./server/run_server.sh`

**Opción B - Línea de Comandos (Más Directo):**
```bash
python run_server.py --https
```

### 3️⃣ ¡Listo!
La API estará corriendo en: **`https://localhost:5001`**

La aplicación de escritorio (`main_app.py`) se conectará automáticamente si se ejecuta en la misma máquina.

---

## 🏗️ ¿Qué es este Servidor?

Este es un **backend API Flask** que:
- ✅ Gestiona autenticación de usuarios y roles
- ✅ Maneja subida y almacenamiento de imágenes (MongoDB)
- ✅ Procesa solicitudes de clasificación
- ✅ Proporciona gestión de experimentos

**La App se comunica con Este Servidor:**
```
┌─────────────────┐
│   main_app.py   │  (Aplicación de escritorio)
│  (GUI - Flet)   │
└────────┬────────┘
         │ Peticiones HTTPS
         ↓
┌─────────────────────┐
│  run_server.py      │  (Este archivo)
│  API & Backend      │
└────────┬────────────┘
         │ MongoDB
         ↓
┌─────────────────────┐
│    MongoDB          │
│  Almacenamiento     │
│  de Imágenes        │
└─────────────────────┘
```

---

## 📝 Ejecutar el Servidor

### Menú Interactivo (Recomendado para usuarios nuevos)
```bash
# Windows
cd server && run_server.cmd

# Linux/Mac
./server/run_server.sh
```

Aparecerá un menú con 5 opciones. Elige tu configuración preferida.

---

### Línea de Comandos (Más Control)

| Comando | Cuándo utilizarlo |
|---------|------------------|
| `python run_server.py --https` | **RECOMENDADO** - HTTPS con auto-recarga |
| `python run_server.py` | Modo HTTP (solo testing, menos seguro) |
| `python run_server.py --https --port 8443` | Puerto personalizado (si 5001 está en uso) |
| `python run_server.py --host 0.0.0.0 --https` | Permitir conexiones remotas |

**Para la mayoría de usuarios:** `python run_server.py --https` es perfecto.

**Nota:** El servidor se ejecuta en modo desarrollo con auto-recarga, lo cual es perfecto para uso local y desarrollo.

---

## 🔐 HTTPS y Certificados

### ¿Por qué HTTPS?
- ✅ Cifra datos entre app y servidor
- ✅ Requerido para conexiones seguras modernas
- ✅ Los certificados autofirmados funcionan bien para uso interno

### Certificados Autofirmados
- Se generan automáticamente en la primera ejecución
- Válidos por 365 días
- Se almacenan en `ssl_certs/` (directorio raíz)
- ⚠️ Los navegadores pueden mostrar advertencia (esto es normal y seguro para uso interno)

**La Aplicación de Escritorio acepta certificados autofirmados automáticamente** - sin acción necesaria.

---

## ⚙️ Requisitos

### Requisitos del Sistema
- Python 3.8+
- OpenSSL (para generar certificados)
  - **Windows**: Descarga desde https://slproweb.com/products/Win32OpenSSL.html
  - **Linux**: `sudo apt-get install openssl`
  - **Mac**: `brew install openssl`

### Paquetes Python (desde requirements.txt)
- Flask - Framework web
- httpx - Cliente HTTP
- PyMongo - Conexión a MongoDB
- Torch/TorchVision - Modelos ML
- Flet - Framework de app de escritorio

---

## 🔍 Verificar la Configuración

Antes de desplegar, valida que todo está correctamente configurado:

```bash
python server/validate_setup.py
```

Debe mostrar ✓ en todos los checks. Si algo falla, te indicará qué instalar.

---

## 🌐 Acceso Remoto (Máquina Diferente)

Si necesitas conectar la app desde una **máquina diferente** en la misma red:

### Paso 1: Obtén la IP de tu Servidor
```bash
# Windows
ipconfig

# Linux/Mac
ifconfig
```

Busca algo como: `192.168.1.100` o `10.0.0.50`

### Paso 2: Configura la App para Usar esa IP

En `logicav3.py` en la máquina cliente, cambia:
```python
# Línea 8 - cambiar de:
URL_API = "https://localhost:5001"

# A la IP de tu servidor:
URL_API = "https://192.168.1.100:5001"  # Reemplaza con tu IP actual
```

### Paso 3: Añade Excepción para Certificado

En las peticiones, añade `verify=False`:
```python
res = httpx.post(url, json=data, verify=False)
```

### Requisitos de Red
- Ambas máquinas en la **misma red** (LAN del campus o VPN de universidad)
- Firewall permite puerto 5001
- Si no estás seguro, contacta a tu departamento de TI

---

## 📁 Contenido de la Carpeta server/

```
server/
├── run_server.cmd              # Menú interactivo (Windows)
├── run_server.sh               # Menú interactivo (Linux/Mac)
├── generate_certificates.py    # Generador de certificados SSL
├── validate_setup.py           # Verificador de dependencias
└── README.md                   # Este archivo
```

---

## 🆘 Solución de Problemas

### "OpenSSL no encontrado"
```bash
# Windows con Chocolatey
choco install openssl

# O descarga: https://slproweb.com/products/Win32OpenSSL.html
```

### "El puerto 5001 ya está en uso"
```bash
# Usa un puerto diferente
python run_server.py --https --port 8443
```

### "No puedo conectar desde otra máquina"
- ✅ ¿Ambas máquinas en la **misma red**?
- ✅ ¿El firewall permite puerto 5001?
- ✅ ¿Usando la IP correcta (no `localhost`)?

### "Errores de certificado"
- **En la app**: Añade `verify=False` a las peticiones httpx
- **Errores del sistema**: Verifica que OpenSSL está correctamente instalado

---

## ❓ Preguntas Frecuentes

**P: ¿Puedo usar HTTP en lugar de HTTPS?**
A: Sí, con `python run_server.py` (sin --https) para testing. HTTPS es más seguro.

**P: ¿Por qué la aplicación necesita este servidor?**
A: El servidor gestiona la base de datos, autenticación de usuarios y procesamiento de imágenes. La app es solo la interfaz.

**P: ¿Funciona en Windows?**
A: Sí, funciona perfectamente en Windows, Linux y Mac.

**P: ¿Dónde se almacenan los certificados?**
A: En la carpeta `ssl_certs/` en la raíz del proyecto (se generan automáticamente).

**P: ¿Puedo usar esto en producción?**
A: Este servidor de desarrollo es adecuado para uso local/interno. Para producción pública, considera usar un servidor WSGI apropiado detrás de nginx.

---

## 📚 Documentación Relacionada

- **Proyecto Principal**: [README.md](../README.md) o [README_ES.md](../README_ES.md)
- **Guía de la App de Escritorio**: Ver `README_APP.md` en la raíz
- **Código de la API**: [main.py](../main.py)
- **Código de la App**: [main_app.py](../main_app.py)

---

## 🎯 Próximos Pasos

1. Ejecuta `python server/validate_setup.py`
2. Inicia el servidor: `python run_server.py --https`
3. Ejecuta la app de escritorio: `python main_app.py`
4. Inicia sesión y prueba la funcionalidad

---

*Última Actualización: Febrero 2026 | TFG Clasificación de Enfermedades de Plantas*
