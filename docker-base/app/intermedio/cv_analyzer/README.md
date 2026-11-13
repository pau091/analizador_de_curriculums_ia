# Analizador de currículums con IA

Aplicación de Streamlit que compara un currículum en PDF con la descripción de un puesto. Extrae el texto del documento, lo envía a un modelo de lenguaje mediante LangChain y muestra un análisis estructurado del candidato.

Por defecto usa un modelo **local** servido por [Ollama](https://ollama.com) (`qwen2.5:7b`), de modo que el CV no sale del equipo. De forma opcional puede usar OpenAI (`gpt-4o-mini`) cambiando una variable de entorno.

## Contenido

- [Funcionalidades](#funcionalidades)
- [Funcionamiento](#funcionamiento)
- [Decisiones técnicas](#decisiones-técnicas)
- [Criterios de evaluación](#criterios-de-evaluación)
- [Estructura](#estructura)
- [Modelo de salida](#modelo-de-salida)
- [Requisitos](#requisitos)
- [Configuración](#configuración)
- [Ejecución local](#ejecución-local)
- [Ejecución con Docker](#ejecución-con-docker)
- [Uso](#uso)
- [Cambios respecto al código base](#cambios-respecto-al-código-base)
- [Limitaciones](#limitaciones)
- [Resolución de problemas](#resolución-de-problemas)
- [Enlaces de la aplicación](#enlaces-de-la-aplicación)

## Funcionalidades

- Carga de un CV en formato PDF con texto seleccionable.
- Entrada de los requisitos y responsabilidades del puesto, con un ejemplo que se puede cargar con un botón.
- Extracción del nombre, experiencia, educación y habilidades relevantes.
- Identificación de fortalezas y áreas de desarrollo.
- Estimación del porcentaje de ajuste al puesto, entre 0 y 100.
- Recomendación final de contratación según el resultado.
- Panel lateral con el estado de conexión del modelo, los criterios de evaluación y la escala.
- Elección del proveedor del modelo (Ollama u OpenAI) mediante variables de entorno.
- Pestaña **Ejemplo** con un análisis real generado previamente sobre un CV ficticio. Se muestra al instante, sin llamar al modelo, y permite descargar el PDF de ejemplo.

El módulo no usa base de datos ni implementa persistencia o exportación. El botón **Guardar Análisis** solo muestra un aviso de funcionalidad en desarrollo.

## Funcionamiento

1. `app.py` llama a `main()` de la interfaz de Streamlit.
2. La interfaz lee la configuración del modelo y comprueba la conexión. En el panel lateral muestra *Ollama conectado* o el problema detectado.
3. El usuario carga un PDF y escribe la descripción del puesto.
4. Al pulsar **Analizar Candidato**, la interfaz comprueba que existan ambas entradas y que el proveedor esté configurado.
5. `extraer_texto_pdf()` lee el archivo en memoria con PyPDF2, recorre sus páginas y concatena el texto con un separador por página. Si no hay texto o la lectura falla, devuelve un mensaje de error que la interfaz muestra antes de detener el proceso.
6. `crear_sistema_prompts()` combina las instrucciones del reclutador con el mensaje que contiene el CV y la descripción del puesto.
7. `crear_evaluador_cv()` crea el modelo del proveedor configurado con `temperature=0.2` y le aplica `with_structured_output(AnalisisCV, method="json_schema")`, de modo que la respuesta debe ajustarse al esquema Pydantic.
8. `evaluar_candidato()` invoca la cadena `chat_prompt | modelo_estructurado` y devuelve el análisis validado. Si algo falla, lanza `ErrorEvaluacion` con la causa original.
9. El resultado se guarda en `st.session_state` y la interfaz muestra el porcentaje de ajuste, el perfil del candidato, las habilidades, las fortalezas, las áreas de desarrollo y la recomendación final, junto con el archivo, el modelo y el tiempo empleado.

```
PDF ──> pdf_processor ──> texto del CV ─┐
                                        ├──> cv_prompts ──> modelo (Ollama/OpenAI) ──> AnalisisCV (Pydantic) ──> interfaz
Descripción del puesto ─────────────────┘
```

## Decisiones técnicas

### Qué se usa y por qué

| Componente | Uso | Motivo |
|---|---|---|
| Streamlit | Interfaz web | Permite construir la interfaz en Python con poco código; es adecuado para un prototipo centrado en la IA. |
| PyPDF2 | Extracción de texto | Lee PDF en memoria sin dependencias del sistema. |
| LangChain (`langchain-core`) | Plantilla de prompt y encadenamiento | `ChatPromptTemplate` separa instrucciones y datos; `prompt \| modelo` compone la cadena; el mismo código sirve para varios proveedores. |
| `with_structured_output` + Pydantic | Respuesta estructurada | El modelo responde con un JSON que debe cumplir el esquema `AnalisisCV`; Pydantic valida tipos y rangos (por ejemplo, porcentaje entre 0 y 100). |
| Ollama + `qwen2.5:7b` (`langchain-ollama`) | Modelo por defecto | Modelo local con buen rendimiento en español y en salida JSON, ejecutable en un equipo con 16 GB de RAM. |
| OpenAI `gpt-4o-mini` (`langchain-openai`) | Modelo alternativo | Más rápido y preciso cuando se acepta enviar datos a un servicio externo. |
| Variables de entorno | Configuración | Permiten cambiar de proveedor o de modelo sin modificar el código. |
| Docker | Ejecución reproducible | La aplicación se ejecuta igual en cualquier equipo con Docker. |
| Temperatura 0.2 | Parámetro del modelo | Reduce la variabilidad entre ejecuciones; para evaluar se prefiere estabilidad frente a creatividad. |

### Por qué un modelo local

- **Privacidad.** Un CV contiene datos personales (nombre, contacto, historial laboral). Con Ollama el texto se procesa en el propio equipo y no se envía a terceros, lo que facilita cumplir la normativa de protección de datos personales (en Colombia, la Ley 1581 de 2012).
- **Sin costo por uso.** No se paga por tokens ni se necesita una clave de API.
- **Funciona sin conexión** una vez descargado el modelo.
- **Sin dependencia de un proveedor.** Cambiar a OpenAI solo requiere `LLM_PROVIDER=openai`.

Contrapartidas: en un equipo sin GPU dedicada el análisis tarda entre 1 y 3 minutos (en las pruebas, entre 110 y 170 segundos, incluida la carga del modelo), frente a unos segundos con OpenAI. Un modelo de 7B también es menos preciso que uno comercial.

### Qué no se usa y por qué

| No se usa | Motivo |
|---|---|
| Base de datos | El alcance es analizar, no almacenar. PostgreSQL y pgAdmin aparecen en `docker-compose.yml` porque es el entorno compartido del repositorio, pero este módulo no los utiliza. |
| OCR | El alcance se limita a PDF con texto seleccionable. Un PDF escaneado produce un error explícito en lugar de un análisis sin datos. |
| RAG, embeddings o base vectorial | Un CV cabe completo en el contexto del modelo (`OLLAMA_NUM_CTX=8192`); fragmentarlo añadiría complejidad sin beneficio. |
| Ponderación calculada en el código | Los pesos se indican al modelo en el prompt y el porcentaje lo estima el modelo. Es una decisión de alcance; ver [Limitaciones](#limitaciones). |
| `load_dotenv()` | La configuración se toma del entorno del proceso. En Docker Compose, el `.env` se inyecta con `env_file`. |
| Procesamiento por lotes y autenticación | Fuera del alcance de esta versión. |

## Criterios de evaluación

El prompt solicita los siguientes pesos:

| Criterio | Peso solicitado |
|---|---|
| Experiencia relevante | 40 % |
| Habilidades técnicas | 35 % |
| Formación y certificaciones | 15 % |
| Coherencia profesional | 10 % |

El porcentaje lo genera el modelo a partir de estas instrucciones. El código no calcula una fórmula ponderada ni devuelve puntuaciones parciales por criterio.

La interfaz utiliza dos conjuntos de umbrales:

| Porcentaje | Evaluación principal |
|---|---|
| 80–100 | Excelente |
| 60–79 | Bueno |
| 40–59 | Regular |
| 0–39 | Bajo |

| Porcentaje | Recomendación final |
|---|---|
| 70–100 | Candidato recomendado |
| 50–69 | Candidato con potencial |
| 0–49 | Candidato no recomendado |

Por ejemplo, un resultado de 65 % aparece como *Bueno* en la evaluación principal y como *Candidato con potencial* en la recomendación final.

## Estructura

```
docker-base/
├── requirements.txt                 # Dependencias con versiones fijadas
├── Dockerfile                       # Imagen con Python 3.12 que arranca este módulo
├── docker-compose.yml               # Entorno compartido: app, PostgreSQL y pgAdmin
├── .env.example                     # Plantilla de variables de entorno
├── .gitignore
├── .dockerignore
└── app/intermedio/cv_analyzer/
    ├── README.md
    ├── app.py                       # Punto de entrada de Streamlit
    ├── .streamlit/
    │   └── config.toml              # Tema visual y opciones de Streamlit
    ├── ejemplos/
    │   ├── cv_ejemplo.pdf           # CV ficticio para pruebas y demostraciones
    │   └── analisis_ejemplo.json    # Resultado real del modelo sobre ese CV
    ├── models/
    │   └── cv_model.py              # Esquema Pydantic AnalisisCV
    ├── prompts/
    │   └── cv_prompts.py            # Instrucciones y plantilla de evaluación
    ├── services/
    │   ├── pdf_processor.py         # Extracción de texto del PDF
    │   └── cv_evaluator.py          # Configuración del proveedor e invocación del modelo
    └── ui/
        ├── streamlit_ui.py          # Páginas Analizador y Ejemplo: entradas, validaciones y presentación
        └── styles.py                # Estilos CSS y componentes HTML
```

Los directorios `__pycache__`, si aparecen, contienen archivos generados por Python y no forman parte de la lógica de la aplicación.

## Modelo de salida

Todos los campos de `AnalisisCV` son obligatorios:

| Campo | Tipo | Contenido |
|---|---|---|
| `nombre_candidato` | `str` | Nombre extraído del CV |
| `experiencia_años` | `int` | Años de experiencia relevante |
| `habilidades_clave` | `list[str]` | Habilidades relevantes para el puesto |
| `education` | `str` | Nivel educativo y especialización |
| `experiencia_relevante` | `str` | Resumen de la experiencia relacionada |
| `fortalezas` | `list[str]` | Fortalezas del candidato |
| `areas_mejora` | `list[str]` | Áreas de desarrollo |
| `porcentaje_ajuste` | `int` | Ajuste al puesto, validado entre 0 y 100 |

Las cantidades sugeridas de habilidades, fortalezas y áreas de mejora se describen en el esquema, pero no tienen restricciones de longitud implementadas.

## Requisitos

- Python 3.12 o superior (el Dockerfile usa 3.12; también se probó con 3.14).
- Para el modo por defecto: [Ollama](https://ollama.com) instalado y en ejecución, con el modelo descargado (unos 4.7 GB) y al menos 8 GB de RAM libres.
- Para el modo OpenAI: una clave de API con acceso al modelo configurado, cuota disponible y conexión a Internet.
- Un PDF con texto extraíble; no se implementa OCR para documentos escaneados.
- Docker, solo si se ejecuta en contenedor.

Dependencias directas (versiones fijadas en `requirements.txt`):

| Paquete | Versión |
|---|---|
| streamlit | 1.67.0 |
| PyPDF2 | 3.0.1 |
| langchain-core | 1.7.6 |
| langchain-ollama | 1.1.0 |
| langchain-openai | 1.7.4 |
| pydantic | 2.14.3 |

## Configuración

La aplicación se configura con variables de entorno. Todas tienen un valor por defecto salvo `OPENAI_API_KEY`.

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | Proveedor del modelo: `ollama` u `openai`. |
| `OLLAMA_MODEL` | `qwen2.5:7b` | Modelo de Ollama. |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Dirección del servidor de Ollama. En Docker se usa `http://host.docker.internal:11434`. |
| `OLLAMA_NUM_CTX` | `8192` | Tamaño del contexto en tokens. Evita que Ollama recorte CV largos sin avisar. |
| `OPENAI_MODEL` | `gpt-4o-mini` | Modelo de OpenAI. |
| `OPENAI_API_KEY` | (ninguno) | Obligatoria solo si `LLM_PROVIDER=openai`. |

La aplicación no llama a `load_dotenv()`: crear un archivo `.env` no basta para la ejecución local. Las variables deben estar definidas en la terminal que ejecuta Streamlit. No incluyas claves reales en archivos versionados; `.env` está en `.gitignore`.

## Ejecución local

Los comandos se ejecutan desde la raíz `docker-base/`, salvo donde se indica un cambio de directorio.

### 1. Preparar Ollama

Instala Ollama, ábrelo y descarga el modelo:

```bash
ollama pull qwen2.5:7b
ollama list
```

### 2. Crear un entorno e instalar dependencias

En Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Si PowerShell bloquea la activación, ejecuta antes `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

En macOS o Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. (Opcional) Usar OpenAI

En Windows PowerShell:

```powershell
$env:LLM_PROVIDER = "openai"
$env:OPENAI_API_KEY = "tu_clave_de_openai"
```

En macOS o Linux:

```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY="tu_clave_de_openai"
```

### 4. Iniciar Streamlit

```bash
cd app/intermedio/cv_analyzer
python -m streamlit run app.py --server.port=8501
```

Abre http://localhost:8501/. El panel lateral debe mostrar *Ollama conectado*. Para detener la aplicación, pulsa `Ctrl + C` en la terminal.

Ejecutar desde esta carpeta permite resolver los imports locales `ui`, `services`, `models` y `prompts`, y cargar el tema de `.streamlit/config.toml`.

## Ejecución con Docker

El contenedor no incluye Ollama: se conecta al Ollama del equipo anfitrión mediante `host.docker.internal`. Ollama debe estar abierto antes de iniciar el contenedor.

### Contenedor independiente

Desde `docker-base/`:

```bash
docker build -t cv-analyzer .
docker run --rm -p 8501:8501 cv-analyzer
```

Abre http://localhost:8501/. El Dockerfile ya arranca este módulo y define `LLM_PROVIDER=ollama` y `OLLAMA_BASE_URL=http://host.docker.internal:11434`. En Linux añade `--add-host=host.docker.internal:host-gateway` y configura Ollama para escuchar en una interfaz accesible desde Docker (`OLLAMA_HOST=0.0.0.0`).

Para usar OpenAI:

```bash
docker run --rm -p 8501:8501 -e LLM_PROVIDER=openai -e OPENAI_API_KEY cv-analyzer
```

Si modificas el código, vuelve a ejecutar `docker build` para actualizar la imagen.

### Entorno Docker Compose del repositorio

`docker-compose.yml` inicia el entorno de desarrollo compartido. El servicio `app` ejecuta `sleep infinity` y monta el repositorio como volumen, por lo que es necesario iniciar Streamlit de forma explícita.

1. Copia `.env.example` como `.env` y completa los valores. Las variables de PostgreSQL y pgAdmin son obligatorias para este Compose, aunque el analizador no las utiliza:
   - `POSTGRES_USER`, `POSTGRES_PASSWORD` y `POSTGRES_DB`.
   - `PGADMIN_DEFAULT_EMAIL` y `PGADMIN_DEFAULT_PASSWORD`.
   - `PGADMIN_SERVERS_JSON`, con la configuración JSON de servidores que se monta en pgAdmin como `servers.json`.
   - `POSTGRES_PORT` y `PGADMIN_PORT` son opcionales (por defecto 5433 y 5050).
2. Levanta el entorno e inicia Streamlit:

```bash
docker compose up -d --build
docker compose exec -w /app/app/intermedio/cv_analyzer app \
  python -m streamlit run app.py --server.address=0.0.0.0 --server.port=8501
```

Abre http://localhost:8501/. Compose inyecta las variables del `.env` en el servicio `app` mediante `env_file` y fija `OLLAMA_BASE_URL` para llegar al Ollama del anfitrión. Si cambias el `.env` después de crear el contenedor, recréalo para actualizar su entorno.

Para detener el entorno:

```bash
docker compose down
```

## Uso

1. Carga un CV en PDF con texto seleccionable (paso 1).
2. Escribe el puesto, la experiencia requerida, las habilidades obligatorias y deseables y las responsabilidades (paso 2), o pulsa **Usar descripción de ejemplo**.
3. Pulsa **Analizar Candidato** y espera la respuesta del modelo. Con Ollama en CPU puede tardar unos minutos.
4. Revisa el porcentaje de ajuste, el perfil, las habilidades, las fortalezas y las áreas de desarrollo junto con la recomendación final.
5. Pulsa **Limpiar** para borrar el PDF, la descripción y el resultado.

### CV de ejemplo

La carpeta `ejemplos/` contiene un CV ficticio (`cv_ejemplo.pdf`, candidata *Laura Gómez Rojas*, perfil de desarrolladora backend Python) y el resultado real que generó `qwen2.5:7b` al analizarlo con la descripción de ejemplo: 82 %, *Excelente* y *Candidato recomendado*.

- La pestaña **Ejemplo** muestra ese resultado al instante y permite descargar el PDF. Es útil en una demostración: mientras el análisis en vivo se ejecuta en la pestaña **Analizador**, el resultado ya está disponible en la otra pestaña.
- Para repetir el análisis en vivo, sube `ejemplos/cv_ejemplo.pdf` en la pestaña **Analizador** y pulsa **Usar descripción de ejemplo**. El porcentaje puede variar unos puntos entre ejecuciones.
- El resultado guardado no se regenera automáticamente. Si cambias el prompt o el modelo, `analisis_ejemplo.json` reflejará la versión con la que se generó (el modelo y la fecha aparecen en la propia pestaña).

Ejemplo de descripción:

```
Puesto: Desarrollador Python
Requisitos obligatorios: 3 años de experiencia, Python, APIs REST y PostgreSQL.
Deseables: Docker, pruebas automatizadas y experiencia con LangChain.
Responsabilidades: desarrollar servicios, integrar APIs y mantener pruebas.
```

## Cambios respecto al código base

| Problema original | Solución |
|---|---|
| El bloque `except` de `services/cv_evaluator.py` construía `AnalisisCV` con `fotalezas` y `porcetaje_ajuste`; el resultado alternativo fallaba y el error original se perdía. | Se eliminó el análisis alternativo. Ahora se registra el error con `logging` y se lanza `ErrorEvaluacion` con la causa real, que la interfaz muestra junto con una sugerencia según el proveedor. |
| El botón **Limpiar** solo llamaba a `st.rerun()` y no borraba los campos. | Borra el PDF cargado, la descripción y el último análisis. |
| El resultado no se conservaba en `st.session_state` y desaparecía con cualquier interacción. | Se guarda en `st.session_state`; pulsar **Guardar Análisis** ya no lo borra. |
| Sin clave de OpenAI el error aparecía solo al analizar. | La configuración se valida antes de llamar al modelo y el estado se muestra en el panel lateral. |
| Solo admitía OpenAI. | Se añadió Ollama como proveedor por defecto, seleccionable con `LLM_PROVIDER`. |
| El `CMD` del Dockerfile apuntaba a `app/main.py`, que no existe en este proyecto. | El `CMD` arranca directamente este módulo. |
| Dependencias sin versión fijada. | Versiones fijadas en `requirements.txt`. |

## Limitaciones

- **Evaluación generativa.** El porcentaje y las observaciones proceden del modelo y pueden variar entre ejecuciones. El modelo puede equivocarse (por ejemplo, señalar como ausente una habilidad que el CV sí menciona). La aplicación es una herramienta de apoyo: la decisión de contratación debe tomarla una persona.
- **Sesgos.** El modelo puede reproducir sesgos presentes en sus datos de entrenamiento.
- **Velocidad en local.** Sin GPU dedicada, un análisis con `qwen2.5:7b` tarda entre 1 y 3 minutos.
- **Sin OCR.** Un PDF compuesto solo por imágenes no puede analizarse; el error se muestra en la interfaz.
- **Sin almacenamiento.** El resultado vive en la sesión del navegador; al recargar la página se pierde.
- **Sin procesamiento por lotes.** Se analiza un CV por operación.
- **Sin segmentación de documentos.** El texto completo del CV se envía en una sola invocación. Con Ollama el contexto está limitado por `OLLAMA_NUM_CTX`; un documento muy largo puede recortarse.
- **Privacidad con OpenAI.** Si `LLM_PROVIDER=openai`, el texto del CV y la descripción del puesto se envían a OpenAI.

## Resolución de problemas

| Síntoma | Qué revisar |
|---|---|
| El panel lateral muestra *Ollama no responde* | Abre Ollama y comprueba `ollama list`. Verifica `OLLAMA_BASE_URL`. Pulsa **Volver a comprobar**. |
| El panel lateral pide `ollama pull` | Descarga el modelo indicado en `OLLAMA_MODEL`. |
| El análisis tarda varios minutos | Es normal con un modelo local en CPU. Puedes usar un modelo más pequeño (`OLLAMA_MODEL=qwen2.5:3b`, tras `ollama pull qwen2.5:3b`) o OpenAI. |
| No encuentra `streamlit` u otro paquete | Activa el entorno virtual e instala `requirements.txt` con el mismo intérprete que ejecuta la aplicación. |
| No encuentra `ui`, `services`, `models` o `prompts` | Ejecuta el comando desde `app/intermedio/cv_analyzer/`. |
| Falla el análisis o aparece un error de validación | Lee el mensaje de error que muestra la interfaz. Con OpenAI, comprueba `OPENAI_API_KEY`, la conectividad, el acceso al modelo y la cuota. |
| El PDF aparece vacío o no puede procesarse | Usa un PDF con texto seleccionable y verifica que el archivo se abra correctamente. |
| El contenedor no llega a Ollama | Comprueba que Ollama esté abierto en el anfitrión. En Linux, revisa `--add-host` y `OLLAMA_HOST`. |
| Compose exige variables de PostgreSQL o pgAdmin | Completa el `.env` a partir de `.env.example` o usa el contenedor independiente. |
| Compose falla con *port is already allocated* en 5433 o 5050 | Otro contenedor usa ese puerto. Cambia `POSTGRES_PORT` o `PGADMIN_PORT` en el `.env` (por ejemplo, `55433` y `55050`). |
| El puerto 8501 está ocupado | En local, usa otro `--server.port`; con Docker, cambia el puerto del anfitrión, por ejemplo `-p 8502:8501`. |

## Enlaces de la aplicación

Con la aplicación en ejecución (en local o con Docker), abre estos enlaces en el navegador:

| Página | Enlace | Contenido |
|---|---|---|
| Analizador | [http://localhost:8501/](http://localhost:8501/) | Carga de un CV y análisis en vivo con el modelo. |
| Ejemplo | [http://localhost:8501/ejemplo](http://localhost:8501/ejemplo) | Análisis de ejemplo ya generado y descarga del CV ficticio. |

Solo con Docker Compose (usa el puerto definido en `PGADMIN_PORT` si lo cambiaste):

| Servicio | Enlace |
|---|---|
| pgAdmin | [http://localhost:5050/](http://localhost:5050/) |

Servicio local que usa la aplicación:

| Servicio | Enlace | Uso |
|---|---|---|
| API de Ollama | [http://localhost:11434/api/tags](http://localhost:11434/api/tags) | Lista los modelos descargados; sirve para comprobar que Ollama está en ejecución. |
