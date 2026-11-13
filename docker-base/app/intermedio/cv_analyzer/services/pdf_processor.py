"""Extracción de texto de currículums en PDF."""

from typing import BinaryIO

from PyPDF2 import PdfReader

PREFIJO_ERROR = "Error:"


def es_error(texto: str) -> bool:
    """Indica si el resultado de extraer_texto_pdf() es un mensaje de error."""
    return texto.startswith(PREFIJO_ERROR)


def extraer_texto_pdf(archivo_pdf: BinaryIO) -> str:
    """Lee el PDF en memoria y concatena el texto de sus páginas.

    Devuelve el texto con un separador por página o, si no hay texto
    extraíble o la lectura falla, un mensaje que empieza por PREFIJO_ERROR.
    """
    try:
        lector = PdfReader(archivo_pdf)
        paginas = []
        for numero, pagina in enumerate(lector.pages, start=1):
            texto = (pagina.extract_text() or "").strip()
            if texto:
                paginas.append(f"--- Página {numero} ---\n{texto}")

        if not paginas:
            return (
                f"{PREFIJO_ERROR} no se encontró texto en el PDF. "
                "Asegúrate de que tenga texto seleccionable (no se admite OCR)."
            )
        return "\n\n".join(paginas)
    except Exception as error:  # PyPDF2 lanza varios tipos de excepción
        return f"{PREFIJO_ERROR} no se pudo leer el PDF ({error})."
