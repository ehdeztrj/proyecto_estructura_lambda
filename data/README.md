# Origen y Estructura de los Datos

## 1. Fuente
* **Dataset:** *Retail Sales Dataset* (Kaggle).
* **Volumen:** 1,000 registros transaccionales (periodo 2023–2024).
* **Atributos:** Transaction ID, Date, Customer ID, Gender, Age, Product Category, Quantity, Price per Unit, Total Amount.

## 2. Partición para Arquitectura Lambda
* **historical_sales.csv (907 registros):** Ventas del 01/01/2023 al 30/11/2023. Almacenamiento inmutable para Batch Layer.
* **incoming_sales.csv (93 registros):** Ventas del 01/12/2023 al 01/01/2024. Flujo en tiempo real para Speed Layer.
* **retail_sales_dataset.csv (1,000 registros):** Archivo fuente completo consolidado.
* **batch_view.json:** Vista precalculada persistida de la capa Batch.
