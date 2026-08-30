"""Definición del modelo de datos del gestor de gastos."""

import uuid
from dataclasses import asdict, dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Dict, List

TRANSACTION_TYPES: List[str] = ["gasto", "ingreso"]

CATEGORIAS_SUGERIDAS = ("comida", "transporte", "vivienda", "ocio", "salud", "otros")


def redondear_monto(valor: float) -> float:
    """Redondea un monto a 2 decimales con redondeo medio hacia arriba."""
    return float(Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


@dataclass
class Transaction:
    """Representa un ingreso o gasto registrado en el sistema."""

    tipo: str
    descripcion: str
    monto: float
    categoria: str = "otros"
    fecha: date = field(default_factory=date.today)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def __post_init__(self) -> None:
        self.tipo = self.tipo.strip().lower()
        if self.tipo not in TRANSACTION_TYPES:
            raise ValueError(
                f"Tipo inválido: '{self.tipo}'. Debe ser 'gasto' o 'ingreso'."
            )
        monto = float(self.monto)
        if monto < 0:
            raise ValueError("El monto no puede ser negativo.")
        self.monto = redondear_monto(monto)
        self.descripcion = self.descripcion.strip()
        if not self.descripcion:
            raise ValueError("La descripción no puede estar vacía.")
        if isinstance(self.fecha, str):
            self.fecha = date.fromisoformat(self.fecha)
        self.categoria = (self.categoria or "otros").strip().lower() or "otros"

    def to_dict(self) -> Dict[str, object]:
        """Convierte la transacción a un diccionario serializable."""
        data = asdict(self)
        data["fecha"] = self.fecha.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Transaction":
        """Construye una transacción a partir de un diccionario."""
        data = dict(data)
        data["fecha"] = date.fromisoformat(str(data["fecha"]))
        return cls(**data)