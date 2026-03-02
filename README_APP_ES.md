# **App de Clasificación y Gestión de Imágenes de Plantas**

Esta app forma parte de un sistema diseñado para recopilar, almacenar y etiquetar imágenes de hojas de plantas sanas y enfermas. Permite a los usuarios interactuar con la base de datos de imágenes y realizar tareas específicas según su rol: **usuario**, **etiquetador** o **administrador**.

---

## **📋 Funcionalidades principales**

### **Para usuarios:**
- Subir imágenes de hojas de plantas:
  - **Subida individual**: Sube una imagen a la base de datos.
  - **Subida masiva**: Sube múltiples imágenes organizadas en carpetas, busca las carpetas en el PC donde se está ejecutando la API. Solo para Usuarios+.
- Realizar predicciones básicas utilizando modelos entrenados*
- **Experimentos**:
  - Ver resultados de experimentos existentes
  - Comparar experimentos existentes
  - Crear un nuevo experimento y solicitar su entrenamiento

### **Para etiquetadores:**
- Validar imágenes subidas por los usuarios.
- Revisar y editar etiquetas asociadas a las imágenes.
- Modificar las clases existentes en la base de datos.

### **Para administradores:**
- Gestionar usuarios:
  - Añadir nuevos usuarios.
  - Eliminar usuarios existentes.
  - Modificar roles de usuario (usuario, etiquetador, administrador).
- Aprobar solicitudes de entrenamiento de modelos.

### **Otras funcionalidades:**
- Registro de nuevos usuarios.
- Cambiar la IP de la API desde la app.
- Cambiar la dirección de la base de datos

---

## **⚙️ Requisitos**

- Python 3.8 o superior.
- Flutter 3.16.7 para crear la apk
- Instalar las dependencias del proyecto:
  ```bash
  pip install -r requirements.txt
  ```

## **Para usar la app conectada a la API principal:**  
- **Uso básico:**
  - Ejecuta el archivo `main_app.py`:
    ```bash
    python main_app.py
    ```
  - Conéctate a la API principal (cuando esté disponible).  
    Si necesitas cambiar la IP de la API, puedes hacerlo desde la configuración de la app.

---

## **Para usar la app con tu propia base de datos local:**
Si deseas trabajar con tu propia base de datos MongoDB local, sigue estos pasos adicionales:

1. **Clonar el repositorio:**
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd <CARPETA_DEL_REPOSITORIO>
   ```

2. **Configurar la base de datos local:**
  - Asegúrate de tener MongoDB instalado y corriendo en tu máquina.
  - Ejecuta el script setup_bbdd.py para inicializar la base de datos:
  ```bash
  python scripts/setup_bbdd.py
  ```

3. **Ejecutar la API:**
  - Inicia la API en tu máquina local:
  ```bash
  python main.py
  ```

4. **Cambiar la URL de la API y la base de datos:**

  - Desde la app, cambia la URL de la API para que apunte a tu máquina local (por ejemplo, http://127.0.0.1:5001).

5. **Subir imágenes y trabajar con tu base de datos:**
  - Usa la funcionalidad de subida masiva o individual desde la app.
  - Realiza validaciones, ediciones y experimentos con tu base de datos local.

## 📖 Notas importantes
 - Mientras el servidor principal no esté disponible, las funcionalidades de la app estarán limitadas.
 - Si decides trabajar con tu propia base de datos local, asegúrate de seguir los pasos descritos en la sección correspondiente.
 - En la predicción de imágenes, si aportas la planta correspondiente te seguirá dando la probabilidad de que la predicción sea correcta teniendo en cuenta todas las posibilidades, no solo las de esa planta.

## 🤝 Contribuciones y contacto
 - Si deseas contribuir al desarrollo de la app, por favor abre un issue o envía un pull request.
 - Para dudas o sugerencias, contacta con el desarrollador.