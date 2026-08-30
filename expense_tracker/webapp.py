"""Servidor web móvil para gestionar los gastos desde cualquier dispositivo."""

import argparse
import os
from datetime import date
from typing import List

from flask import Flask, redirect, render_template, request, url_for

from .models import CATEGORIAS_SUGERIDAS, Transaction
from .reports import format_money, summarize
from .storage import build_storage, default_data_file


def _recientes(transacciones: List[Transaction], limite: int = 100) -> List[Transaction]:
    ordenadas = sorted(transacciones, key=lambda tx: (tx.fecha, tx.id), reverse=True)
    return ordenadas[:limite]


def crear_app(data_file=None) -> Flask:
    """Crea y configura la aplicación Flask."""
    app = Flask(__name__)
    app.config["DATA_FILE"] = str(data_file or default_data_file())

    @app.template_filter("money")
    def money(monto):
        return format_money(monto)

    @app.get("/")
    def inicio():
        storage = build_storage(app.config["DATA_FILE"])
        transacciones = _recientes(storage.load())
        resumen_total = summarize(transacciones)
        hoy = date.today()
        del_mes = [tx for tx in transacciones
                   if (tx.fecha.year, tx.fecha.month) == (hoy.year, hoy.month)]
        resumen_mes = summarize(del_mes)
        return render_template(
            "index.html",
            transacciones=transacciones,
            resumen=resumen_total,
            resumen_mes=resumen_mes,
            categorias=CATEGORIAS_SUGERIDAS,
            mes=f"{hoy.year}-{hoy.month:02d}",
            hoy=hoy.isoformat(),
            mensaje=request.args.get("mensaje"),
            correcto=request.args.get("correcto") == "1",
        )

    @app.post("/agregar")
    def agregar():
        try:
            tx = Transaction(
                tipo=request.form.get("tipo", "gasto"),
                descripcion=request.form.get("descripcion", ""),
                monto=request.form.get("monto", "0"),
                categoria=request.form.get("categoria", "otros"),
                fecha=request.form.get("fecha") or date.today().isoformat(),
            )
        except ValueError as error:
            return redirect(url_for("inicio", mensaje=str(error)))

        storage = build_storage(app.config["DATA_FILE"])
        transacciones = storage.load()
        transacciones.append(tx)
        storage.save(transacciones)
        return redirect(url_for("inicio", correcto=1))

    @app.post("/eliminar/<tx_id>")
    def eliminar(tx_id):
        storage = build_storage(app.config["DATA_FILE"])
        transacciones = storage.load()
        restantes = [tx for tx in transacciones if tx.id != tx_id]
        if len(restantes) == len(transacciones):
            return redirect(url_for("inicio", mensaje="No se encontró la transacción."))
        storage.save(restantes)
        return redirect(url_for("inicio", correcto=1))

    @app.get("/salud")
    def salud():
        return {"ok": True}

    return app


app = crear_app()


def main() -> None:
    """Punto de entrada del servidor web."""
    parser = argparse.ArgumentParser(description="Servidor web del gestor de gastos.")
    parser.add_argument("--data-file", default=str(default_data_file()),
                        help="Archivo Excel o JSON con los datos.")
    parser.add_argument("--host", default="127.0.0.1",
                        help="Host de escucha (por defecto: 127.0.0.1).")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "5000")),
                        help="Puerto de escucha (por defecto: 5000).")
    parser.add_argument("--debug", action="store_true", help="Modo de depuración.")
    args = parser.parse_args()
    servidor = crear_app(args.data_file)
    servidor.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()