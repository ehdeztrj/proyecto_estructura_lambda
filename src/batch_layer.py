# -*- coding: utf-8 -*-
"""
batch_layer.py
---------------
CAPA BATCH (Batch Layer) de la Arquitectura Lambda.

Responsabilidad en esta práctica:
    Procesar el conjunto de ventas HISTÓRICAS (data/historical_sales.csv)
    y calcular estadísticas generales y confiables sobre todo ese
    histórico. Esta capa representa el procesamiento "pesado" y periódico
    que en un sistema real tardaría minutos u horas (aquí se simula en
    segundos porque el dataset es pequeño), pero que produce una "vista
    batch" (batch view) exacta y completa.

Concepto clave: la MARCA DE AGUA (watermark)
    Cada vez que la capa batch procesa un conjunto de datos, registra
    hasta qué FECHA quedó cubierto ese cálculo (la fecha más reciente
    incluida). Esa marca de agua ("watermark") es la que usará la capa
    Speed para saber si una venta que llega ya estaba contemplada por el
    batch o si todavía es "nueva". Usamos la fecha y no el Transaction ID
    porque, en este dataset (como en la vida real), los identificadores
    de transacción NO están ordenados cronológicamente: una venta con un
    ID numéricamente menor puede tener una fecha más reciente que otra
    con un ID mayor. La fecha es el dato correcto para decidir qué ya
    fue consolidado y qué no.
"""

from collections import defaultdict
from statistics import mean

from utils import leer_ventas_csv


def procesar_batch(ventas):
    """
    Recibe una lista de ventas (ya leídas con utils.leer_ventas_csv) y
    calcula las estadísticas generales del histórico.

    Devuelve un diccionario ("vista batch") con:
      - total_transacciones
      - total_vendido
      - ticket_promedio
      - clientes_unicos
      - ventas_por_categoria
      - ventas_por_genero
      - unidades_por_categoria
      - categoria_top
      - watermark: la fecha más reciente incluida en este cálculo
                   (marca hasta dónde llegó el batch en el tiempo)
      - transaction_id_max: el Transaction ID más alto visto (solo
                   informativo, no se usa para decidir qué es "nuevo")
    """
    if not ventas:
        return {
            "total_transacciones": 0,
            "total_vendido": 0.0,
            "ticket_promedio": 0.0,
            "clientes_unicos": 0,
            "ventas_por_categoria": {},
            "ventas_por_genero": {},
            "unidades_por_categoria": {},
            "categoria_top": None,
            "watermark": None,
            "transaction_id_max": 0,
        }

    ventas_por_categoria = defaultdict(float)
    unidades_por_categoria = defaultdict(int)
    ventas_por_genero = defaultdict(float)
    clientes = set()
    montos = []

    transaction_id_max = 0
    fecha_max = ventas[0]["Date"]

    for v in ventas:
        montos.append(v["Total Amount"])
        ventas_por_categoria[v["Product Category"]] += v["Total Amount"]
        unidades_por_categoria[v["Product Category"]] += v["Quantity"]
        ventas_por_genero[v["Gender"]] += v["Total Amount"]
        clientes.add(v["Customer ID"])

        if v["Transaction ID"] > transaction_id_max:
            transaction_id_max = v["Transaction ID"]
        if v["Date"] > fecha_max:
            fecha_max = v["Date"]

    categoria_top = max(ventas_por_categoria.items(), key=lambda kv: kv[1])[0]

    return {
        "total_transacciones": len(ventas),
        "total_vendido": round(sum(montos), 2),
        "ticket_promedio": round(mean(montos), 2),
        "clientes_unicos": len(clientes),
        "ventas_por_categoria": dict(ventas_por_categoria),
        "ventas_por_genero": dict(ventas_por_genero),
        "unidades_por_categoria": dict(unidades_por_categoria),
        "categoria_top": categoria_top,
        "watermark": fecha_max,
        "transaction_id_max": transaction_id_max,
    }


def ejecutar_batch_layer(ruta_csv_historico, ventas_adicionales=None):
    """
    Punto de entrada de la capa batch.

    - ruta_csv_historico: ruta al CSV histórico (data/historical_sales.csv)
    - ventas_adicionales: lista opcional de ventas extra (formato de
      utils.leer_ventas_csv) que ya llegaron por la capa Speed y que en
      este ciclo de batch se van a "consolidar" dentro del histórico.
      Esto simula el reprocesamiento periódico típico de la capa batch
      (por ejemplo, un job que corre cada noche e incorpora todo lo que
      llegó por streaming durante el día).

    Devuelve la vista batch (diccionario) calculada con utils.
    """
    ventas = leer_ventas_csv(ruta_csv_historico)

    if ventas_adicionales:
        ventas = ventas + ventas_adicionales

    return procesar_batch(ventas)
