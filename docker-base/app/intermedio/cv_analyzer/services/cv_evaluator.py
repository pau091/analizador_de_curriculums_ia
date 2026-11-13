"""Configuración e invocación del modelo de lenguaje para evaluar candidatos.

El proveedor se elige con variables de entorno:

- LLM_PROVIDER: "ollama" (por defecto) u "openai".
- OLLAMA_MODEL (qwen2.5:7b), OLLAMA_BASE_URL (http://localhost:11434) y
  OLLAMA_NUM_CTX (8192) para Ollama.
- OPENAI_MODEL (gpt-4o-mini) y OPENAI_API_KEY para OpenAI.
"""

import logging
import os
from dataclasses import dataclass

from models.cv_model import AnalisisCV
from prompts.cv_prompts import crear_sistema_prompts

logger = logging.getLogger(__name__)

TEMPERATURA = 0.2
PROVEEDORES = ("ollama", "openai")


class ErrorEvaluacion(Exception):
    """La evaluación del candidato no pudo completarse."""


@dataclass(frozen=True)
class ConfiguracionLLM:
    proveedor: str
    modelo: str
    base_url: str | None = None
    num_ctx: int | None = None

    @property
    def descripcion(self) -> str:
        return f"{self.proveedor} · {self.modelo}"


def obtener_configuracion() -> ConfiguracionLLM:
    """Lee la configuración del modelo desde las variables de entorno."""
    proveedor = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
    if proveedor not in PROVEEDORES:
        raise ErrorEvaluacion(
            f"LLM_PROVIDER='{proveedor}' no es válido. Usa uno de: {', '.join(PROVEEDORES)}."
        )
    if proveedor == "openai":
        return ConfiguracionLLM("openai", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))

    try:
        num_ctx = int(os.getenv("OLLAMA_NUM_CTX", "8192"))
    except ValueError as error:
        raise ErrorEvaluacion("OLLAMA_NUM_CTX debe ser un número entero.") from error
    return ConfiguracionLLM(
        proveedor="ollama",
        modelo=os.getenv("OLLAMA_MODEL", "qwen2.5:7b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        num_ctx=num_ctx,
    )


def validar_configuracion(config: ConfiguracionLLM) -> str | None:
    """Devuelve un mensaje si falta algo para usar el proveedor, o None."""
    if config.proveedor == "openai" and not os.getenv("OPENAI_API_KEY"):
        return "LLM_PROVIDER=openai requiere la variable de entorno OPENAI_API_KEY."
    return None


def verificar_conexion(config: ConfiguracionLLM) -> tuple[bool, str]:
    """Comprueba de forma rápida si el proveedor está listo para usarse."""
    problema = validar_configuracion(config)
    if problema:
        return False, problema
    if config.proveedor != "ollama":
        return True, "Clave de OpenAI configurada"

    import json
    import urllib.request

    try:
        with urllib.request.urlopen(f"{config.base_url}/api/tags", timeout=2) as respuesta:
            modelos = {m["name"] for m in json.load(respuesta).get("models", [])}
    except Exception:
        return False, f"Ollama no responde en {config.base_url}"
    if config.modelo not in modelos and f"{config.modelo}:latest" not in modelos:
        return False, f"Falta el modelo. Ejecuta: ollama pull {config.modelo}"
    return True, "Ollama conectado"


def crear_evaluador_cv(config: ConfiguracionLLM | None = None):
    """Devuelve el modelo configurado para responder conforme a AnalisisCV."""
    config = config or obtener_configuracion()
    if config.proveedor == "openai":
        from langchain_openai import ChatOpenAI

        modelo = ChatOpenAI(model=config.modelo, temperature=TEMPERATURA)
    else:
        from langchain_ollama import ChatOllama

        modelo = ChatOllama(
            model=config.modelo,
            base_url=config.base_url,
            temperature=TEMPERATURA,
            num_ctx=config.num_ctx,  # evita que Ollama recorte CVs largos en silencio
        )
    return modelo.with_structured_output(AnalisisCV, method="json_schema")


def evaluar_candidato(texto_cv: str, descripcion_puesto: str) -> AnalisisCV:
    """Evalúa el CV frente al puesto y devuelve el análisis estructurado.

    Lanza ErrorEvaluacion con la causa original si falla la llamada al
    modelo o la validación de la respuesta, en lugar de devolver un
    análisis ficticio.
    """
    config = obtener_configuracion()
    try:
        cadena = crear_sistema_prompts() | crear_evaluador_cv(config)
        resultado = cadena.invoke(
            {"texto_cv": texto_cv, "descripcion_puesto": descripcion_puesto}
        )
    except Exception as error:
        logger.exception("Falló la evaluación del candidato con %s", config.descripcion)
        raise ErrorEvaluacion(
            f"No se pudo completar el análisis con {config.descripcion}: "
            f"{type(error).__name__}: {error}"
        ) from error

    if not isinstance(resultado, AnalisisCV):
        raise ErrorEvaluacion("El modelo no devolvió un análisis con el formato esperado.")
    return resultado
