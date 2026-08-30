"""Pruebas del gestor de gastos e ingresos."""

import csv
import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from expense_tracker.cli import main
from expense_tracker.models import Transaction
from expense_tracker.reports import export_csv, summarize
from expense_tracker.storage import Storage, build_storage
from expense_tracker.webapp import crear_app


class TransactionTests(unittest.TestCase):

    def test_crea_gasto_valido(self):
        tx = Transaction("gasto", "Café", 3.5, "comida", "2026-08-01")
        self.assertEqual(tx.tipo, "gasto")
        self.assertEqual(tx.monto, 3.5)
        self.assertEqual(tx.fecha, date(2026, 8, 1))

    def test_tipo_invalido_lanza_error(self):
        with self.assertRaises(ValueError):
            Transaction("invalido", "Compra", 10)

    def test_monto_negativo_lanza_error(self):
        with self.assertRaises(ValueError):
            Transaction("gasto", "Compra", -1)

    def test_descripcion_vacia_lanza_error(self):
        with self.assertRaises(ValueError):
            Transaction("gasto", "   ", 10)

    def test_categoria_por_defecto(self):
        tx = Transaction("gasto", "Pago", 10, "")
        self.assertEqual(tx.categoria, "otros")

    def test_redondea_monto(self):
        tx = Transaction("ingreso", "Nómina", 1000.005)
        self.assertEqual(tx.monto, 1000.01)

    def test_to_dict_y_from_dict(self):
        tx = Transaction("gasto", "Pan", 2.5, "comida", "2026-08-02")
        restaurada = Transaction.from_dict(tx.to_dict())
        self.assertEqual(restaurada, tx)
        self.assertEqual(restaurada.fecha, date(2026, 8, 2))


class StorageTests(unittest.TestCase):

    def test_carga_vacio_cuando_no_existe(self):
        with tempfile.TemporaryDirectory() as tmp:
            storage = Storage(Path(tmp) / "no_existe.json")
            self.assertEqual(storage.load(), [])

    def test_guardar_y_cargar_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            archivo = Path(tmp) / "datos.json"
            storage = Storage(archivo)
            tx = Transaction("gasto", "Cine", 12, "ocio", "2026-08-03")
            storage.save([tx])
            cargadas = storage.load()
            self.assertEqual(len(cargadas), 1)
            self.assertEqual(cargadas[0], tx)

    def test_build_storage_elige_segun_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsInstance(build_storage(Path(tmp) / "d.json"), Storage)
            from expense_tracker.excel_store import ExcelStorage
            self.assertIsInstance(build_storage(Path(tmp) / "d.xlsx"), ExcelStorage)


class ExcelStorageTests(unittest.TestCase):

    def test_roundtrip_excel(self):
        with tempfile.TemporaryDirectory() as tmp:
            archivo = Path(tmp) / "datos.xlsx"
            storage = build_storage(archivo)
            tx = Transaction("gasto", "Café", 4.5, "comida", "2026-08-10")
            storage.save([tx])
            cargadas = storage.load()
            self.assertEqual(len(cargadas), 1)
            self.assertEqual(cargadas[0], tx)

    def test_carga_vacio_cuando_no_existe(self):
        with tempfile.TemporaryDirectory() as tmp:
            storage = build_storage(Path(tmp) / "sin_datos.xlsx")
            self.assertEqual(storage.load(), [])

    def test_carga_acepta_fechas_editadas_por_excel(self):
        with tempfile.TemporaryDirectory() as tmp:
            archivo = Path(tmp) / "datos.xlsx"
            build_storage(archivo).save([])
            from openpyxl import load_workbook
            wb = load_workbook(archivo)
            wb.active.append(["id123", "gasto", "Prueba", 9.5, "otros", "2026-08-15"])
            wb.save(archivo)
            cargadas = build_storage(archivo).load()
            self.assertEqual(len(cargadas), 1)
            self.assertEqual(cargadas[0].descripcion, "Prueba")


class ReportTests(unittest.TestCase):

    def test_resumen_totales(self):
        tx = [
            Transaction("gasto", "Café", 5, "comida", "2026-08-01"),
            Transaction("gasto", "Bus", 2, "transporte", "2026-08-02"),
            Transaction("gasto", "Comida", 15, "comida", "2026-08-03"),
            Transaction("ingreso", "Nómina", 1000, "", "2026-08-01"),
        ]
        resumen = summarize(tx)
        self.assertEqual(resumen["total_gastos"], 22.0)
        self.assertEqual(resumen["total_ingresos"], 1000.0)
        self.assertEqual(resumen["balance"], 978.0)
        self.assertEqual(resumen["por_categoria"]["comida"], 20.0)
        self.assertEqual(resumen["por_categoria"]["transporte"], 2.0)

    def test_resumen_vacio(self):
        resumen = summarize([])
        self.assertEqual(resumen["total_gastos"], 0)
        self.assertEqual(resumen["total_ingresos"], 0)
        self.assertEqual(resumen["por_categoria"], {})

    def test_exportar_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            archivo = Path(tmp) / "salida.csv"
            tx = [Transaction("gasto", "Libro", 20, "ocio", "2026-08-05")]
            export_csv(tx, archivo)
            with open(archivo, newline="", encoding="utf-8-sig") as f:
                filas = list(csv.reader(f))
            self.assertEqual(filas[0], ["id", "tipo", "descripcion", "monto", "categoria", "fecha"])
            self.assertEqual(filas[1][1:], ["gasto", "Libro", "20.00", "ocio", "2026-08-05"])


class CliTests(unittest.TestCase):

    def setUp(self):
        self._tempdir = tempfile.TemporaryDirectory()
        self.data_file = str(Path(self._tempdir.name) / "datos.json")

    def tearDown(self):
        self._tempdir.cleanup()

    def ejecutar(self, *args, data_file=None):
        archivo = data_file or self.data_file
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            codigo = main(["--data-file", archivo, *args])
        return codigo, buffer.getvalue()

    def test_agregar_y_listar(self):
        codigo, _ = self.ejecutar("agregar", "--descripcion", "Café", "--monto", "3.5",
                                  "--categoria", "comida", "--fecha", "2026-08-10")
        self.assertEqual(codigo, 0)
        codigo, salida = self.ejecutar("listar")
        self.assertEqual(codigo, 0)
        self.assertIn("Café", salida)
        self.assertIn("$3.50", salida)

    def test_agregar_ingreso(self):
        codigo, salida = self.ejecutar("agregar", "--tipo", "ingreso", "--descripcion",
                                       "Nómina", "--monto", "1500")
        self.assertEqual(codigo, 0)
        self.assertIn("Ingreso registrado", salida)

    def test_monto_invalido_rechazado(self):
        codigo, _ = self.ejecutar("agregar", "--descripcion", "X", "--monto", "-5")
        self.assertEqual(codigo, 1)

    def test_eliminar(self):
        self.ejecutar("agregar", "--descripcion", "Sueldo", "--monto", "10")
        _, salida = self.ejecutar("listar")
        linea = next(l for l in salida.splitlines() if "Sueldo" in l)
        id_visible = linea.strip().split()[-1]
        codigo, _ = self.ejecutar("eliminar", "--id", id_visible)
        self.assertEqual(codigo, 0)
        codigo, salida = self.ejecutar("listar")
        self.assertIn("Sin transacciones", salida)

    def test_eliminar_inexistente(self):
        codigo, _ = self.ejecutar("eliminar", "--id", "no-existe")
        self.assertEqual(codigo, 1)

    def test_resumen_filtra_por_mes(self):
        self.ejecutar("agregar", "--descripcion", "Gas", "--monto", "40",
                      "--categoria", "vivienda", "--fecha", "2026-08-15")
        self.ejecutar("agregar", "--descripcion", "Cena", "--monto", "30",
                      "--fecha", "2026-07-15")
        codigo, salida = self.ejecutar("resumen", "--anio", "2026", "--mes", "8")
        self.assertEqual(codigo, 0)
        self.assertIn("$40.00", salida)
        self.assertNotIn("$30.00", salida)

    def test_resumen_mes_sin_anio_error(self):
        codigo, _ = self.ejecutar("resumen", "--mes", "8")
        self.assertEqual(codigo, 1)

    def test_exportar(self):
        self.ejecutar("agregar", "--descripcion", "Camiseta", "--monto", "9.99")
        salida_csv = str(Path(self._tempdir.name) / "salida.csv")
        codigo, salida = self.ejecutar("exportar", "--archivo", salida_csv)
        self.assertEqual(codigo, 0)
        self.assertTrue(os.path.exists(salida_csv))

    def test_cli_escribe_en_excel(self):
        archivo = str(Path(self._tempdir.name) / "datos.xlsx")
        codigo, _ = self.ejecutar("agregar", "--descripcion", "Cena", "--monto", "25",
                                  "--categoria", "comida", data_file=archivo)
        self.assertEqual(codigo, 0)
        self.assertTrue(os.path.exists(archivo))
        _, salida = self.ejecutar("listar", data_file=archivo)
        self.assertIn("Cena", salida)

    def test_mensaje_guardado_en_excel(self):
        archivo = str(Path(self._tempdir.name) / "datos.xlsx")
        self.ejecutar("agregar", "--descripcion", "Bus", "--monto", "2", data_file=archivo)
        from expense_tracker.excel_store import ExcelStorage
        excel = ExcelStorage(archivo)
        cargadas = excel.load()
        self.assertEqual(len(cargadas), 1)
        self.assertEqual(cargadas[0].descripcion, "Bus")


class WebAppTests(unittest.TestCase):

    def setUp(self):
        self._tempdir = tempfile.TemporaryDirectory()
        self.data_file = str(Path(self._tempdir.name) / "web.xlsx")
        app = crear_app(self.data_file)
        app.testing = True
        self.client = app.test_client()

    def tearDown(self):
        self._tempdir.cleanup()

    def test_pagina_inicial(self):
        respuesta = self.client.get("/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Mis Gastos", respuesta.get_data(as_text=True))

    def test_agregar_desde_la_web(self):
        respuesta = self.client.post("/agregar", data={
            "tipo": "gasto",
            "descripcion": "Café en la web",
            "monto": "3.5",
            "categoria": "comida",
            "fecha": "2026-08-10",
        })
        self.assertEqual(respuesta.status_code, 302)
        pagina = self.client.get("/").get_data(as_text=True)
        self.assertIn("Café en la web", pagina)

    def test_monto_invalido_desde_la_web(self):
        respuesta = self.client.post("/agregar", data={
            "monto": "-5",
            "descripcion": "Mal",
        }, follow_redirects=True)
        self.assertEqual(respuesta.status_code, 200)
        pagina = respuesta.get_data(as_text=True)
        self.assertIn("El monto no puede ser negativo", pagina)

    def test_eliminar_desde_la_web(self):
        self.client.post("/agregar", data={
            "descripcion": "A eliminar",
            "monto": "10",
        })
        from expense_tracker.excel_store import ExcelStorage
        tx = ExcelStorage(self.data_file).load()[0]
        respuesta = self.client.post("/eliminar/{}".format(tx.id))
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(ExcelStorage(self.data_file).load(), [])

    def test_salud(self):
        respuesta = self.client.get("/salud")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json, {"ok": True})


if __name__ == "__main__":
    unittest.main()