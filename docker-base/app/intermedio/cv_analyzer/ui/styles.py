"""Estilos y componentes HTML de la interfaz.

Todo texto que procede del CV o del modelo se escapa con html.escape antes
de insertarse en HTML.
"""

from html import escape

CSS = """
<style>
:root {
  --azul: #1E40AF;
  --azul-oscuro: #0F1E4A;
  --texto: #0F172A;
  --texto-suave: #475569;
  --borde: #E2E8F0;
  --tarjeta: #FFFFFF;
}
.block-container { padding-top: 2rem; max-width: 1200px; }
#MainMenu, footer { visibility: hidden; }

.hero {
  background: linear-gradient(120deg, var(--azul-oscuro) 0%, var(--azul) 100%);
  color: #FFFFFF; border-radius: 14px; padding: 1.6rem 2rem; margin-bottom: 1.4rem;
}
.hero h1 { color: #FFFFFF; font-size: 1.9rem; margin: 0 0 .3rem 0; padding: 0; }
.hero p { color: #DBE4FF; margin: 0; font-size: 1rem; }
.hero .insignias { margin-top: .9rem; display: flex; gap: .5rem; flex-wrap: wrap; }
.hero .insignia {
  background: rgba(255,255,255,.14); border: 1px solid rgba(255,255,255,.25);
  color: #FFFFFF; border-radius: 999px; padding: .2rem .75rem; font-size: .8rem;
}

.paso { display: flex; align-items: center; gap: .6rem; margin-bottom: .4rem; }
.paso .num {
  width: 28px; height: 28px; border-radius: 50%; background: var(--azul); color: #FFFFFF;
  display: grid; place-items: center; font-weight: 700; font-size: .9rem; flex-shrink: 0;
}
.paso .titulo { font-weight: 700; font-size: 1.05rem; color: var(--texto); }
.paso-ayuda { color: var(--texto-suave); font-size: .88rem; margin: 0 0 .6rem 2.4rem; }

.seccion { font-size: .78rem; letter-spacing: .08em; text-transform: uppercase;
  color: var(--texto-suave); font-weight: 700; margin: 0 0 .6rem 0; }

.puntaje { display: flex; flex-direction: column; align-items: center; gap: .6rem; }
.anillo {
  width: 168px; height: 168px; border-radius: 50%;
  background: conic-gradient(var(--c) calc(var(--p) * 1%), #E5E9F2 0);
  display: grid; place-items: center;
}
.anillo .interior {
  width: 132px; height: 132px; border-radius: 50%; background: #FFFFFF;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.anillo .valor { font-size: 2.3rem; font-weight: 800; color: var(--texto); line-height: 1; }
.anillo .etiqueta { font-size: .8rem; color: var(--texto-suave); margin-top: .25rem; }
.evaluacion {
  border-radius: 999px; padding: .25rem .9rem; font-weight: 700; font-size: .9rem;
  color: var(--c); background: color-mix(in srgb, var(--c) 12%, white);
}

.dato { margin-bottom: .75rem; }
.dato .k { font-size: .78rem; color: var(--texto-suave); text-transform: uppercase;
  letter-spacing: .05em; }
.dato .v { font-size: 1.02rem; color: var(--texto); font-weight: 600; }
.resumen { color: var(--texto); line-height: 1.55; font-size: .95rem; }

.chips { display: flex; flex-wrap: wrap; gap: .45rem; padding-bottom: .5rem; }
.resumen { padding-bottom: .5rem; }
.chip {
  background: #EEF2FF; color: var(--azul); border: 1px solid #C7D2FE;
  border-radius: 999px; padding: .3rem .8rem; font-size: .86rem; font-weight: 600;
}

.lista { list-style: none; padding: 0; margin: 0; }
.lista li { display: flex; gap: .55rem; padding: .45rem 0; color: var(--texto);
  border-bottom: 1px solid var(--borde); font-size: .93rem; line-height: 1.45; }
.lista li:last-child { border-bottom: none; }
.lista .icono { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: .5rem; }
.lista.pos .icono { background: #15803D; }
.lista.neg .icono { background: #B45309; }

.veredicto {
  border-radius: 12px; padding: 1.1rem 1.3rem; border-left: 6px solid var(--c);
  background: color-mix(in srgb, var(--c) 9%, white);
}
.veredicto .t { font-weight: 800; color: var(--c); font-size: 1.1rem; }
.veredicto .d { color: var(--texto); margin-top: .2rem; font-size: .95rem; }

.meta { color: var(--texto-suave); font-size: .8rem; text-align: right; margin-top: .4rem; }

.estado { display: flex; align-items: center; gap: .5rem; font-weight: 600; }
.punto { width: 10px; height: 10px; border-radius: 50%; background: var(--c); }
.tabla-mini { width: 100%; font-size: .85rem; border-collapse: collapse; border: none; }
.tabla-mini tr, .tabla-mini td { border: none; background: transparent; }
.tabla-mini td { padding: .35rem 0; border-bottom: 1px solid var(--borde); }
.tabla-mini td:last-child { text-align: right; font-weight: 700; }
</style>
"""


def hero(titulo: str, subtitulo: str, insignias: list[str]) -> str:
    chips = "".join(f'<span class="insignia">{escape(i)}</span>' for i in insignias)
    return (
        f'<div class="hero"><h1>{escape(titulo)}</h1><p>{escape(subtitulo)}</p>'
        f'<div class="insignias">{chips}</div></div>'
    )


def paso(numero: int, titulo: str, ayuda: str) -> str:
    return (
        f'<div class="paso"><span class="num">{numero}</span>'
        f'<span class="titulo">{escape(titulo)}</span></div>'
        f'<p class="paso-ayuda">{escape(ayuda)}</p>'
    )


def seccion(titulo: str) -> str:
    return f'<p class="seccion">{escape(titulo)}</p>'


def anillo_puntaje(porcentaje: int, evaluacion: str, color: str) -> str:
    return (
        f'<div class="puntaje"><div class="anillo" style="--p:{porcentaje};--c:{color}">'
        f'<div class="interior"><span class="valor">{porcentaje}%</span>'
        f'<span class="etiqueta">ajuste al puesto</span></div></div>'
        f'<span class="evaluacion" style="--c:{color}">{escape(evaluacion)}</span></div>'
    )


def dato(clave: str, valor: str) -> str:
    return f'<div class="dato"><div class="k">{escape(clave)}</div><div class="v">{escape(valor)}</div></div>'


def chips(elementos: list[str]) -> str:
    if not elementos:
        return '<p class="resumen">Sin datos.</p>'
    return '<div class="chips">' + "".join(f'<span class="chip">{escape(e)}</span>' for e in elementos) + "</div>"


def lista(elementos: list[str], positiva: bool) -> str:
    if not elementos:
        return '<p class="resumen">Sin datos.</p>'
    clase = "pos" if positiva else "neg"
    items = "".join(f'<li><span class="icono"></span><span>{escape(e)}</span></li>' for e in elementos)
    return f'<ul class="lista {clase}">{items}</ul>'


def veredicto(titulo: str, detalle: str, color: str) -> str:
    return (
        f'<div class="veredicto" style="--c:{color}"><div class="t">{escape(titulo)}</div>'
        f'<div class="d">{escape(detalle)}</div></div>'
    )


def estado(texto: str, color: str) -> str:
    return f'<div class="estado"><span class="punto" style="--c:{color}"></span>{escape(texto)}</div>'


def tabla_mini(filas: list[tuple[str, str]]) -> str:
    cuerpo = "".join(f"<tr><td>{escape(a)}</td><td>{escape(b)}</td></tr>" for a, b in filas)
    return f'<table class="tabla-mini">{cuerpo}</table>'
