# -*- coding: utf-8 -*-
"""
main.py
--------
Orquestador de la simulación de Arquitectura Lambda para la práctica de
Big Data. Este archivo es el que se ejecuta en clase y muestra, en un
solo flujo, cómo colaboran las tres capas:

    1) BATCH LAYER  -> procesa el histórico de ventas (data/historical_sales.csv)
                        y calcula estadísticas generales.
    2) SPEED LAYER  -> simula la llegada de ventas nuevas (data/incoming_sales.csv)
                        una por una / en pequeños grupos, y mantiene
                        indicadores recientes.
    3) SERVING LAYER -> combina ambas vistas en un solo resultado
                         coherente, sin contar dos veces una misma venta.

Además, el programa simula un CICLO DE REPROCESAMIENTO del batch (como
ocurriría cada noche en un sistema real): el batch "absorbe" las ventas
que ya llegaron por streaming y el speed layer las descarta de su
memoria, demostrando que el total combinado NO cambia (no hay doble
conteo) aunque cambie de dónde provienen los datos.

Uso:
    python main.py                  -> modo por defecto (lotes de 15)
    python main.py --step           -> muestra la llegada venta por venta
    python main.py --lote 10        -> tamaño de lote personalizado
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from batch_layer import ejecutar_batch_layer, procesar_batch
from serving_layer import mostrar_vista_combinada
from speed_layer import SpeedLayerState
from utils import formatear_moneda, leer_ventas_csv, subtitulo, tabla_categoria, titulo

RUTA_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_HISTORICO = os.path.join(RUTA_BASE, "data", "historical_sales.csv")
RUTA_INCOMING = os.path.join(RUTA_BASE, "data", "incoming_sales.csv")
RUTA_BATCH_VIEW = os.path.join(RUTA_BASE, "data", "batch_view.json")


def guardar_batch_view(vista_batch):
    """Guarda la vista batch como JSON (simula la 'batch view' persistida
    que en un sistema real consultaría la capa Serving)."""
    with open(RUTA_BATCH_VIEW, "w", encoding="utf-8") as f:
        json.dump(vista_batch, f, ensure_ascii=False, indent=2)


def mostrar_vista_batch(vista_batch):
    titulo("CAPA BATCH (procesamiento del histórico completo)")
    print(f"  Archivo procesado        : data/historical_sales.csv")
    print(f"  Total de transacciones   : {vista_batch['total_transacciones']}")
    print(f"  Total vendido            : {formatear_moneda(vista_batch['total_vendido'])}")
    print(f"  Ticket promedio          : {formatear_moneda(vista_batch['ticket_promedio'])}")
    print(f"  Clientes únicos          : {vista_batch['clientes_unicos']}")
    print(f"  Categoría más vendida    : {vista_batch['categoria_top']}")
    print(f"  Transaction ID máximo visto (solo informativo): {vista_batch['transaction_id_max']}")
    print(f"  Watermark (fecha máxima cubierta por el batch) : {vista_batch['watermark']}")

    subtitulo("Ventas por categoría (solo histórico)")
    tabla_categoria(vista_batch["ventas_por_categoria"])


def dividir_en_lotes(lista, tamano_lote):
    for i in range(0, len(lista), tamano_lote):
        yield lista[i : i + tamano_lote]


def main():
    parser = argparse.ArgumentParser(
        description="Simulación de Arquitectura Lambda (Batch + Speed + Serving)."
    )
    parser.add_argument(
        "--step",
        action="store_true",
        help="Muestra la llegada de ventas una por una (más lento, más detallado).",
    )
    parser.add_argument(
        "--lote",
        type=int,
        default=15,
        help="Tamaño del lote de ventas nuevas por iteración (por defecto 15).",
    )
    parser.add_argument(
        "--pausa",
        type=float,
        default=0.0,
        help="Segundos de pausa entre cada llegada/lote, para hacerlo más visual en la demo (por defecto 0).",
    )
    args = parser.parse_args()

    titulo("SIMULACIÓN DE ARQUITECTURA LAMBDA - SISTEMA DE VENTAS", "#")
    print(
        "Este programa simula, con datos reales de un CSV de ventas de retail,\n"
        "cómo colaboran las capas Batch, Speed y Serving de una Arquitectura Lambda.\n"
        "Es una demostración académica, no una infraestructura de producción."
    )

    # -----------------------------------------------------------------
    # PASO 1: CAPA BATCH sobre el histórico
    # -----------------------------------------------------------------
    vista_batch = ejecutar_batch_layer(RUTA_HISTORICO)
    mostrar_vista_batch(vista_batch)
    guardar_batch_view(vista_batch)

    # -----------------------------------------------------------------
    # PASO 2: CAPA SPEED - estado inicial (aún sin ventas nuevas)
    # -----------------------------------------------------------------
    speed_state = SpeedLayerState(watermark_inicial=vista_batch["watermark"])
    vista_reciente = speed_state.calcular_vista_reciente()

    titulo("ESTADO INICIAL DE LA CAPA SERVING (antes de que llegue algo nuevo)")
    mostrar_vista_combinada(vista_batch, vista_reciente)

    # -----------------------------------------------------------------
    # PASO 3: CAPA SPEED - simulación de llegada de ventas nuevas
    # -----------------------------------------------------------------
    ventas_nuevas = leer_ventas_csv(RUTA_INCOMING)

    titulo(f"CAPA SPEED: comienzan a llegar {len(ventas_nuevas)} ventas nuevas en tiempo real", "#")
    print(
        "Estas ventas representan diciembre de 2023 / enero de 2024: son las\n"
        "transacciones más recientes, que aún NO forman parte del histórico\n"
        "consolidado por el batch. La capa Speed las procesa a medida que llegan."
    )

    if args.step:
        for i, venta in enumerate(ventas_nuevas, start=1):
            speed_state.registrar_venta(venta)
            vista_reciente = speed_state.calcular_vista_reciente()
            subtitulo(
                f"Llegó venta #{i}/{len(ventas_nuevas)} "
                f"(Transaction ID {venta['Transaction ID']}, {venta['Product Category']}, "
                f"{formatear_moneda(venta['Total Amount'])})"
            )
            mostrar_vista_combinada(vista_batch, vista_reciente)
            if args.pausa:
                time.sleep(args.pausa)
    else:
        for n_lote, lote in enumerate(dividir_en_lotes(ventas_nuevas, args.lote), start=1):
            speed_state.registrar_lote(lote)
            vista_reciente = speed_state.calcular_vista_reciente()
            subtitulo(
                f"Llegó el lote #{n_lote} ({len(lote)} ventas nuevas, "
                f"acumulado speed: {vista_reciente['total_transacciones']})"
            )
            mostrar_vista_combinada(vista_batch, vista_reciente)
            if args.pausa:
                time.sleep(args.pausa)

    # -----------------------------------------------------------------
    # PASO 4: reprocesamiento periódico del BATCH (consolida lo reciente)
    # -----------------------------------------------------------------
    titulo("CICLO DE REPROCESAMIENTO DEL BATCH (por ejemplo, el 'job' de cada noche)", "#")
    print(
        "En un sistema real, la capa batch se ejecuta de forma periódica y en algún\n"
        "momento vuelve a procesar TODO el histórico, incluyendo las ventas que ya\n"
        "habían llegado por streaming. Simulamos ese ciclo aquí: el batch absorbe\n"
        "las ventas que la capa speed ya había mostrado."
    )

    total_antes = mostrar_vista_combinada(vista_batch, speed_state.calcular_vista_reciente())

    ventas_historicas = leer_ventas_csv(RUTA_HISTORICO)
    vista_batch_nueva = procesar_batch(ventas_historicas + ventas_nuevas)
    guardar_batch_view(vista_batch_nueva)

    # El speed layer descarta de su memoria todo lo que el nuevo batch ya cubre
    speed_state.actualizar_watermark(vista_batch_nueva["watermark"])
    vista_reciente_nueva = speed_state.calcular_vista_reciente()

    subtitulo("Nueva vista batch después del reprocesamiento")
    mostrar_vista_batch(vista_batch_nueva)

    titulo("SERVING LAYER DESPUÉS DEL REPROCESAMIENTO (debe dar el MISMO total)")
    total_despues = mostrar_vista_combinada(vista_batch_nueva, vista_reciente_nueva)

    titulo("VERIFICACIÓN: ¿HUBO DOBLE CONTEO?", "#")
    print(f"  Total combinado ANTES del reprocesamiento : {formatear_moneda(total_antes['total_vendido'])}")
    print(f"  Total combinado DESPUÉS del reprocesamiento: {formatear_moneda(total_despues['total_vendido'])}")
    if abs(total_antes["total_vendido"] - total_despues["total_vendido"]) < 0.01:
        print("  -> Los totales COINCIDEN. El reprocesamiento del batch no duplicó ventas.")
    else:
        print("  -> ATENCIÓN: los totales NO coinciden, revisar la lógica de watermark.")

    titulo("FIN DE LA SIMULACIÓN", "#")
    print(
        "Resumen para la exposición:\n"
        "  - BATCH   -> visión completa y exacta, pero desactualizada por diseño.\n"
        "  - SPEED   -> visión parcial pero inmediata de lo más reciente.\n"
        "  - SERVING -> combina ambas y evita doble conteo usando el watermark."
    )


if __name__ == "__main__":
    main()
