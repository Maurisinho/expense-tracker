"""Genera atajos instalables (archivos .shortcut) para la app Atajos de iPhone.

El atajo generado:
  1. Pregunta la descripción del gasto.
  2. Pregunta el monto.
  3. Pregunta la categoría.
  4. Envía los datos a la API del gestor.
  5. Muestra la respuesta.
"""

import plistlib
import uuid
from typing import Dict, List


def _action(identificador: str, parametros: Dict[str, object], *,
            nombre_salida: str | None = None, uuid_accion: str | None = None) -> Dict[str, object]:
    accion: Dict[str, object] = {
        "WFWorkflowActionIdentifier": identificador,
        "WFWorkflowActionParameters": parametros,
    }
    if nombre_salida and uuid_accion:
        accion["ActionOutputName"] = nombre_salida
        accion["ActionOutputUUID"] = uuid_accion
    return accion


def _magic_variable(nombre: str, uuid_accion: str) -> Dict[str, object]:
    return {"Value": {"Type": "ActionOutput", "OutputName": nombre, "OutputUUID": uuid_accion}}


def generator_atajo(url_api: str, nombre_atayo: str = "Nuevo gasto") -> bytes:
    """Devuelve el contenido binario (plist) de un atajo de iPhone."""
    uuid_descripcion = str(uuid.uuid4()).upper()
    uuid_monto = str(uuid.uuid4()).upper()
    uuid_categoria = str(uuid.uuid4()).upper()

    acciones: List[Dict[str, object]] = [
        _action("is.workflow.actions.ask",
                {"WFAskActionPrompt": "¿Qué has comprado?", "WFInputType": "Text"},
                nombre_salida="Descripción", uuid_accion=uuid_descripcion),
        _action("is.workflow.actions.ask",
                {"WFAskActionPrompt": "¿Cuánto ha sido?", "WFInputType": "Number"},
                nombre_salida="Monto", uuid_accion=uuid_monto),
        _action("is.workflow.actions.ask",
                {"WFAskActionPrompt": "Categoría (comida, transporte, ocio...)", "WFInputType": "Text"},
                nombre_salida="Categoría", uuid_accion=uuid_categoria),
        _action("is.workflow.actions.downloadurl", {
            "WFHTTPMethod": "POST",
            "WFHTTPBodyType": "Json",
            "WFURL": url_api,
            "WFJSONValues": {
                "tipo": "gasto",
                "descripcion": _magic_variable("Descripción", uuid_descripcion),
                "monto": _magic_variable("Monto", uuid_monto),
                "categoria": _magic_variable("Categoría", uuid_categoria),
            },
        }),
        _action("is.workflow.actions.showresult", {}),
    ]

    flujo: Dict[str, object] = {
        "WFWorkflowActions": acciones,
        "WFWorkflowClientVersion": "1100",
        "WFWorkflowMinimumClientVersion": "900",
        "WFWorkflowImportQuestions": [],
        "WFWorkflowInputContentItemClasses": ["WFStringContentItem"],
        "WFWorkflowName": nombre_atayo,
        "WFWorkflowTypes": ["NCWidget"],
        "WFWorkflowIcon": {
            "WFWorkflowIconGlyphNumber": 59721,
            "WFWorkflowIconStartColor": 4271458815,
            "WFWorkflowIconBackgroundColor": 4294596039,
        },
    }

    return plistlib.dumps(flujo, fmt=plistlib.FMT_BINARY, sort_keys=False)