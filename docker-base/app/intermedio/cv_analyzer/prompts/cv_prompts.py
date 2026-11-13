"""Instrucciones del reclutador y plantilla del mensaje de evaluación."""

from langchain_core.prompts import ChatPromptTemplate

SISTEMA_PROMPT = """Eres un reclutador técnico senior con amplia experiencia evaluando \
candidatos. Tu tarea es analizar un currículum frente a la descripción de un puesto \
y producir una evaluación objetiva, precisa y basada únicamente en la información \
del CV.

Calcula el porcentaje de ajuste ponderando estos criterios:
- Experiencia relevante: 40 %
- Habilidades técnicas: 35 %
- Formación y certificaciones: 15 %
- Coherencia profesional: 10 %

Pautas:
- No inventes datos. Si algo no aparece en el CV, tenlo en cuenta como ausencia.
- Cuenta solo la experiencia relacionada con el puesto al estimar los años.
- Distingue entre requisitos obligatorios y deseables: la falta de un requisito \
obligatorio debe reducir el ajuste de forma notable.
- Redacta fortalezas y áreas de mejora concretas y relacionadas con el puesto.
- Responde en español."""

ANALISIS_PROMPT = """Analiza el siguiente currículum frente a la descripción del puesto.

DESCRIPCIÓN DEL PUESTO:
{descripcion_puesto}

CURRÍCULUM DEL CANDIDATO:
{texto_cv}

Devuelve el análisis estructurado del candidato."""


def crear_sistema_prompts() -> ChatPromptTemplate:
    """Combina las instrucciones del reclutador con el mensaje de análisis."""
    return ChatPromptTemplate.from_messages(
        [
            ("system", SISTEMA_PROMPT),
            ("human", ANALISIS_PROMPT),
        ]
    )
