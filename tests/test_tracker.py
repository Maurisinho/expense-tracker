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
from expense_tracker.storage import Storage


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

    def ejecutar(self, *args):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            codigo = main(["--data-file", self.data_file, *args])
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


if __name__ == "__main__":
    unittest.main()