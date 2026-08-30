# Gestor de Gastos e Ingresos

Un gestor personal de gastos e ingresos que funciona de tres maneras:

1. **Desde la terminal** (programa de línea de comandos).
2. **Desde tu iPhone o cualquier navegador**, gracias a una app web con un
   túnel de Cloudflare que la hace accesible desde cualquier lugar.
3. **Tus datos viven en un Excel en la nube (OneDrive)**: el programa lee y
   escribe un archivo `.xlsx` en tu carpeta de OneDrive, que se sincroniza
   solo con la nube y puedes abrir con la app Excel de tu iPhone.

## Características

- Registrar gastos e ingresos con descripción, monto, categoría y fecha.
- Interfaz web **adaptada a móvil**: añade gastos desde el iPhone en segundos.
- Listar transacciones con filtros por tipo, categoría y rango de fechas.
- Eliminar transacciones por su identificador.
- Resumen de cuentas: totales, balance y desglose por categoría (con porcentajes).
- Resúmenes filtrados por año o por mes.
- Exportación de todas las transacciones a un archivo CSV.
- Persistencia en **Excel (xlsx)** dentro de tu carpeta de OneDrive por defecto
  (también se admite JSON, según la extensión del archivo de datos).

## Requisitos

- Python 3.9 o superior.
- Dependencias: `Flask` y `openpyxl` (se instalan automáticamente).
- `cloudflared` (solo para la web accesible desde cualquier lugar):

  ```powershell
  winget install Cloudflare.cloudflared
  ```

## Instalación

```bash
git clone https://github.com/Maurisinho/expense-tracker.git
cd expense-tracker
pip install -e .
```

## Usarla desde tu iPhone (acceso desde cualquier lugar)

1. En el PC, ejecuta el arranque de todo:

   ```powershell
   .\iniciar.ps1
   ```

   El script enciende el servidor web y crea un túnel de Cloudflare, y te
   muestra una URL tipo `https://xxxx.trycloudflare.com`.

2. Abre esa URL en tu iPhone (funciona con 4G/5G o cualquier WiFi).
3. Añade gastos e ingresos: se guardan al instante en el Excel de tu OneDrive.

> **Nota sobre la URL**: con el túnel gratuito (`trycloudflare.com`) la URL
> cambia cada vez que reinicias el túnel. Si quieres un enlace fijo, mira la
> sección *Túnel fijo* más abajo.

### Ver el Excel en la nube

El archivo de datos por defecto es:

```
C:\Users\mauri\OneDrive\ExpenseTracker\transacciones.xlsx
```

- Se sincroniza solo con **OneDrive** (nube) en cuanto lo guardas.
- Ábrelo desde el iPhone con la app **Excel** o desde **onedrive.com**.
- Puedes editarlo manualmente; el programa lee cualquier cambio que hagas.

## Usarla con Atajos (Shortcuts) de iPhone

La web genera un **atajo `.shortcut` ya construido** que se instala con un toque
y usa la API JSON del gestor (0 preguntas de configuración).

### Instalación automática del atajo

1. Desde tu **iPhone**, abre en Safari la dirección de tu gestor y pulsa el
   enlace **"¿Quieres añadir gastos con Atajos/Siri? Instala el atajo"** que
   aparece al final de la página (equivalente a `TU-URL/atajo/instalar`).
2. Safari descargará `nuevo-gasto.shortcut`; iOS te mostrará **"Obtener atajo"**
   → pulsa **Añadir atajo**.
3. Listo. El atajo **"Nuevo gasto"** te preguntará:

   - ¿Qué has comprado? *(descripción)*
   - ¿Cuánto ha sido? *(monto)*
   - Categoría *(comida, transporte, ocio...)*

   …lo envía a la API, lo guarda en el Excel de OneDrive y te muestra la respuesta.

4. Para usarlo con **Siri**: *"Oye Siri, Nuevo gasto"*.

> Un atajo de iPhone no se puede probar desde este ordenador: si al instalarlo
> iOS te pide permisos extra (p. ej. "redes locales"), acéptalos. Y recuerda que
> si la URL del túnel cambia al reiniciar `iniciar.ps1`, vuelve a instalar el
> atajo (o configura el *Túnel fijo* para que no cambie).

### Cómo crear el atajo manualmente (alternativa)

1. Abre la app **Atajos** y pulsa **+** → **Nuevo atajo**.
2. Añade la acción **Texto**: escribe `Descripción` y en el valor pulsa
   **Preguntar cada vez**. Será lo que describa el gasto.
3. Añade la acción **Número**: escribe el monto y actívalo como
   **Preguntar cada vez**.
4. (Opcional) Añade otro **Texto** `Categoría` con "Preguntar cada vez"
   (comida, transporte, ocio...). Si lo omites, quedará como `otros`.
5. Añade la acción **Obtener contenido de URL**:

   - **URL**: `https://TU-URL-DEL-TUNEL/api/agregar`
   - **Método**: `POST`
   - **Cuerpo**: `JSON`
   - **Añadir campo**:
     - `descripcion` → la variable del texto *Descripción*
     - `monto` → la variable del número
     - `categoria` → la variable *Categoría* (o un texto fijo `otros`)
     - `tipo` → texto fijo `gasto` (o "Preguntar cada vez" para gasto/ingreso)

6. Añade la acción **Mostrar resultado** seleccionando *Contenido de la URL*.
7. Ponle nombre al atajo (ej. `Añadir gasto`) y pruébalo.

Ahora puedes decirle a Siri: **"Oye Siri, Añadir gasto"**.

> La URL de `trycloudflare.com` cambia cada vez que reinicias el túnel; si te
> pasa, vuelve a ejecutar `iniciar.ps1` y actualiza la URL del paso 5 (o
> configura el *Túnel fijo* más arriba si quieres que no cambie nunca).

### Referencia rápida de la API

| Método | Ruta | Cuerpo | Respuesta |
| --- | --- | --- | --- |
| `POST` | `/api/agregar` | `{"tipo","descripcion","monto","categoria","fecha"}` | `{"ok":true,"id":...}` |
| `GET` | `/api/listar` | — | `{"transacciones":[...]}` |
| `GET` | `/api/resumen` | — | `{"resumen":{...},"resumen_mes":{...}}` |
| `POST` | `/api/eliminar/<id>` | — | `{"ok":true}` |

Todos los campos de `/api/agregar` aceptan también formulario o parámetros en
la URL, así que un atajo aún más sencillo puede llamar a:

```
https://TU-URL/api/agregar?descripcion=Café&monto=3.5&categoria=comida&tipo=gasto
```

## Uso desde la terminal

Muestra la ayuda:

```bash
expense-tracker --help
```

```bash
# Registrar un gasto
expense-tracker agregar --descripcion "Café" --monto 3.50 --categoria comida

# Registrar un ingreso
expense-tracker agregar --tipo ingreso --descripcion "Nómina" --monto 1500

# Listar, filtrar y eliminar
expense-tracker listar --tipo gasto --categoria comida
expense-tracker listar --desde 2026-08-01 --hasta 2026-08-31
expense-tracker eliminar --id 3f2a1b4c9d0e

# Resúmenes y exportación
expense-tracker resumen --anio 2026 --mes 8
expense-tracker exportar --archivo mis-gastos.csv
```

Por defecto, el CLI también guarda en el Excel de OneDrive. Para indicar otro
archivo de datos (Excel o JSON):

```bash
expense-tracker --data-file ./misdatos.xlsx agregar --descripcion "Prueba" --monto 5
```

## Arranque manual del servidor web

```powershell
# Servidor local (solo mismo equipo o red local)
python -m expense_tracker.webapp --host 0.0.0.0 --port 5000

# O usando el comando instalado
expense-tracker-web
```

Para el túnel de Cloudflare por separado:

```powershell
cloudflared tunnel --url http://127.0.0.1:5000
```

## Túnel fijo (opcional)

Si una URL estable te importa (en lugar de la que cambia de `trycloudflare`):

```powershell
cloudflared tunnel login                     # vincula tu cuenta de Cloudflare
cloudflared tunnel create gastos             # crea el túnel
cloudflared tunnel route dns gastos gastos.tudominio.com
```

Después, con un pequeño archivo de config (o con la flag `--url`) el enlace
`https://gastos.tudominio.com` será permanente.

## Ejecutar las pruebas

```bash
python -m unittest discover -s tests -v
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
│   ├── excel_store.py   # almacenamiento en Excel (xlsx)
│   ├── storage.py       # selección de almacenamiento (Excel/JSON)
│   ├── webapp.py        # servidor web para móvil (Flask)
│   ├── shortcuts.py     # generador de atajos para la app Atajos de iPhone
│   ├── templates/       # interfaz web móvil
│   └── static/          # estilos y scripts de la web
├── tests/
│   └── test_tracker.py  # pruebas (unittest)
├── iniciar.ps1          # arranca servidor + túnel Cloudflare
├── .github/workflows/ci.yml
├── pyproject.toml
└── README.md
```

## Licencia

Distribuido bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE).