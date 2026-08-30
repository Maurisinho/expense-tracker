"""Persistencia de las transacciones en un archivo JSON o Excel."""

import json
import os
import sys
from pathlib import Path
from typing import List, Protocol

from .models import Transaction


class DataStorage(Protocol):
    """Interfaz común de los almacenamientos de datos."""

    def load(self) -> List[Transaction]:
        ...

    def save(self, transactions: List[Transaction]) -> None:
        ...


def default_data_file() -> Path:
    """Devuelve la ruta por defecto del archivo de datos (Excel en OneDrive)."""
    from .excel_store import default_excel_file

    return default_excel_file()


def build_storage(path=None):
    """Devuelve el almacenamiento adecuado según la extensión del archivo."""
    ruta = Path(path or default_data_file())
    if ruta.suffix.lower() == ".xlsx":
        from .excel_store import ExcelStorage

        return ExcelStorage(ruta)
    return Storage(ruta)


class Storage:
    """Lee y escribe las transacciones en un archivo JSON."""

    def __init__(self, path) -> None:
        self.path = Path(path)

    def load(self) -> List[Transaction]:
        """Carga las transacciones del archivo de datos."""
        if not self.path.exists():
            return []
        with open(self.path, "r", encoding="utf-8") as file:
            raw = json.load(file)
        return [Transaction.from_dict(item) for item in raw]

    def save(self, transactions: List[Transaction]) -> None:
        """Guarda las transacciones en el archivo de datos."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [transaction.to_dict() for transaction in transactions]
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)


def legacy_default_data_file() -> Path:
    """Antigua ruta JSON por defecto (solo para compatibilidad)."""
    if os.name == "nt":
        base = os.environ.get("APPDATA") or str(Path.home())
        folder = Path(base) / "ExpenseTracker"
    elif sys.platform == "darwin":
        folder = Path.home() / "Library" / "Application Support" / "ExpenseTracker"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        folder = base / "expense_tracker"
    return folder / "transactions.json"