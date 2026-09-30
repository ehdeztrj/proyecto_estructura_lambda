# -*- coding: utf-8 -*-
"""
utils.py
--------
Funciones de apoyo compartidas por las tres capas de la Arquitectura Lambda.

Se usan solamente librerías estándar de Python (csv, os, datetime) para
mantener el proyecto simple, portable y sin dependencias externas que
instalar.
"""

import csv
import os


def leer_ventas_csv(ruta_csv):
    """
    Lee un archivo CSV de ventas y devuelve una lista de diccionarios,
    con los tipos numéricos ya convertidos (Quantity, Price per Unit,
    Total Amount, Age -> int/float).

    Cada elemento devuelto tiene esta forma:
        {
            "Transaction ID": 1,
            "Date": "2023-11-24",
            "Customer ID": "CUST001",
            "Gender": "Male",
            "Age": 34,
            "Product Category": "Beauty",
            "Quantity": 3,
            "Price per Unit": 50.0,
            "Total Amount": 150.0,
        }
    """
    if not os.path.exists(ruta_csv):
        raise FileNotFoundError(
            f"No se encontró el archivo '{ruta_csv}'. "
            "Verifica que el CSV esté en la carpeta 'data/'."
        )

    ventas = []
    with open(ruta_csv, newline="", encoding="utf-8-sig") as f:
        lector = csv.DictReader(f)
        for fila in lector:
            venta = {
                "Transaction ID": int(fila["Transaction ID"]),
                "Date": fila["Date"].strip(),
                "Customer ID": fila["Customer ID"].strip(),
                "Gender": fila["Gender"].strip(),
                "Age": int(fila["Age"]),
                "Product Category": fila["Product Category"].strip(),
                "Quantity": int(fila["Quantity"]),
                "Price per Unit": float(fila["Price per Unit"]),
                "Total Amount": float(fila["Total Amount"]),
            }
            ventas.append(venta)
    return ventas


def linea(caracter="-", ancho=70):
    return caracter * ancho


def titulo(texto, caracter="="):
    """Imprime un encabezado visualmente distinguible en la consola."""
    print()
    print(linea(caracter))
    print(texto)
    print(linea(caracter))


def subtitulo(texto):
    print(f"\n>> {texto}")
    print(linea("-", len(texto) + 3))


def formatear_moneda(valor):
    return f"${valor:,.2f}"


def tabla_categoria(diccionario_totales, titulo_col="Categoría"):
    """
    Imprime un diccionario {categoria: total} como una tabla de texto
    simple, ordenada de mayor a menor total, sin usar librerías externas.
    """
    if not diccionario_totales:
        print("  (sin datos)")
        return

    ancho_nombre = max(len(titulo_col), *(len(k) for k in diccionario_totales))
    encabezado = f"  {titulo_col:<{ancho_nombre}}  {'Total':>14}"
    print(encabezado)
    print("  " + "-" * (len(encabezado) - 2))
    for categoria, total in sorted(
        diccionario_totales.items(), key=lambda kv: kv[1], reverse=True
    ):
        print(f"  {categoria:<{ancho_nombre}}  {formatear_moneda(total):>14}")
