# Gestor de Gastos e Ingresos

Un gestor personal de gastos e ingresos que funciona desde la línea de comandos.
Escrito en Python **sin dependencias externas** (usa solo la biblioteca estándar),
así que funciona en Windows, macOS y Linux.

## Características

- Registrar gastos e ingresos con descripción, monto, categoría y fecha.
- Listar transacciones con filtros por tipo, categoría y rango de fechas.
- Eliminar transacciones por su identificador.
- Resumen de cuentas: totales, balance y desglose por categoría (con porcentajes).
- Resúmenes filtrados por año o por mes.
- Exportación de todas las transacciones a un archivo CSV.
- Persistencia automática en un archivo JSON (por defecto en tu carpeta de datos del sistema).
- Archivo de datos configurable con `--data-file`.

## Instalación

### Desde el código fuente (recomendado)

```bash
git clone https://github.com/Maurisinho/expense-tracker.git
cd expense-tracker
pip install -e .
```

### Sin instalación

Puedes ejecutarlo directamente sin instalar nada:

```bash
python -m expense_tracker --help
```

## Uso

Muestra la ayuda:

```bash
expense-tracker --help
```

### Registrar un gasto

```bash
expense-tracker agregar --descripcion "Café" --monto 3.50 --categoria comida
```

### Registrar un ingreso

```bash
expense-tracker agregar --tipo ingreso --descripcion "Nómina" --monto 1500 --fecha 2026-08-01
```

### Listar transacciones

```bash
expense-tracker listar
expense-tracker listar --tipo gasto --categoria comida
expense-tracker listar --desde 2026-08-01 --hasta 2026-08-31
```

### Eliminar una transacción

```bash
expense-tracker listar        # para ver el id de cada transacción
expense-tracker eliminar --id 3f2a1b4c9d0e
```

### Resumen de cuentas

```bash
expense-tracker resumen               # de todo el período
expense-tracker resumen --anio 2026
expense-tracker resumen --anio 2026 --mes 8
```

### Exportar a CSV

```bash
expense-tracker exportar --archivo mis-gastos.csv
```

### Usar un archivo de datos propio

```bash
expense-tracker --data-file ./mi-datos.json agregar --descripcion "Prueba" --monto 5
```

## Ejemplo de salida

```
$ expense-tracker resumen --anio 2026 --mes 8
Resumen (2026-08)
----------------------------------------
Ingresos : $1,500.00
Gastos   :   $253.50
Balance  : $1,246.50 (superávit)
----------------------------------------
Gastos por categoría:
  vivienda      $120.00   47.3%
  comida         $80.50   31.8%
  transporte     $40.00   15.8%
  ocio           $13.00    5.1%
```

## Estructura del proyecto

```
expense-tracker/
├── expense_tracker/
│   ├── __init__.py      # metadatos del paquete
│   ├── __main__.py      # permite ejecutar con python -m
│   ├── cli.py           # interfaz de línea de comandos
│   ├── models.py        # modelo de datos (Transaction)
│   ├── reports.py       # resúmenes y exportación CSV
│   └── storage.py       # persistencia en JSON
├── tests/
│   └── test_tracker.py  # pruebas (unittest)
├── .github/workflows/ci.yml
├── pyproject.toml
└── README.md
```

## Ejecutar las pruebas

```bash
python -m unittest discover -s tests -v
```

## Licencia

Distribuido bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE).