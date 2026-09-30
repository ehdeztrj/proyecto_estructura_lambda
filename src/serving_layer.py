# -*- coding: utf-8 -*-
"""
serving_layer.py
-----------------
CAPA SERVING (Serving Layer) de la Arquitectura Lambda.

Responsabilidad en esta práctica:
    Combinar la vista batch (resultado de batch_layer.py, calculada
    sobre el histórico) con la vista reciente (resultado de
    speed_layer.py, calculada sobre lo que llegó en tiempo real) para
    entregar UNA sola vista coherente, como si el usuario final
    consultara un solo panel de ventas sin saber que por debajo hay dos
    procesos distintos trabajando.

Cómo se evita el doble conteo:
    La capa speed ya se encarga de no guardar en memoria ventas con
    fecha (Date) <= watermark del batch (ver speed_layer.py). Por lo
    tanto, al sumar "vista batch + vista reciente" en esta capa, cada
    transacción se cuenta EXACTAMENTE UNA VEZ:
        - Si Date <= watermark  -> ya está en la vista batch.
        - Si Date  > watermark  -> solo puede estar en la vista
          reciente (memoria de la capa speed).
    Esta capa no vuelve a filtrar nada por su cuenta: simplemente confía
    en que las dos vistas que recibe ya son disjuntas, y lo dice
    explícitamente al usuario para que quede claro en la demostración.
"""

from collections import defaultdict

from utils import formatear_moneda, subtitulo, tabla_categoria, titulo


def combinar_vistas(vista_batch, vista_reciente):
    """
    Combina la vista batch y la vista reciente en una sola vista
    "servida" al usuario final.
    """
    total_transacciones = (
        vista_batch["total_transacciones"] + vista_reciente["total_transacciones"]
    )
    total_vendido = round(
        vista_batch["total_vendido"] + vista_reciente["total_vendido"], 2
    )
    ticket_promedio = (
        round(total_vendido / total_transacciones, 2)
        if total_transacciones > 0
        else 0.0
    )

    categorias_combinadas = defaultdict(float)
    for cat, monto in vista_batch["ventas_por_categoria"].items():
        categorias_combinadas[cat] += monto
    for cat, monto in vista_reciente["ventas_por_categoria"].items():
        categorias_combinadas[cat] += monto

    return {
        "total_transacciones": total_transacciones,
        "total_vendido": total_vendido,
        "ticket_promedio": ticket_promedio,
        "ventas_por_categoria": dict(categorias_combinadas),
        "transacciones_desde_batch": vista_batch["total_transacciones"],
        "transacciones_desde_speed": vista_reciente["total_transacciones"],
        "watermark_batch": vista_batch.get("watermark"),
    }


def mostrar_vista_combinada(vista_batch, vista_reciente):
    """
    Imprime en consola la vista combinada (Serving Layer) de forma
    clara para la demostración en vivo, mostrando por separado el
    aporte de cada capa antes de presentar el total.
    """
    combinada = combinar_vistas(vista_batch, vista_reciente)

    titulo("CAPA SERVING (vista combinada para el usuario final)")

    print(
        f"  Transacciones que vienen del BATCH (histórico consolidado): "
        f"{combinada['transacciones_desde_batch']}"
    )
    print(
        f"  Transacciones que vienen del SPEED (tiempo real, aún no consolidadas): "
        f"{combinada['transacciones_desde_speed']}"
    )
    print(
        "  -> No hay doble conteo: el Speed Layer solo guarda ventas con "
        f"fecha posterior al watermark del batch ({combinada['watermark_batch']})."
    )

    subtitulo("Totales combinados (Batch + Speed)")
    print(f"  Total de transacciones : {combinada['total_transacciones']}")
    print(f"  Total vendido           : {formatear_moneda(combinada['total_vendido'])}")
    print(f"  Ticket promedio         : {formatear_moneda(combinada['ticket_promedio'])}")

    subtitulo("Ventas por categoría (combinado)")
    tabla_categoria(combinada["ventas_por_categoria"])

    return combinada
