# -*- coding: utf-8 -*-
"""
speed_layer.py
---------------
CAPA SPEED (Speed Layer / capa de tiempo real) de la Arquitectura Lambda.

Responsabilidad en esta práctica:
    Simular la llegada de ventas NUEVAS, una por una o en pequeños
    grupos (como si fueran ventas ocurriendo "ahora mismo" en una
    tienda), y mantener actualizados los indicadores recientes SIN
    tener que reprocesar todo el histórico. Esto imita el comportamiento
    de un sistema de streaming real (por ejemplo Kafka + Spark
    Streaming), pero de forma muy simplificada: en lugar de un flujo de
    red, leemos filas de data/incoming_sales.csv y las "inyectamos" de a
    poco en un bucle controlado por el programa.

Concepto clave: la capa Speed solo debe recordar lo que el batch
    TODAVÍA NO ha incluido. Por eso esta clase guarda un "watermark"
    (la misma fecha límite que produce la capa batch: la fecha más
    reciente que el batch ya consolidó) y, si alguna vez cambia (porque
    el batch se reprocesó y ya incorporó esas ventas), descarta de su
    memoria las transacciones que ya quedaron cubiertas por el nuevo
    batch. Así se evita el doble conteo en la capa Serving.

    Se usa la FECHA de la venta (columna "Date") como criterio, no el
    "Transaction ID", porque en este dataset los IDs son solo un
    consecutivo de carga y no reflejan el orden cronológico real de las
    ventas.
"""

from collections import defaultdict
from statistics import mean


class SpeedLayerState:
    """
    Mantiene en memoria el estado "reciente" de ventas que aún no han
    sido incorporadas por la capa batch.
    """

    def __init__(self, watermark_inicial=None):
        # watermark: fecha (string "YYYY-MM-DD") hasta la cual el batch
        # YA procesó. Toda venta con Date <= watermark se considera ya
        # cubierta por el batch y la capa speed no debe contarla.
        self.watermark = watermark_inicial
        self.ventas_recientes = []  # lista de ventas aún no absorbidas por el batch

    def registrar_venta(self, venta):
        """
        Procesa la llegada de UNA venta nueva. Si su fecha ya fue
        cubierta por el batch (Date <= watermark), se ignora para evitar
        doble conteo; si no, se agrega a la memoria reciente.
        """
        if self.watermark is not None and venta["Date"] <= self.watermark:
            return False  # ya estaba en el batch, no se cuenta de nuevo
        self.ventas_recientes.append(venta)
        return True

    def registrar_lote(self, ventas):
        """Procesa una lista de ventas nuevas (pequeño grupo/lote)."""
        agregadas = 0
        for v in ventas:
            if self.registrar_venta(v):
                agregadas += 1
        return agregadas

    def actualizar_watermark(self, nuevo_watermark):
        """
        Se llama cuando la capa batch termina un reprocesamiento y
        "absorbe" ventas que antes estaban solo en la capa speed.
        Descarta de la memoria reciente todo lo que ya quedó cubierto.
        """
        self.watermark = nuevo_watermark
        self.ventas_recientes = [
            v for v in self.ventas_recientes if v["Date"] > self.watermark
        ]

    def calcular_vista_reciente(self):
        """
        Calcula estadísticas de lo que hay actualmente en memoria
        (equivalente en miniatura a lo que hace batch_layer.procesar_batch,
        pero solo sobre las ventas recientes aún no consolidadas).
        """
        ventas = self.ventas_recientes
        if not ventas:
            return {
                "total_transacciones": 0,
                "total_vendido": 0.0,
                "ticket_promedio": 0.0,
                "ventas_por_categoria": {},
                "clientes_unicos": 0,
                "ultimo_transaction_id": None,
            }

        ventas_por_categoria = defaultdict(float)
        clientes = set()
        montos = []
        ultimo_id = None

        for v in ventas:
            montos.append(v["Total Amount"])
            ventas_por_categoria[v["Product Category"]] += v["Total Amount"]
            clientes.add(v["Customer ID"])
            ultimo_id = v["Transaction ID"]

        return {
            "total_transacciones": len(ventas),
            "total_vendido": round(sum(montos), 2),
            "ticket_promedio": round(mean(montos), 2),
            "ventas_por_categoria": dict(ventas_por_categoria),
            "clientes_unicos": len(clientes),
            "ultimo_transaction_id": ultimo_id,
        }
