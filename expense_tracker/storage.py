"""Persistencia de las transacciones en un archivo JSON."""

import json
import os
import sys
from pathlib import Path
from typing import List

from .models import Transaction


def default_data_file() -> Path:
    """Devuelve la ruta por defecto del archivo de datos según el sistema."""
    if os.name == "nt":
        base = os.environ.get("APPDATA") or str(Path.home())
        folder = Path(base) / "ExpenseTracker"
    elif sys.platform == "darwin":
        folder = Path.home() / "Library" / "Application Support" / "ExpenseTracker"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        folder = base / "expense_tracker"
    return folder / "transactions.json"


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