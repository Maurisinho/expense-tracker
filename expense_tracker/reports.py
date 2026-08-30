"""Generación de resúmenes y exportación de datos."""

import csv
from datetime import date
from typing import Dict, List

from .models import Transaction, redondear_monto


def format_money(monto: float) -> str:
    """Da formato de moneda a una cantidad."""
    return f"${monto:,.2f}"


def summarize(transactions: List[Transaction]) -> Dict[str, object]:
    """Calcula totales de ingresos, gastos y desglose por categoría."""
    gastos = [t for t in transactions if t.tipo == "gasto"]
    ingresos = [t for t in transactions if t.tipo == "ingreso"]
    total_gastos = redondear_monto(sum(t.monto for t in gastos))
    total_ingresos = redondear_monto(sum(t.monto for t in ingresos))

    por_categoria: Dict[str, float] = {}
    for tx in gastos:
        por_categoria[tx.categoria] = redondear_monto(
            por_categoria.get(tx.categoria, 0.0) + tx.monto
        )

    return {
        "total_gastos": total_gastos,
        "total_ingresos": total_ingresos,
        "balance": redondear_monto(total_ingresos - total_gastos),
        "por_categoria": dict(sorted(por_categoria.items(), key=lambda kv: kv[1], reverse=True)),
    }


def monthly_summary(transactions: List[Transaction], year: int, month: int) -> Dict[str, object]:
    """Calcula un resumen para un mes concreto (año y mes)."""
    filtradas = [t for t in transactions if t.fecha.year == year and t.fecha.month == month]
    return summarize(filtradas)


def export_csv(transactions: List[Transaction], path) -> None:
    """Exporta las transacciones a un archivo CSV (codificado UTF-8)."""
    with open(path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["id", "tipo", "descripcion", "monto", "categoria", "fecha"])
        for tx in transactions:
            writer.writerow(
                [tx.id, tx.tipo, tx.descripcion, f"{tx.monto:.2f}", tx.categoria, tx.fecha.isoformat()]
            )