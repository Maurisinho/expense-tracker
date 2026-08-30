"""Interfaz de línea de comandos del gestor de gastos."""

import argparse
import sys
from datetime import date
from typing import List, Optional

from . import __version__
from .models import CATEGORIAS_SUGERIDAS, Transaction
from .reports import export_csv, format_money, summarize
from .storage import Storage, default_data_file


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="expense-tracker",
        description="Gestor simple de gastos e ingresos personales.",
    )
    parser.add_argument(
        "--data-file",
        default=str(default_data_file()),
        help=f"Ruta del archivo de datos (por defecto: {default_data_file()}).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    sub = parser.add_subparsers(dest="comando", required=True)

    p_add = sub.add_parser("agregar", aliases=["add"], help="Registrar un gasto o ingreso.")
    p_add.add_argument("--tipo", choices=["gasto", "ingreso"], default="gasto",
                       help="Tipo de registro (por defecto: gasto).")
    p_add.add_argument("--descripcion", required=True, help="Descripción del registro.")
    p_add.add_argument("--monto", required=True, type=float, help="Monto en unidades monetarias.")
    p_add.add_argument("--categoria", default="otros",
                       help=f"Categoría (sugeridas: {', '.join(CATEGORIAS_SUGERIDAS)}).")
    p_add.add_argument("--fecha", default=date.today().isoformat(),
                       help="Fecha en formato YYYY-MM-DD (por defecto: hoy).")
    p_add.set_defaults(func=_cmd_agregar)

    p_list = sub.add_parser("listar", aliases=["list"], help="Listar transacciones.")
    p_list.add_argument("--tipo", choices=["gasto", "ingreso"], help="Filtrar por tipo.")
    p_list.add_argument("--categoria", help="Filtrar por categoría.")
    p_list.add_argument("--desde", help="Fecha inicial (YYYY-MM-DD).")
    p_list.add_argument("--hasta", help="Fecha final (YYYY-MM-DD).")
    p_list.set_defaults(func=_cmd_listar)

    p_del = sub.add_parser("eliminar", aliases=["rm"], help="Eliminar una transacción por id.")
    p_del.add_argument("--id", required=True, help="Identificador de la transacción.")
    p_del.set_defaults(func=_cmd_eliminar)

    p_sum = sub.add_parser("resumen", aliases=["summary"], help="Mostrar un resumen de cuentas.")
    p_sum.add_argument("--anio", type=int, default=None, help="Filtrar por año.")
    p_sum.add_argument("--mes", type=int, default=None,
                       help="Filtrar por mes (1-12); requiere --anio.")
    p_sum.set_defaults(func=_cmd_resumen)

    p_exp = sub.add_parser("exportar", aliases=["export"],
                           help="Exportar las transacciones a un archivo CSV.")
    p_exp.add_argument("--archivo", default="transacciones.csv",
                       help="Ruta del archivo CSV de salida.")
    p_exp.set_defaults(func=_cmd_exportar)

    return parser


def _cmd_agregar(args: argparse.Namespace, storage: Storage) -> int:
    try:
        tx = Transaction(
            tipo=args.tipo,
            descripcion=args.descripcion,
            monto=args.monto,
            categoria=args.categoria,
            fecha=args.fecha,
        )
    except ValueError as error:
        _error(str(error))
        return 1

    transactions = storage.load()
    transactions.append(tx)
    storage.save(transactions)

    seccion = "Gasto" if tx.tipo == "gasto" else "Ingreso"
    print(
        f"{seccion} registrado: {tx.descripcion} - {format_money(tx.monto)} "
        f"[{tx.categoria} - {tx.fecha}] (id: {tx.id})"
    )
    return 0


def _cmd_listar(args: argparse.Namespace, storage: Storage) -> int:
    transactions = storage.load()
    filtradas = _filtrar(transactions, args.tipo, args.categoria, args.desde, args.hasta)

    if not filtradas:
        print("Sin transacciones para mostrar.")
        return 0

    print(
        f"{'Fecha':<12}{'Tipo':<9}{'Categoría':<13}{'Descripción':<38}"
        f"{'Monto':>12}  {'Id'}"
    )
    print("-" * 100)
    for tx in filtradas:
        print(
            f"{tx.fecha.isoformat():<12}{tx.tipo:<9}{tx.categoria:<13}"
            f"{tx.descripcion[:37]:<38}{format_money(tx.monto):>12}  {tx.id}"
        )
    print("-" * 100)
    total = sum(tx.monto if tx.tipo == "ingreso" else -tx.monto for tx in filtradas)
    print(f"Total registrado: {format_money(total)}")
    return 0


def _cmd_eliminar(args: argparse.Namespace, storage: Storage) -> int:
    transactions = storage.load()
    restantes = [tx for tx in transactions if tx.id != args.id]
    if len(restantes) == len(transactions):
        _error(f"No se encontró ninguna transacción con id '{args.id}'.")
        return 1
    storage.save(restantes)
    print(f"Transacción '{args.id}' eliminada.")
    return 0


def _cmd_resumen(args: argparse.Namespace, storage: Storage) -> int:
    transactions = storage.load()
    if args.mes is not None:
        if args.anio is None:
            _error("La opción --mes requiere --anio.")
            return 1
        filtradas = [t for t in transactions
                     if t.fecha.year == args.anio and t.fecha.month == args.mes]
        periodo = f"{args.anio}-{args.mes:02d}"
    elif args.anio is not None:
        filtradas = [t for t in transactions if t.fecha.year == args.anio]
        periodo = str(args.anio)
    else:
        filtradas = transactions
        periodo = "todo el período"

    resumen = summarize(filtradas)

    print(f"Resumen ({periodo})")
    print("-" * 40)
    print(f"Ingresos : {format_money(resumen['total_ingresos'])}")
    print(f"Gastos   : {format_money(resumen['total_gastos'])}")
    balance = resumen["balance"]
    estado = "superávit" if balance >= 0 else "déficit"
    print(f"Balance  : {format_money(balance)} ({estado})")
    print("-" * 40)

    por_categoria = resumen["por_categoria"]
    if por_categoria:
        total_gastos = resumen["total_gastos"]
        print("Gastos por categoría:")
        for categoria, monto in por_categoria.items():
            porcentaje = 100.0 * monto / total_gastos if total_gastos else 0.0
            print(f"  {categoria:<13} {format_money(monto):>12}  {porcentaje:.1f}%")
    else:
        print("Sin gastos registrados.")
    return 0


def _cmd_exportar(args: argparse.Namespace, storage: Storage) -> int:
    transactions = storage.load()
    try:
        export_csv(transactions, args.archivo)
    except OSError as error:
        _error(f"No se pudo exportar: {error}")
        return 1
    print(f"Exportadas {len(transactions)} transacciones a '{args.archivo}'.")
    return 0


def _filtrar(transactions: List[Transaction], tipo: Optional[str], categoria: Optional[str],
             desde: Optional[str], hasta: Optional[str]) -> List[Transaction]:
    filtradas: List[Transaction] = []
    for tx in transactions:
        if tipo is not None and tx.tipo != tipo:
            continue
        if categoria is not None and tx.categoria != categoria.lower().strip():
            continue
        if desde is not None and tx.fecha < date.fromisoformat(desde):
            continue
        if hasta is not None and tx.fecha > date.fromisoformat(hasta):
            continue
        filtradas.append(tx)
    filtradas.sort(key=lambda tx: (tx.fecha, tx.id))
    return filtradas


def _error(mensaje: str) -> None:
    print(f"error: {mensaje}", file=sys.stderr)


def main(argv: Optional[List[str]] = None) -> int:
    """Punto de entrada principal de la aplicación."""
    args = _build_parser().parse_args(argv)
    storage = Storage(args.data_file)
    return args.func(args, storage)