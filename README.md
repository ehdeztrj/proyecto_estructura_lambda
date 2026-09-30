# Simulación de Arquitectura Lambda en Python (Sistema de Ventas Retail)

* **Materia:** Manejo Masivo de Datos / Big Data
* **Unidad:** 1. Fundamentos de Big Data
* **Equipo:** 5

---

## 1. Descripción del Proyecto
Este proyecto demuestra de forma práctica y simplificada el funcionamiento, colaboración e integración de las tres capas de una **Arquitectura Lambda** (Batch Layer, Speed Layer y Serving Layer) sobre un sistema de transacciones comerciales (*Retail Sales Dataset*).

El sistema simula el flujo dual de procesamiento: cálculo inmutable sobre datos históricos consolidados, captura en tiempo real de transacciones entrantes con baja latencia, y resolución de consultas unificadas en la capa de servicio sin incurrir en doble conteo mediante control temporal de marca de agua (*watermark*).

---

## 2. Arquitectura del Sistema

```text
                        ┌────────────────────────────────────────┐
                        │      Ingesta Continua de Datos         │
                        └───────────────────┬────────────────────┘
                                            │
                     ┌──────────────────────┴──────────────────────┐
                     ▼                                             ▼
          ┌─────────────────────┐                       ┌─────────────────────┐
          │     BATCH LAYER     │                       │     SPEED LAYER     │
          │  (Datos Históricos) │                       │ (Eventos Recientes) │
          └──────────┬──────────┘                       └──────────┬──────────┘
                     │ Precalcula                                  │ Vistas en
                     │ Batch Views                                 │ memoria
                     ▼                                             ▼
          ┌───────────────────────────────────────────────────────────────────┐
          │                           SERVING LAYER                           │
          │        (Fusión disjunta de vistas Batch + Speed en tiempo real)   │
          └─────────────────────────────────┬─────────────────────────────────┘
                                            │
                                            ▼
                                    Consulta Unificada
```

* **Batch Layer (`src/batch_layer.py`):** Procesa el histórico inmutable (`data/historical_sales.csv`), precalcula la vista maestra (`data/batch_view.json`) y determina el *watermark* temporal.
* **Speed Layer (`src/speed_layer.py`):** Procesa eventos entrantes (`data/incoming_sales.csv`) de forma incremental y mantiene un buffer en memoria de transacciones recientes no cubiertas por el batch.
* **Serving Layer (`src/serving_layer.py`):** Indexa y fusiona ambas vistas para responder consultas analíticas con baja latencia y exactitud matemática.

---

## 3. Requisitos del Entorno
* **Python 3.8** o superior.
* Librería estándar únicamente (`csv`, `json`, `os`, `sys`, `time`, `collections`, `statistics`, `argparse`). Sin dependencias externas vía pip.

---

## 4. Instrucciones de Instalación y Ejecución

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/TU_USUARIO/proyecto-big-data.git
   cd proyecto-big-data
   ```

2. **Ejecución estándar:**
   ```bash
   python src/main.py
   ```

3. **Ejecución interactiva para demostración en vivo:**
   ```bash
   python src/main.py --step --pausa 0.2
   ```

---

## 5. Verificación de Consistencia
* **Watermark:** La capa Speed valida que `Date > watermark`.
* **Reprocesamiento:** Al consolidar el batch nocturno, la capa Speed purga su memoria y la Serving Layer confirma que el total vendido ($456,000.00) se mantiene idéntico sin duplicaciones.
