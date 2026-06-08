# Plan de redacción — Memoria TFG Foliarium

**Documento maestro:** `memoria/estructura_memoria_tfg.tex`  
**Título oficial (solicitud UPV):** Clasificación de enfermedades en hojas de plantas mediante aprendizaje profundo con imágenes reales y de laboratorio  
**Nombre del sistema:** Foliarium  
**Tutor:** Carlos Carrascosa Casamayor · **Curso:** 2025-2026  
**Última actualización del plan:** junio 2026

---

## Decisiones cerradas

- [x] Título de portada = título de la solicitud de tema (sin cambiar por ahora).
- [x] Nombre del sistema en la memoria: **Foliarium** (sin forzar «FolIArium» en el texto formal).
- [x] Incluir sección de colaboradores / agradecimientos.
- [x] Seguridad: apartado breve en requisitos/implementación, no capítulo entero.
- [x] Guía de usuario: referencia en cuerpo + PDF en apéndice o enlace a `docs/guia_usuario.pdf` / landing del servidor.
- [ ] Consultar al tutor si conviene matizar el título en la memoria (marco de trabajo vs. solo clasificación).

---

## Fase 0 — Configuración y compilación

- [x] Actualizar metadatos (`\title`, `\author`, `\tutor`, `\curs`, resúmenes, keywords) con Foliarium.
- [ ] Compilar PDF desde `memoria/` (`pdflatex` × 2) sin errores.
- [ ] Verificar que `tfgetsinf.cls` y logos/portada están en `memoria/`.
- [ ] Lista de figuras/tablas pendientes (arquitectura, segmentación, resultados…).

---

## Fase 1 — Preliminares

### Metadatos y front matter

- [x] Título oficial en `\title`.
- [ ] Resumen en valenciano/catalán (borrador → revisión).
- [ ] Resumen en castellano (borrador → revisión).
- [ ] Resumen en inglés (borrador → revisión).
- [ ] Palabras clave en tres idiomas (revisar si añadir «Foliarium» o «plataforma»).

### Anexo ODS (documento aparte: `latex/ods_etsinf_anexo.tex`)

- [ ] Rellenar tabla Alto/Medio/Bajo/No (ODS 2, 9, 12, 15 probables).
- [ ] Reflexión 500–1500 palabras.

### Colaboradores y agradecimientos

- [ ] Sección de agradecimientos / colaboradores (Jaime Carlavilla, Marta Rallo, Carlos Carrascosa…).
- [ ] Revisar `src/assets/colaboradores.txt` como fuente.

---

## Fase 2 — Capítulo 1: Introducción

- [ ] § Motivación y contexto del problema.
- [x] § Objetivos generales y específicos (borrador en .tex).
- [x] § Enfoque adoptado (borrador en .tex).
- [ ] § Alcance del trabajo y limitaciones.
- [ ] § Impacto esperado.
- [ ] § Metodología general de trabajo.
- [ ] § Estructura de la memoria.
- [ ] § Colaboradores y participación externa (sustituye la antigua «Duda»).

---

## Fase 3 — Capítulo 2: Marco teórico y estado del arte

- [ ] § Visión por computador aplicada a agricultura.
- [ ] § Aprendizaje profundo y CNN.
- [ ] § Transfer learning y MobileNetV2.
- [ ] § Clasificación multiclase y multitarea.
- [ ] § PlantVillage y datasets de campo.
- [ ] (Opcional) Notación / glosario.
- [ ] **Material fuente:** `main.tex` §Estado del arte — adaptar y actualizar nombre Foliarium.

---

## Fase 4 — Capítulo 3: Análisis del problema y requisitos

- [ ] § Casos de uso del sistema.
- [ ] § Roles: usuario, etiquetador, administrador.
- [ ] § Requisitos funcionales (tabla recomendada).
- [ ] § Requisitos no funcionales.
- [ ] § Criterios de calidad y **seguridad** (JWT, bcrypt, HTTPS, Docker, rate limiting — breve).

---

## Fase 5 — Capítulo 4: Diseño y arquitectura

- [ ] § Visión global del sistema (+ diagrama).
- [ ] § Backend, cliente Flet y scripts auxiliares.
- [ ] § Comunicación app–API (`logicav3`, HTTP/JSON).
- [ ] § Modelo de datos MongoDB.
- [ ] § Despliegue Docker y servidor UPV (`plantas.gti-ia.upv.es`).
- [ ] **Prioridad alta** — escribir con arquitectura actual (no copiar `main.tex` obsoleto).

---

## Fase 6 — Capítulo 5: Datos y preparación experimental

- [ ] § Fuentes de datos y organización del repositorio.
- [ ] § Taxonomía de plantas y enfermedades.
- [ ] § Limpieza, validación e importación de imágenes.
- [x] § Preprocesamientos: color, grayscale y segmentado (redactado en .tex).
- [ ] § División train/validation/test.
- [ ] § Balanceo de clases y control de sesgos.
- [ ] **Material fuente:** `main.tex` pipeline importación — corregir rutas (`scripts/`).

---

## Fase 7 — Capítulo 6: Modelo y metodología de entrenamiento

- [ ] § Arquitectura multitarea MobileNetV2.
- [ ] § Estrategias de fine-tuning.
- [ ] § Pérdida, optimización y métricas.
- [ ] § Gestión de experimentos (`config.yaml`, carpetas `experiments/`).
- [ ] § Scripts de entrenamiento e inferencia.
- [ ] **Material fuente:** `main.tex` §multitarea + `utils/model.py`, `utils/train.py`.

---

## Fase 8 — Capítulo 7: Implementación del sistema

- [ ] § Backend Flask y endpoints principales (agrupados por dominio).
- [ ] § Interfaz Flet (PC, Android, Windows, Linux).
- [ ] § Autenticación y roles.
- [ ] § Herramientas de administración y scripts.
- [ ] § Integración con modelos de predicción.

---

## Fase 9 — Capítulo 8: Experimentación y resultados

> **Dependencia:** exportar métricas y gráficos desde el servidor de producción (`experiments/`).

- [ ] § Experimentos de referencia (PlantVillage).
- [ ] § Comparativa formatos de imagen (color / grayscale / segmented).
- [ ] § Comparativa configuraciones de entrenamiento.
- [ ] § Resultados con imágenes reales (exploratorio; pocos datos).
- [ ] § Análisis de errores y mal clasificados.
- [ ] § Discusión de resultados.

---

## Fase 10 — Capítulo 9: Validación y despliegue

- [ ] § Validación funcional por rol.
- [ ] § Validación Docker y despliegue UPV.
- [ ] § Reproducibilidad de experimentos.
- [ ] (Opcional) Validación por terceros / testers.

---

## Fase 11 — Capítulo 10: Conclusiones y trabajo futuro

- [ ] § Conclusiones.
- [ ] § Limitaciones (marco de trabajo, escasez de datos reales).
- [ ] § Trabajo futuro.

---

## Fase 12 — Cierre documental

- [ ] Bibliografía ampliada (Mohanty, MobileNetV2, PlantDoc, domain shift…).
- [ ] Revisión de estilo y referencias cruzadas.
- [ ] Revisión con tutor (Carlos).
- [ ] PDF final para entrega.

---

## Apéndices (`\APPENDIX`)

- [ ] Ap. A — Instalación y ejecución (resumen de `docs/USUARIO.md` y `docs/DOCKER.md`).
- [ ] Ap. B — Comandos para reproducir experimentos.
- [ ] Ap. C — Fragmentos de código clave.
- [ ] Ap. D — Figuras y tablas complementarias.
- [ ] Ap. E — **Guía de usuario** (incluir PDF o enlace estable a la landing / `docs/guia_usuario.pdf`).

---

## Orden de trabajo recomendado (si no sabes por dónde seguir)

1. Cap. 1 (completar secciones pendientes).
2. Cap. 2 (estado del arte desde `main.tex`).
3. Cap. 4 (arquitectura actual).
4. Cap. 3 (requisitos + seguridad breve).
5. Cap. 5–7 (datos, modelo, implementación).
6. Cap. 8 (cuando tengas resultados del servidor).
7. Cap. 9–10 + apéndices + ODS + revisión tutor.

---

## Notas

- `main.tex` = almacén provisional. No usar como memoria final.
- No editar dos esquemas a la vez: solo `memoria/estructura_memoria_tfg.tex`.
- Problemas técnicos del repo: `docs/problemas_detectados.txt`.

