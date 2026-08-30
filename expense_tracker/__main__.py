"""Punto de entrada para ejecutar el paquete con ``python -m expense_tracker``."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())