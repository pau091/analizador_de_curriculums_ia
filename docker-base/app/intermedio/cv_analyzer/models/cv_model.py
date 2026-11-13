"""Esquema de salida estructurada del análisis de un currículum."""

from pydantic import BaseModel, Field


class AnalisisCV(BaseModel):
    """Resultado del análisis de un CV frente a la descripción de un puesto.

    Todos los campos son obligatorios. Las cantidades sugeridas en las
    descripciones orientan al modelo, pero no se validan.
    """

    nombre_candidato: str = Field(
        description="Nombre completo del candidato tal como aparece en el CV."
    )
    experiencia_años: int = Field(
        description="Años totales de experiencia laboral relevante para el puesto."
    )
    habilidades_clave: list[str] = Field(
        description="Entre 5 y 7 habilidades del candidato más relevantes para el puesto."
    )
    education: str = Field(
        description="Nivel educativo más alto alcanzado y especialización principal."
    )
    experiencia_relevante: str = Field(
        description="Resumen concreto de la experiencia directamente relacionada con el puesto."
    )
    fortalezas: list[str] = Field(
        description="Entre 3 y 5 fortalezas principales del candidato respecto al puesto."
    )
    areas_mejora: list[str] = Field(
        description="Entre 2 y 4 áreas en las que el candidato debería desarrollarse."
    )
    porcentaje_ajuste: int = Field(
        ge=0,
        le=100,
        description="Porcentaje de ajuste del candidato al puesto, entre 0 y 100.",
    )
