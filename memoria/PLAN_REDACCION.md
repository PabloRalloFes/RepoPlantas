# Plan de redacción — Memoria TFG Foliarium

**Documento maestro:** `memoria/estructura_memoria_tfg.tex`  
**Título oficial (solicitud UPV):** Clasificación de enfermedades en hojas de plantas mediante aprendizaje profundo con imágenes reales y de laboratorio  
**Nombre del sistema:** Foliarium  
**Tutor:** Carlos Carrascosa Casamayor · **Curso:** 2025-2026  
**Última actualización del plan:** junio 2026

### Mapa de capítulos (orden vigente)


| Cap. | Título                                        |
| ---- | --------------------------------------------- |
| 1    | Introducción                                  |
| 2    | Marco teórico y estado del arte               |
| 3    | Análisis del problema                         |
| 4    | Diseño y arquitectura de la solución          |
| 5    | **Implementación de Foliarium**               |
| 6    | **Datos y pipeline de preparación**           |
| 7    | Modelo y metodología de entrenamiento         |
| 8    | Experimentación y resultados                  |
| 9    | Validación y despliegue *(Docker y UPV aquí)* |
| 10   | Conclusiones y trabajo futuro                 |


---

## Decisiones cerradas

- [x] Título de portada = título de la solicitud de tema (sin cambiar por ahora).
- [x] Nombre del sistema en la memoria: **Foliarium** (sin forzar «FolIArium» en el texto formal).
- [x] Incluir sección de colaboradores / agradecimientos.
- [x] Seguridad: § dedicado en cap. 3 (análisis de seguridad); RF/RNF en apéndice.
- [x] Guía de usuario: referencia en cuerpo + PDF en apéndice o enlace a `docs/guia_usuario.pdf` / landing del servidor.
- [ ] Consultar al tutor si conviene matizar el título en la memoria (marco de trabajo vs. solo clasificación).

---

## Fase 0 — Configuración y compilación

- [x] Actualizar metadatos (`\title`, `\author`, `\tutor`, `\curs`, resúmenes, keywords) con Foliarium.
- [x] Compilar PDF desde `memoria/` (`pdflatex` × 2) sin errores.
- [x] Apéndices: no usar `\backmatter` antes de la bibliografía (rompe numeración A, B, C).
- [x] Verificar que `tfgetsinf.cls` y logos/portada están en `memoria/`.
- [ ] Lista de figuras/tablas pendientes (arquitectura, segmentación, resultados…).

---

## Fase 1 — Preliminares

### Metadatos y front matter

- [x] Título oficial en `\title`.
- [x] Resumen en valenciano/catalán.
- [x] Resumen en castellano.
- [x] Resumen en inglés.
- [x] Palabras clave en tres idiomas (revisar si añadir «Foliarium» o «plataforma»).

### Anexo ODS (documento aparte: `latex/ods_etsinf_anexo.tex`)

- [ ] Rellenar tabla Alto/Medio/Bajo/No (ODS 2, 9, 12, 15 probables).
- [ ] Reflexión 500–1500 palabras.

---

## Fase 2 — Capítulo 1: Introducción

- [x] § Motivación y contexto (COSASS, Cátedra Planeta, datasets fragmentados, plataforma multi-fuente).
- [ ] Completar párrafo inicial tras hablar con Jaime Carlavilla (nota en .tex).
- [ ] § Objetivos generales y específicos (matizados: CNN, integración multi-dataset; nota MobileNetV2 pendiente tutor).
- [x] § Enfoque adoptado.
- [x] § Alcance del trabajo y limitaciones.
- [x] § Impacto esperado.
- [x] § Metodología general de trabajo.
- [x] § Estructura de la memoria.
- [ ] § Colaboradores y agradecimientos (pendiente redacción).

---

## Fase 3 — Capítulo 2: Marco teórico y estado del arte

- [x] § Introducción al capítulo.
- [x] § Fundamentos de aprendizaje profundo (condensado: Mohanty, transfer learning, arquitecturas, multitarea).
- [x] § Estado del arte: conjuntos de datos y modelos (tabla comparativa + PlantDoc, PlantCLEF, IP102, Kaggle).
- [x] § Estado del arte: sistemas y aplicaciones (Plantix, Nuru, cliente-servidor).
- [x] § Crítica al estado del arte (fragmentación, no unificación).
- [x] § Propuesta y posicionamiento de Foliarium (plataforma, no modelo único).
- [x] Bibliografía ampliada (Mohanty, PlantDoc, PlantCLEF, IP102, Ferentinos, Sladojevic, Plant Pathology).
- [ ] Revisión con tutor: redacción final y extensión si hace falta.

**Coherencia Cap. 1 ↔ 2 ↔ 6:** premisa datasets matizada; Cap. 6 incluye normalización PlantDoc.

**Decisión pendiente:** MobileNetV2 vs otras arquitecturas (notas en Cap. 1, 7 y 10; inferencia en servidor).

---

## Fase 4 — Capítulo 3: Análisis del problema

- [x] § Introducción al capítulo (puente desde estado del arte).
- [x] § Formulación del problema, actores y oportunidades.
- [x] § Identificación y análisis de alternativas (A/B/C) con criterios de selección.
- [x] § Solución propuesta (Foliarium, fases, validación).
- [x] § Análisis de seguridad (contenido previo conservado).
- [x] § Análisis de eficiencia y coste computacional (servidor vs. móvil).
- [x] § Marco legal y ético (RGPD, PI, licencias datos, ética diagnóstico).
- [x] § Análisis de riesgos (tabla).
- [x] § Plan de trabajo y presupuesto orientativo (retrospectivo).
- [ ] RF/RNF movidos a apéndice «Requisitos del sistema (referencia)». (Necesario?)
- [ ] Eliminar Análisis energético o de eficiencia algorítmica?
- [ ] Revisión con Carlos: horas del plan de trabajo y matiz RGPD institucional.

---

## Fase 5 — Capítulo 4: Diseño y arquitectura (Por revisar a partir de aquí)

- [x] § Visión global del sistema (falta diagrama; añadir figura más adelante).
- [x] § Backend, cliente Flet y scripts auxiliares.
- [x] § Comunicación app–API (`logicav3`, HTTP/JSON, JWT).
- [x] § Modelo de datos MongoDB (colecciones y esquema).
- [x] § Elección de MongoDB, alternativas descartadas y persistencia híbrida (borrador añadido).
- [ ] **Revisar al repasar cap. 4:** completar/validar § MongoDB (diagrama ER opcional, índices si aplica).
- [x] § Consideraciones de despliegue (breve; detalle en Cap. 9).
- [ ] Revisión con tutor y posible figura de arquitectura.

---

## Fase 6 — Capítulo 5: Implementación de Foliarium

- [x] § Backend Flask y endpoints principales (agrupados por dominio).
- [x] § Interfaz Flet (PC, Android, Windows, Linux).
- [x] § Autenticación y roles.
- [x] § Herramientas de administración y scripts.
- [x] § Integración con modelos de predicción.
- [ ] Revisión manual: capturas de pantalla por rol; detallar flujos concretos si el tutor lo pide.

---

## Fase 7 — Capítulo 6: Datos y pipeline de preparación

- [x] § Fuentes de datos (PlantVillage, PlantDoc, App, otras).
- [x] § Normalización de fuentes externas (mapeo clases, pipeline).
- [x] § Taxonomía de plantas y enfermedades.
- [x] § Limpieza, validación e importación de imágenes.
- [x] § Preprocesamientos: color, grayscale y segmentado (redactado previamente).
- [x] § División train/validation/test.
- [x] § Balanceo de clases y control de sesgos.
- [ ] **Importación PlantDoc en servidor:** ejecutar `scripts/prepare_plantdoc_import.py` + subida (véase `docs/importacion_plantdoc.md`).
- [ ] Añadir proporciones concretas de split desde `experiments/BASE/config.yaml` del servidor.
- [ ] **Material fuente:** revisar rutas y fuentes reales concretas (vid, etc.) con datos del servidor.

---

## Fase 8 — Capítulo 7: Modelo y metodología de entrenamiento

- [x] § Arquitectura multitarea CNN / MobileNetV2 (borrador + nota decisión arquitectura).
- [ ] § Estrategias de fine-tuning.
- [ ] § Pérdida, optimización y métricas.
- [ ] § Gestión de experimentos (`config.yaml`, carpetas `experiments/`).
- [ ] § Scripts de entrenamiento e inferencia.
- [ ] **Material fuente:** `main.tex` §multitarea + `utils/model.py`, `utils/train.py`.

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

- [x] § Introducción cap. 9 vs cap. 8 (plataforma vs modelo).
- [x] § Validación funcional (borrador: pruebas autor + amigos; pendiente matriz formal).
- [x] § Despliegue Docker Compose (mongo, api, initdb, Dockerfile, Gunicorn, healthchecks).
- [x] § Despliegue producción UPV (landing, guía PDF, descargas clientes).
- [x] § Reproducibilidad (infra en cap. 9; experimentos detallados en cap. 8).
- [x] § Pruebas con usuarios externos (borrador informal).
- [ ] Completar placeholders: matriz pruebas por rol, encuesta, capturas, detalle TLS/proxy.
- [ ] **Añadir enlace a Google Forms** (encuesta de usabilidad) en la landing `plantas.gti-ia.upv.es` (`templates/landing.html`). ✅ Hecho — pendiente desplegar en servidor.
- [ ] Tras import PlantDoc + reentrenamiento: no mezclar métricas aquí (van a cap. 8).

---

## Fase 11 — Capítulo 10: Conclusiones y trabajo futuro

- [ ] § Conclusiones.
- [ ] § Limitaciones (marco de trabajo, heterogeneidad de fuentes).
- [x] § Trabajo futuro (nuevas fuentes + arquitecturas alternativas; borrador).

---

## Fase 12 — Cierre documental

- [x] Bibliografía ampliada (PlantDoc, PlantCLEF, IP102, Ferentinos, Sladojevic, Plant Pathology).
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
3. Cap. 4 (diseño / arquitectura).
4. Cap. 5 (implementación de Foliarium).
5. Cap. 3 (análisis del problema, alternativas, legal/ético) — alineado con guía ETSINF.
6. Cap. 6–7 (datos y modelo).
7. Cap. 8 (cuando tengas resultados del servidor).
8. Cap. 9–10 + apéndices + ODS + revisión tutor.

---

## Secciones a considerar

- Autenticidad de la Información
- Narrativa y Visualización
- Convenciones
- ~~Reorganizar estado del arte~~ (hecho en Cap. 2)
- Decidir con tutor: MobileNetV2 vs EfficientNet/ResNet (inferencia en servidor)
- Ejecutar importación PlantDoc en servidor antes de Cap. 8

## Notas

- `main.tex` = almacén provisional. No usar como memoria final.
- No editar dos esquemas a la vez: solo `memoria/estructura_memoria_tfg.tex`.
- Problemas técnicos del repo: `docs/problemas_detectados.txt`.

