"""Interfaz de Streamlit: entradas, validaciones y presentación del análisis."""

import json
import time
from pathlib import Path

import streamlit as st

from models.cv_model import AnalisisCV
from services.cv_evaluator import (
    ConfiguracionLLM,
    ErrorEvaluacion,
    evaluar_candidato,
    obtener_configuracion,
    validar_configuracion,
    verificar_conexion,
)
from services.pdf_processor import es_error, extraer_texto_pdf
from ui import styles

EJEMPLO_PUESTO = """Puesto: Desarrollador Python
Requisitos obligatorios: 3 años de experiencia, Python, APIs REST y PostgreSQL.
Deseables: Docker, pruebas automatizadas y experiencia con LangChain.
Responsabilidades: desarrollar servicios, integrar APIs y mantener pruebas."""

CARPETA_EJEMPLOS = Path(__file__).resolve().parent.parent / "ejemplos"

VERDE, AZUL, AMBAR, ROJO = "#15803D", "#1D4ED8", "#B45309", "#B91C1C"

CRITERIOS = [
    ("Experiencia relevante", "40 %"),
    ("Habilidades técnicas", "35 %"),
    ("Formación y certificaciones", "15 %"),
    ("Coherencia profesional", "10 %"),
]


def obtener_evaluacion(porcentaje: int) -> tuple[str, str]:
    """Devuelve la etiqueta y el color de la evaluación principal."""
    if porcentaje >= 80:
        return "Excelente", VERDE
    if porcentaje >= 60:
        return "Bueno", AZUL
    if porcentaje >= 40:
        return "Regular", AMBAR
    return "Bajo", ROJO


def obtener_recomendacion(porcentaje: int) -> tuple[str, str, str]:
    """Devuelve el título, el detalle y el color de la recomendación final."""
    if porcentaje >= 70:
        return ("Candidato recomendado",
                "Cumple de forma sólida con el perfil del puesto.", VERDE)
    if porcentaje >= 50:
        return ("Candidato con potencial",
                "Conviene validar las áreas de mejora en una entrevista.", AMBAR)
    return ("Candidato no recomendado",
            "El perfil se aleja de los requisitos del puesto.", ROJO)


# --- Estado y acciones -------------------------------------------------------

def _inicializar_estado() -> None:
    st.session_state.setdefault("id_cargador", 0)
    st.session_state.setdefault("descripcion_puesto", "")
    st.session_state.setdefault("analisis", None)
    st.session_state.setdefault("meta", {})


def _limpiar() -> None:
    """Borra el PDF, la descripción y el último análisis."""
    st.session_state.id_cargador += 1  # una clave nueva vacía el file_uploader
    st.session_state.descripcion_puesto = ""
    st.session_state.analisis = None
    st.session_state.meta = {}


def _usar_ejemplo() -> None:
    st.session_state.descripcion_puesto = EJEMPLO_PUESTO


def _guardar() -> None:
    st.toast("La función Guardar Análisis está en desarrollo.")


@st.cache_data(ttl=20, show_spinner=False)
def _estado_conexion(config: ConfiguracionLLM) -> tuple[bool, str]:
    return verificar_conexion(config)


# --- Secciones de la página --------------------------------------------------

def mostrar_barra_lateral(config: ConfiguracionLLM) -> None:
    with st.sidebar:
        st.markdown("### Configuración")
        listo, mensaje = _estado_conexion(config)
        st.markdown(styles.estado(mensaje, VERDE if listo else ROJO), unsafe_allow_html=True)
        st.markdown(
            styles.tabla_mini([("Proveedor", config.proveedor), ("Modelo", config.modelo)]),
            unsafe_allow_html=True,
        )
        if st.button("Volver a comprobar", width="stretch"):
            _estado_conexion.clear()
            st.rerun()

        st.divider()
        st.markdown("### Criterios de evaluación")
        st.markdown(styles.tabla_mini(CRITERIOS), unsafe_allow_html=True)
        st.caption("Pesos indicados al modelo en el prompt. El porcentaje lo estima el modelo.")

        st.markdown("### Escala")
        st.markdown(
            styles.tabla_mini([
                ("Excelente", "80–100"), ("Bueno", "60–79"),
                ("Regular", "40–59"), ("Bajo", "0–39"),
            ]),
            unsafe_allow_html=True,
        )

        st.divider()
        if config.proveedor == "ollama":
            st.caption("Procesamiento local: el CV no sale de este equipo.")
        else:
            st.caption("El texto del CV y del puesto se envían a OpenAI.")


def mostrar_analisis(analisis: AnalisisCV, meta: dict) -> None:
    porcentaje = analisis.porcentaje_ajuste
    evaluacion, color_eval = obtener_evaluacion(porcentaje)
    titulo, detalle, color_rec = obtener_recomendacion(porcentaje)

    st.markdown("## Resultado del análisis")

    col_puntaje, col_perfil = st.columns([1, 2.2], gap="medium")
    with col_puntaje, st.container(border=True):
        st.markdown(styles.seccion("Ajuste al puesto"), unsafe_allow_html=True)
        st.markdown(styles.anillo_puntaje(porcentaje, evaluacion, color_eval), unsafe_allow_html=True)
    with col_perfil, st.container(border=True):
        st.markdown(styles.seccion("Perfil del candidato"), unsafe_allow_html=True)
        a, b = st.columns(2)
        a.markdown(
            styles.dato("Nombre", analisis.nombre_candidato)
            + styles.dato("Experiencia relevante", f"{analisis.experiencia_años} años"),
            unsafe_allow_html=True,
        )
        b.markdown(styles.dato("Educación", analisis.education), unsafe_allow_html=True)
        st.markdown(
            f'<div class="resumen">{styles.escape(analisis.experiencia_relevante)}</div>',
            unsafe_allow_html=True,
        )

    with st.container(border=True):
        st.markdown(styles.seccion("Habilidades clave"), unsafe_allow_html=True)
        st.markdown(styles.chips(analisis.habilidades_clave), unsafe_allow_html=True)

    col_f, col_m = st.columns(2, gap="medium")
    with col_f, st.container(border=True):
        st.markdown(styles.seccion("Fortalezas"), unsafe_allow_html=True)
        st.markdown(styles.lista(analisis.fortalezas, positiva=True), unsafe_allow_html=True)
    with col_m, st.container(border=True):
        st.markdown(styles.seccion("Áreas de desarrollo"), unsafe_allow_html=True)
        st.markdown(styles.lista(analisis.areas_mejora, positiva=False), unsafe_allow_html=True)

    st.markdown(styles.veredicto(titulo, detalle, color_rec), unsafe_allow_html=True)
    if meta:
        st.markdown(
            f'<div class="meta">{styles.escape(meta["archivo"])} · {styles.escape(meta["modelo"])} · '
            f'{meta["segundos"]:.0f} s</div>',
            unsafe_allow_html=True,
        )


def _configuracion_o_detener() -> ConfiguracionLLM:
    try:
        return obtener_configuracion()
    except ErrorEvaluacion as error:
        st.error(str(error))
        st.stop()


def pagina_analizador() -> None:
    config = _configuracion_o_detener()
    st.markdown(
        styles.hero(
            "Analizador de currículums con IA",
            "Compara un CV en PDF con la descripción de un puesto y obtén una evaluación "
            "estructurada del candidato.",
            ["LangChain", "Salida estructurada con Pydantic", config.descripcion],
        ),
        unsafe_allow_html=True,
    )

    col_cv, col_puesto = st.columns(2, gap="medium")
    with col_cv, st.container(border=True):
        st.markdown(styles.paso(1, "Currículum", "PDF con texto seleccionable (no se admite OCR)."),
                    unsafe_allow_html=True)
        archivo_cv = st.file_uploader(
            "Currículum en PDF",
            type=["pdf"],
            key=f"cv_{st.session_state.id_cargador}",
            label_visibility="collapsed",
        )
    with col_puesto, st.container(border=True):
        st.markdown(styles.paso(2, "Descripción del puesto",
                                "Requisitos obligatorios, deseables y responsabilidades."),
                    unsafe_allow_html=True)
        descripcion = st.text_area(
            "Descripción del puesto",
            key="descripcion_puesto",
            height=150,
            placeholder=EJEMPLO_PUESTO,
            label_visibility="collapsed",
        )
        st.button("Usar descripción de ejemplo", on_click=_usar_ejemplo, type="tertiary")

    col_analizar, col_limpiar, col_guardar = st.columns([2, 1, 1])
    analizar = col_analizar.button("Analizar Candidato", type="primary", width="stretch")
    col_limpiar.button("Limpiar", on_click=_limpiar, width="stretch")
    col_guardar.button(
        "Guardar Análisis",
        on_click=_guardar,
        disabled=st.session_state.analisis is None,
        width="stretch",
    )

    if analizar:
        st.session_state.analisis = None
        st.session_state.meta = {}
        if archivo_cv is None or not descripcion.strip():
            st.warning("Carga un CV en PDF y escribe la descripción del puesto.")
            st.stop()
        problema = validar_configuracion(config)
        if problema:
            st.error(problema)
            st.stop()

        with st.status("Analizando candidato...", expanded=True) as estado:
            st.write("Extrayendo texto del PDF...")
            texto_cv = extraer_texto_pdf(archivo_cv)
            if es_error(texto_cv):
                estado.update(label="No se pudo leer el PDF", state="error")
                st.error(texto_cv)
                st.stop()

            st.write(f"Evaluando con {config.descripcion}. Con un modelo local puede tardar unos minutos...")
            inicio = time.perf_counter()
            try:
                st.session_state.analisis = evaluar_candidato(texto_cv, descripcion.strip())
            except ErrorEvaluacion as error:
                estado.update(label="El análisis falló", state="error")
                st.error(str(error))
                if config.proveedor == "ollama":
                    st.info(
                        f"Comprueba que Ollama esté en ejecución en {config.base_url} "
                        f"y que el modelo esté descargado: ollama pull {config.modelo}"
                    )
                else:
                    st.info("Revisa la clave de OpenAI, la conexión, el acceso al modelo y la cuota.")
                st.stop()
            st.session_state.meta = {
                "archivo": archivo_cv.name,
                "modelo": config.descripcion,
                "segundos": time.perf_counter() - inicio,
            }
            estado.update(label="Análisis completado", state="complete", expanded=False)
        st.rerun()  # vuelve a dibujar la página para habilitar "Guardar Análisis"

    if st.session_state.analisis is not None:
        st.divider()
        mostrar_analisis(st.session_state.analisis, st.session_state.meta)


@st.cache_data(show_spinner=False)
def _cargar_ejemplo() -> tuple[dict, bytes]:
    """Lee el análisis pregenerado y el PDF del CV de ejemplo."""
    datos = json.loads((CARPETA_EJEMPLOS / "analisis_ejemplo.json").read_text(encoding="utf-8"))
    pdf = (CARPETA_EJEMPLOS / "cv_ejemplo.pdf").read_bytes()
    return datos, pdf


def pagina_ejemplo() -> None:
    """Muestra un análisis real generado previamente, sin llamar al modelo."""
    try:
        datos, pdf = _cargar_ejemplo()
        analisis = AnalisisCV.model_validate(datos["analisis"])
        meta = datos["meta"]
    except (OSError, KeyError, ValueError) as error:
        st.error(f"No se pudo cargar el ejemplo de la carpeta ejemplos/: {error}")
        st.stop()

    st.markdown(
        styles.hero(
            "Ejemplo de análisis",
            "Resultado real generado previamente sobre un CV ficticio. Se muestra al instante, "
            "sin volver a llamar al modelo.",
            ["CV de ejemplo", meta["modelo"], f"Generado el {meta['fecha']}"],
        ),
        unsafe_allow_html=True,
    )

    col_cv, col_puesto = st.columns(2, gap="medium")
    with col_cv, st.container(border=True):
        st.markdown(styles.paso(1, "Currículum", "Candidata ficticia creada para la demostración."),
                    unsafe_allow_html=True)
        st.download_button(
            "Descargar CV de ejemplo (PDF)",
            data=pdf,
            file_name=meta["archivo"],
            mime="application/pdf",
            on_click="ignore",
            width="stretch",
        )
        st.caption("Súbelo en la pestaña Analizador para repetir el análisis en vivo.")
    with col_puesto, st.container(border=True):
        st.markdown(styles.paso(2, "Descripción del puesto", "Usada para generar este resultado."),
                    unsafe_allow_html=True)
        st.markdown(
            '<div class="resumen">'
            + styles.escape(datos["descripcion_puesto"]).replace("\n", "<br>")
            + "</div>",
            unsafe_allow_html=True,
        )

    st.divider()
    mostrar_analisis(analisis, meta)


def main() -> None:
    st.set_page_config(page_title="Analizador de CV con IA", layout="wide")
    st.markdown(styles.CSS, unsafe_allow_html=True)
    _inicializar_estado()
    mostrar_barra_lateral(_configuracion_o_detener())

    pagina = st.navigation(
        [
            st.Page(pagina_analizador, title="Analizador", url_path="analizador", default=True),
            st.Page(pagina_ejemplo, title="Ejemplo", url_path="ejemplo"),
        ],
        position="top",
    )
    pagina.run()
