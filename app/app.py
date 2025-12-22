"""
Prototipo de juego ciencia política

"""

import streamlit as st
import requests
import json
from pathlib import Path
import sys
import pandas as pd

# Agregar el directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models import Evaluacion, Equipo
from app.events import obtener_evento, EVENTOS
from app.prompts import SYSTEM_PROMPT, construir_prompt_usuario, extraer_json_de_respuesta
from app.storage import guardar_evaluacion, cargar_evaluaciones, obtener_ranking


# ============================================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================================

st.set_page_config(
    page_title="Juego de Campaña Política",
    page_icon="🏛️",
    layout="wide"
)


# ============================================================================
# THEME UI - IDENTIDAD VISUAL "CIUDAD ORIENTAL"
# ============================================================================

# Colores de partidos
COLORES_PARTIDO = {
    "Partido Progresista": "#8B1E3F",  # borgoña
    "Partido Conservador": "#0033A0",   # azul
}

# Helpers UI
def party_color(partido: str) -> str:
    """Retorna el color del partido o gris por defecto."""
    return COLORES_PARTIDO.get(partido, "#444444")

def severity_color(severidad: str) -> str:
    """Retorna color según severidad de escándalo."""
    colors = {
        "Baja": "#F2C94C",
        "Media": "#F2994A",
        "Alta": "#EB5757"
    }
    return colors.get(severidad, "#999999")

def card(title: str, body_html: str, border_color: str = "#DDDDDD", icon: str = "") -> None:
    """Renderiza una card con título, cuerpo HTML y borde izquierdo coloreado."""
    st.markdown(
        f"""
        <div class="co-card" style="border-left: 8px solid {border_color};">
          <div class="co-card-title">{icon} {title}</div>
          <div class="co-card-body">{body_html}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def badge(text: str, color: str = "#444444") -> str:
    """Retorna HTML de un badge."""
    return f'<span class="co-badge" style="border-color:{color};">{text}</span>'

def headline(text: str) -> None:
    """Renderiza un titular grande estilo diario."""
    st.markdown(f'<div class="co-headline">{text}</div>', unsafe_allow_html=True)

def score_bar_html(label: str, value: int, max_value: int = 20) -> str:
    """Retorna HTML de una barra horizontal de score."""
    percentage = (value / max_value) * 100
    color = "#27AE60" if value >= 15 else "#F2994A" if value >= 10 else "#EB5757"
    return f"""
    <div style="margin-bottom: 8px;">
      <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
        <span style="font-weight: 600; font-size: 0.9rem;">{label}</span>
        <span style="font-weight: 800; color: {color};">{value}/{max_value}</span>
      </div>
      <div style="background: rgba(0,0,0,0.06); border-radius: 8px; height: 8px; overflow: hidden;">
        <div style="background: {color}; width: {percentage}%; height: 100%; transition: width 0.3s;"></div>
      </div>
    </div>
    """

def score_bar(label: str, value: int, max_value: int = 20) -> None:
    """Renderiza una barra horizontal de score."""
    st.markdown(score_bar_html(label, value, max_value), unsafe_allow_html=True)

# CSS Theme
st.markdown("""
<style>
/* Page Layout */
.block-container { 
    padding-top: 1.2rem; 
    padding-bottom: 2rem; 
    max-width: 1400px; 
}

/* Typography */
h1, h2, h3 { 
    letter-spacing: -0.02em; 
    font-weight: 800;
}
.small-muted { 
    color: rgba(0,0,0,0.55); 
    font-size: 0.92rem; 
}

/* Cards */
.co-card {
    background: #FFFFFF;
    border: 1px solid rgba(0,0,0,0.06);
    border-radius: 14px;
    padding: 16px 18px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.06);
    margin: 12px 0 16px 0;
}
.co-card-title {
    font-weight: 800;
    font-size: 1.05rem;
    margin-bottom: 10px;
    color: #111;
}
.co-card-body { 
    font-size: 0.98rem; 
    line-height: 1.5rem; 
    color: #333;
}

/* Badges */
.co-badge {
    display: inline-block;
    padding: 5px 12px;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 700;
    border: 1.5px solid rgba(0,0,0,0.12);
    background: rgba(0,0,0,0.02);
    margin-right: 8px;
    margin-bottom: 6px;
}

/* Headline (titular grande) */
.co-headline {
    padding: 14px 18px;
    border-radius: 14px;
    border: 1px solid rgba(0,0,0,0.08);
    background: linear-gradient(180deg, rgba(0,0,0,0.02), rgba(0,0,0,0.00));
    font-weight: 900;
    font-size: 1.3rem;
    margin: 12px 0 16px 0;
    line-height: 1.4;
}

/* Score Pill */
.co-pill {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 12px;
    border: 1px solid rgba(0,0,0,0.10);
    background: #fff;
    font-weight: 800;
    font-size: 0.9rem;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #f8f9fa;
}
</style>
""", unsafe_allow_html=True)


# ============================================================================
# INICIALIZACIÓN DE ESTADO
# ============================================================================

if 'evaluaciones' not in st.session_state:
    st.session_state.evaluaciones = cargar_evaluaciones()

if 'ranking_previo' not in st.session_state:
    st.session_state.ranking_previo = None

if 'pagina_actual' not in st.session_state:
    st.session_state.pagina_actual = "Juego"


# ============================================================================
# DATOS INICIALES
# ============================================================================

# Incorporar en el futuro la posibilidad de que sean generado por los jugadores los perfiles

EQUIPOS_INICIALES = [
    Equipo(
        nombre="Equipo 1",
        partido="Partido Progresista",
        candidato="Ana Martínez",
        perfil="Ex intendente, 15 años en política, perfil moderado"
    ),
    Equipo(
        nombre="Equipo 2",
        partido="Partido Progresista",
        candidato="Carlos Ramírez",
        perfil="Diputado joven, perfil más radical, redes sociales fuertes"
    ),
    Equipo(
        nombre="Equipo 3",
        partido="Partido Conservador",
        candidato="María Fernández",
        perfil="Senadora experimentada, perfil conservador, base rural"
    ),
    Equipo(
        nombre="Equipo 4",
        partido="Partido Conservador",
        candidato="Juan López",
        perfil="Empresario, primera vez en política, perfil técnico"
    )
]

FORMATOS_ENTREGA = {
    "Afiche (slogan + promesa)": {
        "campos": {
            "slogan": {"label": "Slogan", "max_chars": 60},
            "propuesta": {"label": "Propuesta", "max_chars": 220}
        }
    },
    "Discurso (apertura + 3 ejes + cierre)": {
        "campos": {
            "apertura": {"label": "Apertura", "max_chars": 220},
            "ejes": {"label": "3 Ejes", "max_chars": 420},
            "cierre": {"label": "Cierre", "max_chars": 180}
        }
    },
    "Crisis (qué decís + qué hacés)": {
        "campos": {
            "declaracion": {"label": "Qué decís", "max_chars": 220},
            "accion": {"label": "Qué hacés", "max_chars": 220}
        }
    },
    "Ataque/Defensa (1 línea)": {
        "campos": {
            "linea": {"label": "Línea", "max_chars": 180}
        }
    }
}


# ============================================================================
# SIDEBAR - NAVEGACIÓN Y CONFIGURACIÓN
# ============================================================================

with st.sidebar:
    st.title("Versión piloto")
    st.caption("Juego de Campaña Política")
    
    # Modo proyector
    modo_proyector = st.toggle("Modo Proyector", value=False, help="Pantalla limpia para aula, sin inputs")
    
    st.divider()
    
    # Navegación principal
    opciones_nav = [
        "Juego",
        "Pantalla",
        "Ranking",
        "Noticiero",
        "Rúbrica",
        "Configuración"
    ]
    
    # Si modo proyector, forzar a Pantalla
    if modo_proyector:
        pagina_seleccionada = "Pantalla"
    else:
        pagina_seleccionada = st.radio(
            "Navegación",
            options=opciones_nav,
            index=opciones_nav.index(st.session_state.pagina_actual) if st.session_state.pagina_actual in opciones_nav else 0,
            label_visibility="collapsed"
        )
    
    st.session_state.pagina_actual = pagina_seleccionada
    
    st.divider()
    
    # Configuración de etapa/ronda
    st.subheader("Ronda Actual")
    etapa = st.selectbox(
        "Etapa",
        ["Internas", "Nacional"],
        help="Etapa actual del juego"
    )
    
    ronda = st.selectbox(
        "Ronda",
        ["R1", "R2", "R3", "R4", "Cierre"],
        help="Ronda actual"
    )
    
    # Información del evento
    try:
        evento = obtener_evento(ronda)
        st.info(f"**{evento['titulo']}**\n\n{evento['tipo_entrega']}")
    except ValueError as e:
        st.error(str(e))
        evento = None
    
    # Configuración técnica (solo si no es modo proyector)
    if not modo_proyector and pagina_seleccionada == "Configuración":
        st.divider()
        st.subheader("Configuración Técnica")
        modelo_ollama = st.text_input(
            "Modelo Ollama",
            value="qwen2.5:3b-instruct",
            help="Nombre del modelo local configurado en Ollama"
        )
        url_ollama = st.text_input(
            "URL Ollama",
            value="http://localhost:11434/api/generate",
            help="URL del endpoint de generación de Ollama"
        )
    else:
        # Valores por defecto para modo proyector
        modelo_ollama = "qwen2.5:3b-instruct"
        url_ollama = "http://localhost:11434/api/generate"


# ============================================================================
# VALIDACIÓN DE EVENTO
# ============================================================================

if evento is None:
    st.error("Error al cargar el evento. Por favor, selecciona una ronda válida en el sidebar.")
    st.stop()


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def obtener_equipos_evaluados_ronda(evaluaciones: list, ronda: str) -> set:
    """Retorna set de candidatos que ya evaluaron en esta ronda."""
    return {e.equipo for e in evaluaciones if e.ronda == ronda}

def obtener_siguiente_equipo_sugerido(evaluaciones: list, ronda: str) -> Equipo:
    """Retorna el primer equipo que aún no evaluó en esta ronda."""
    evaluados = obtener_equipos_evaluados_ronda(evaluaciones, ronda)
    for equipo in EQUIPOS_INICIALES:
        if equipo.candidato not in evaluados:
            return equipo
    return EQUIPOS_INICIALES[0]  # Si todos evaluaron, retorna el primero

def calcular_delta_ranking(ranking_actual: list, ranking_previo: list) -> dict:
    """Calcula deltas de posición entre rankings."""
    deltas = {}
    if ranking_previo:
        # Crear dict de posiciones previas
        posiciones_previas = {}
        for i, pos in enumerate(ranking_previo, 1):
            equipo = pos.get('equipo', '')
            posiciones_previas[equipo] = i
        
        # Calcular deltas
        for i, pos in enumerate(ranking_actual, 1):
            equipo = pos.get('equipo', '')
            pos_prev = posiciones_previas.get(equipo, i)
            delta = pos_prev - i  # Positivo si subió, negativo si bajó
            deltas[equipo] = delta
    return deltas

def test_conexion_ollama(url: str, modelo: str) -> tuple[bool, str]:
    """Prueba la conexión con Ollama."""
    try:
        payload = {
            "model": modelo,
            "prompt": "test",
            "stream": False,
            "options": {"num_predict": 5}
        }
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        return True, "✅ Conexión exitosa"
    except requests.exceptions.RequestException as e:
        return False, f"❌ Error: {str(e)}"


# ============================================================================
# PANTALLAS PRINCIPALES
# ============================================================================

# ========== PANTALLA: PROYECTOR ==========
if pagina_seleccionada == "Pantalla" or modo_proyector:
    st.title("Pantalla de Resultados")
    st.markdown('<div class="small-muted">Modo proyector: ranking, titulares y shocks en vivo.</div>', unsafe_allow_html=True)
    
    ranking = obtener_ranking(st.session_state.evaluaciones)
    
    if not ranking:
        card("Aún no hay resultados", "Realicen la primera entrega y evalúen con el GM.", border_color="#999999")
        st.stop()
    
    # Top 4 Ranking
    html_ranking = ""
    for i, pos in enumerate(ranking[:4], 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🎯"
        col = party_color(pos.get("partido", ""))
        html_ranking += f"""
        <div style="display:flex; justify-content:space-between; align-items:center; padding:12px 0; border-bottom:1px solid rgba(0,0,0,0.06);">
          <div>
            {badge(f"{medal} {i}°", col)}
            <span style="font-weight:900; font-size:1.1rem;">{pos.get('equipo','')}</span>
            <span class="small-muted">({pos.get('partido','')})</span>
          </div>
          <div><span class="co-pill">{pos.get('total_acumulado',0)} pts</span></div>
        </div>
        """
    card("📊 Ranking Acumulado (Top 4)", html_ranking, border_color="#111111")
    
    # Última evaluación
    if st.session_state.evaluaciones:
        ultima = st.session_state.evaluaciones[-1]
        colp = party_color(ultima.partido)
        
        headline(f"📰 {ultima.titular}")
        
        # Badges de contexto
        shock_color = "#27AE60" if ultima.shock_opinion_publica > 0 else "#EB5757" if ultima.shock_opinion_publica < 0 else "#999999"
        st.markdown(
            f"""
            {badge(f"👤 {ultima.candidato}", colp)}
            {badge(f"🗳️ {ultima.etapa} — {ultima.ronda}")}
            {badge(f"🎲 Shock: {ultima.shock_opinion_publica:+d}", shock_color)}
            {badge(f"✅ Total: {ultima.total_final}", "#27AE60" if ultima.total_final >= 80 else "#F2994A" if ultima.total_final >= 60 else "#EB5757")}
            """,
            unsafe_allow_html=True
        )
        
        # Barras de scores
        scores_html = ""
        scores_html += score_bar_html("Claridad", ultima.scores.claridad)
        scores_html += score_bar_html("Estrategia", ultima.scores.estrategia)
        scores_html += score_bar_html("Credibilidad", ultima.scores.credibilidad)
        scores_html += score_bar_html("Emoción/Identidad", ultima.scores.emocion_identidad)
        scores_html += score_bar_html("Riesgo/Backlash", ultima.scores.riesgo_backlash)
        card("📊 Dimensiones", scores_html, border_color=colp)
        
        # Escándalo
        if ultima.escandalo.visible:
            sev = ultima.escandalo.severidad
            sev_color = severity_color(sev)
            card("🚨 Escándalo", f"<b>{sev}</b>: {ultima.escandalo.motivo}", border_color=sev_color)
        
        # Devolución
        card("💬 Devolución de la ciudadanía", ultima.devolucion_gm.replace("\n", "<br/>"), border_color=colp)
        
        # Ticker: últimas 5 evaluaciones
        if len(st.session_state.evaluaciones) > 1:
            ticker_html = ""
            for eval_item in st.session_state.evaluaciones[-5:][::-1]:
                ticker_col = party_color(eval_item.partido)
                ticker_html += f"""
                <div style="padding: 8px 0; border-bottom: 1px solid rgba(0,0,0,0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            {badge(f"{eval_item.etapa} — {eval_item.ronda}", ticker_col)}
                            <strong>{eval_item.candidato}</strong>
                            <span class="small-muted">({eval_item.partido})</span>
                        </div>
                        <div>
                            <span class="co-pill">{eval_item.total_final} pts</span>
                            {f'<span style="color: {shock_color}; font-weight: 700; margin-left: 8px;">{eval_item.shock_opinion_publica:+d}</span>' if eval_item.shock_opinion_publica != 0 else ''}
                        </div>
                    </div>
                    <div style="margin-top: 4px; font-size: 0.9rem; color: #555;">{eval_item.titular[:80]}...</div>
                </div>
                """
            card("📰 Ticker — Últimas jugadas", ticker_html, border_color="#666666")
    
    st.stop()


# ========== PANTALLA: JUEGO (TURNOS) ==========
if pagina_seleccionada == "Juego":
    st.title("Juego — Turnos")
    
    # Estado de la ronda
    evaluaciones_ronda = [e for e in st.session_state.evaluaciones if e.ronda == ronda]
    equipos_evaluados = obtener_equipos_evaluados_ronda(st.session_state.evaluaciones, ronda)
    total_equipos = len(EQUIPOS_INICIALES)
    entregas_evaluadas = len(evaluaciones_ronda)
    progreso = entregas_evaluadas / total_equipos if total_equipos > 0 else 0
    
    estado_html = f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <div>
            <strong>{etapa}</strong> — <strong>{ronda}</strong><br/>
            <span class="small-muted">{evento['titulo']}</span>
        </div>
        <div style="text-align: right;">
            <strong>{entregas_evaluadas}/{total_equipos}</strong> entregas<br/>
            <span class="small-muted">Progreso de ronda</span>
        </div>
    </div>
    """
    st.progress(progreso)
    card("Estado de la Ronda", estado_html, border_color="#111111")
    
    # Siguiente equipo sugerido
    siguiente = obtener_siguiente_equipo_sugerido(st.session_state.evaluaciones, ronda)
    card(
        "Siguiente Equipo",
        f"<strong>{siguiente.candidato}</strong> ({siguiente.partido})<br/><span class='small-muted'>{siguiente.perfil}</span>",
        border_color=party_color(siguiente.partido),
        icon="➡️"
    )
    
    st.divider()
    
    # Turno del equipo
    st.subheader("Turno del Equipo")
    
    # Selección de equipo
    equipo_seleccionado = st.selectbox(
        "Equipo",
        options=range(len(EQUIPOS_INICIALES)),
        format_func=lambda i: f"{EQUIPOS_INICIALES[i].nombre} - {EQUIPOS_INICIALES[i].candidato} ({EQUIPOS_INICIALES[i].partido})",
        help="Selecciona el equipo que presenta la entrega"
    )
    
    equipo = EQUIPOS_INICIALES[equipo_seleccionado]
    col_equipo = party_color(equipo.partido)
    
    # Card de información del equipo
    equipo_html = f"""
    <div>
        <strong>Partido:</strong> {equipo.partido}<br/>
        <strong>Candidato:</strong> {equipo.candidato}<br/>
        <strong>Perfil:</strong> {equipo.perfil}
    </div>
    """
    card("Información del Equipo", equipo_html, border_color=col_equipo)
    
    # Contexto del evento
    card("Contexto del Evento", evento['descripcion'], border_color="#666666")
    
    # Situación interna
    situacion_interna = st.text_area(
        "Situación Interna del Partido",
        value="Tensiones entre corrientes históricas y nuevas generaciones.",
        help="Describe la situación interna actual del partido",
        height=100
    )
    
    # Tablero de campaña
    st.subheader("Tablero de Campaña")
    col1, col2 = st.columns(2)
    with col1:
        segmento = st.selectbox(
            "Segmento objetivo",
            ["Jóvenes urbanos", "Clase media metropolitana", "Interior / rural", "Trabajadores formales", "Indecisos moderados"],
            help="Segmento objetivo de la campaña"
        )
        tono = st.selectbox(
            "Tono",
            ["Positivo (propuesta)", "Contraste (comparación)", "Duro (mano firme)", "Empático (cercanía)"],
            help="Tono comunicacional"
        )
    with col2:
        canal = st.selectbox(
            "Canal",
            ["Acto partidario", "Redes sociales", "Radio", "Puerta a puerta", "TV"],
            help="Canal de comunicación"
        )
        alianza_interna = st.selectbox(
            "Alianza interna",
            ["Históricos", "Nuevas generaciones", "Unidad (mix)", "Neutral (evita interna)"],
            help="Estrategia de alianza interna"
        )
    
    tablero = {
        "segmento": segmento,
        "tono": tono,
        "canal": canal,
        "alianza_interna": alianza_interna
    }
    
    # Sistema de formatos de entrega
    st.subheader(f"Entrega: {evento['tipo_entrega']}")
    
    # Determinar formato sugerido
    tipo_lower = evento['tipo_entrega'].lower()
    formato_default = "Ataque/Defensa (1 línea)"
    if "discurso" in tipo_lower:
        formato_default = "Discurso (apertura + 3 ejes + cierre)"
    elif "afiche" in tipo_lower:
        formato_default = "Afiche (slogan + promesa)"
    elif "crisis" in tipo_lower:
        formato_default = "Crisis (qué decís + qué hacés)"
    
    formato_seleccionado = st.selectbox(
        "Formato",
        options=list(FORMATOS_ENTREGA.keys()),
        index=list(FORMATOS_ENTREGA.keys()).index(formato_default) if formato_default in FORMATOS_ENTREGA else 0,
        help="Selecciona el formato de entrega"
    )
    
    # Campos dinámicos según formato
    campos_entrega = {}
    formato_config = FORMATOS_ENTREGA[formato_seleccionado]
    
    for campo_key, campo_info in formato_config["campos"].items():
        max_chars = campo_info["max_chars"]
        label = campo_info["label"]
        texto = st.text_area(
            f"{label} (máx. {max_chars} caracteres)",
            key=f"entrega_{campo_key}",
            help=f"Máximo {max_chars} caracteres",
            height=100 if max_chars > 200 else 60
        )
        chars_actuales = len(texto)
        if chars_actuales > max_chars:
            st.error(f"⚠️ {chars_actuales}/{max_chars} caracteres (excede el límite)")
        else:
            st.caption(f"{chars_actuales}/{max_chars} caracteres")
        campos_entrega[campo_key] = texto
    
    # Construir entrega_textual
    partes_entrega = []
    for campo_key, texto in campos_entrega.items():
        if texto.strip():
            label = formato_config["campos"][campo_key]["label"]
            partes_entrega.append(f"{label}: {texto.strip()}")
    
    entrega_textual = "\n\n".join(partes_entrega) if partes_entrega else ""
    
    # Botones de acción
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        evaluar = st.button("Enviar a la ciudadanía", type="primary", use_container_width=True)
    with col2:
        if st.button("🔄 Limpiar", use_container_width=True):
            st.rerun()
    
    # Procesamiento de evaluación
    if evaluar:
        errores = []
        
        if not entrega_textual.strip():
            errores.append("⚠️ Por favor, completa al menos un campo de la entrega.")
        
        for campo_key, texto in campos_entrega.items():
            max_chars = formato_config["campos"][campo_key]["max_chars"]
            if len(texto) > max_chars:
                label = formato_config["campos"][campo_key]["label"]
                errores.append(f"⚠️ El campo '{label}' excede el límite de {max_chars} caracteres ({len(texto)} caracteres).")
        
        if errores:
            errores_html = "<br/>".join(errores)
            card("❌ Errores de Turno", errores_html, border_color="#EB5757")
        else:
            # Guardar ranking previo antes de agregar nueva evaluación
            ranking_actual = obtener_ranking(st.session_state.evaluaciones)
            st.session_state.ranking_previo = ranking_actual
            
            with st.spinner("La ciudadanía está evaluando..."):
                try:
                    prompt_usuario = construir_prompt_usuario(
                        etapa=etapa,
                        ronda=ronda,
                        evento=evento,
                        partido=equipo.partido,
                        candidato=equipo.candidato,
                        perfil=equipo.perfil,
                        situacion_interna=situacion_interna,
                        entrega_textual=entrega_textual,
                        tablero=tablero,
                        formato=formato_seleccionado
                    )
                    
                    payload = {
                        "model": modelo_ollama,
                        "prompt": f"{SYSTEM_PROMPT}\n\n{prompt_usuario}",
                        "stream": False,
                        "options": {
                            "temperature": 0.5,
                            "num_predict": 1000
                        }
                    }
                    
                    response = requests.post(url_ollama, json=payload, timeout=300)
                    response.raise_for_status()
                    
                    respuesta_llm = response.json().get('response', '')
                    
                    if not respuesta_llm:
                        st.error("❌ El LLM no devolvió respuesta.")
                    else:
                        json_str = extraer_json_de_respuesta(respuesta_llm)
                        evaluacion = Evaluacion.from_json(json_str)
                        
                        st.session_state.evaluaciones.append(evaluacion)
                        log_file = guardar_evaluacion(
                            evaluacion=evaluacion,
                            prompt_completo=f"{SYSTEM_PROMPT}\n\n{prompt_usuario}",
                            respuesta_llm=respuesta_llm,
                            modelo_usado=modelo_ollama
                        )
                        
                        st.success(f"✅ Evaluación completada. Guardada en {log_file}")
                        st.rerun()
                
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Error de conexión con Ollama: {e}")
                    st.info("💡 Asegúrate de que Ollama esté corriendo y el modelo esté disponible.")
                except json.JSONDecodeError as e:
                    st.error(f"❌ Error al parsear JSON del LLM: {e}")
                    with st.expander("🔍 Ver respuesta del LLM"):
                        st.text(respuesta_llm)
                except ValueError as e:
                    st.error(f"❌ Error de validación: {e}")
                    with st.expander("🔍 Ver respuesta del LLM"):
                        st.text(respuesta_llm if 'respuesta_llm' in locals() else "No disponible")
                except Exception as e:
                    st.error(f"❌ Error inesperado: {e}")
                    st.exception(e)
    
    # Mostrar última evaluación si existe y es de este equipo/ronda
    if st.session_state.evaluaciones:
        ultima = st.session_state.evaluaciones[-1]
        if ultima.equipo == equipo.candidato and ultima.ronda == ronda:
            st.divider()
            st.subheader("📊 Resultado del Turno")
            
            colp = party_color(ultima.partido)
            headline(f"📰 {ultima.titular}")
            
            # Badges
            shock_color = "#27AE60" if ultima.shock_opinion_publica > 0 else "#EB5757" if ultima.shock_opinion_publica < 0 else "#999999"
            st.markdown(
                f"""
                {badge(f"👤 {ultima.candidato}", colp)}
                {badge(f"🗳️ {ultima.etapa} — {ultima.ronda}")}
                {badge(f"🎲 Shock: {ultima.shock_opinion_publica:+d}", shock_color)}
                {badge(f"✅ Total: {ultima.total_final}", "#27AE60" if ultima.total_final >= 80 else "#F2994A" if ultima.total_final >= 60 else "#EB5757")}
                """,
                unsafe_allow_html=True
            )
            
            # Barras de scores
            scores_html = ""
            scores_html += score_bar_html("Claridad", ultima.scores.claridad)
            scores_html += score_bar_html("Estrategia", ultima.scores.estrategia)
            scores_html += score_bar_html("Credibilidad", ultima.scores.credibilidad)
            scores_html += score_bar_html("Emoción/Identidad", ultima.scores.emocion_identidad)
            scores_html += score_bar_html("Riesgo/Backlash", ultima.scores.riesgo_backlash)
            card("📊 Dimensiones", scores_html, border_color=colp)
            
            # Escándalo
            if ultima.escandalo.visible:
                sev = ultima.escandalo.severidad
                sev_color = severity_color(sev)
                card("🚨 Escándalo", f"<b>{sev}</b>: {ultima.escandalo.motivo}", border_color=sev_color)
            
            # Devolución
            card("💬 Devolución de la ciudadanía", ultima.devolucion_gm.replace("\n", "<br/>"), border_color=colp)
            
            # Fortalezas y debilidades
            col1, col2 = st.columns(2)
            with col1:
                fortalezas_html = "<ul style='margin: 0; padding-left: 20px;'>"
                for f in ultima.fortalezas:
                    fortalezas_html += f"<li>{f}</li>"
                fortalezas_html += "</ul>"
                card("✅ Fortalezas", fortalezas_html, border_color="#27AE60")
            with col2:
                debilidades_html = "<ul style='margin: 0; padding-left: 20px;'>"
                for d in ultima.debilidades:
                    debilidades_html += f"<li>{d}</li>"
                debilidades_html += "</ul>"
                card("❌ Debilidades", debilidades_html, border_color="#EB5757")
            
            # Impacto político
            impactos = ultima.impacto_politico
            impactos_html = ""
            impactos_data = [
                ("Instalación", impactos.instalacion),
                ("Persuasión", impactos.persuasion),
                ("Movilización", impactos.movilizacion),
                ("Reputación", impactos.reputacion),
                ("Riesgo", impactos.riesgo)
            ]
            for nombre, valor in impactos_data:
                icon = "⬆️" if valor == "Sube" else "⬇️" if valor == "Baja" else "➡️"
                color = "#27AE60" if valor == "Sube" else "#EB5757" if valor == "Baja" else "#999999"
                impactos_html += f'<div style="display: inline-block; margin-right: 16px; margin-bottom: 8px;"><strong>{nombre}:</strong> <span style="color: {color}; font-weight: 700;">{icon} {valor}</span></div>'
            card("📈 Impacto Político", impactos_html, border_color="#666666")


# ========== PANTALLA: RANKING ==========
if pagina_seleccionada == "📊 Ranking":
    st.title("📊 Ranking Acumulado")
    
    ranking = obtener_ranking(st.session_state.evaluaciones)
    deltas = calcular_delta_ranking(ranking, st.session_state.ranking_previo) if st.session_state.ranking_previo else {}
    
    if not ranking:
        card("📭 Aún no hay evaluaciones", "Realiza tu primera evaluación en la pantalla 'Juego'.", border_color="#999999")
    else:
        # Cards por equipo
        for i, pos in enumerate(ranking, 1):
            col_equipo = party_color(pos.get("partido", ""))
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}°"
            
            delta = deltas.get(pos.get('equipo', ''), 0)
            delta_text = ""
            if delta > 0:
                delta_text = f'<span style="color: #27AE60; font-weight: 700;">⬆️ +{delta}</span>'
            elif delta < 0:
                delta_text = f'<span style="color: #EB5757; font-weight: 700;">⬇️ {delta}</span>'
            
            ranking_html = f"""
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 1.3rem; margin-right: 12px;">{medal}</span>
                    <strong style="font-size: 1.1rem;">{pos.get('equipo', '')}</strong>
                    <span class="small-muted">({pos.get('partido', '')})</span>
                    {delta_text}
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 1.5rem; font-weight: 900; color: {col_equipo};">{pos.get('total_acumulado', 0)}</div>
                    <span class="small-muted">{pos.get('cantidad_entregas', 0)} entregas</span>
                </div>
            </div>
            """
            card(f"", ranking_html, border_color=col_equipo)
        
        # Gráfico
        st.subheader("📈 Visualización")
        df_ranking = pd.DataFrame(ranking)
        if not df_ranking.empty:
            chart_data = df_ranking.set_index('equipo')['total_acumulado']
            st.bar_chart(chart_data)


# ========== PANTALLA: NOTICIERO ==========
if pagina_seleccionada == "🗞️ Noticiero":
    st.title("🗞️ Noticiero — Feed Narrativo")
    
    evaluaciones = st.session_state.evaluaciones[-20:] if len(st.session_state.evaluaciones) > 20 else st.session_state.evaluaciones
    
    if not evaluaciones:
        card("📭 Aún no hay noticias", "Las evaluaciones aparecerán aquí como noticias.", border_color="#999999")
    else:
        for eval_item in reversed(evaluaciones):
            col_noticia = party_color(eval_item.partido)
            
            # Línea de contexto
            contexto_html = f"""
            <div style="margin-bottom: 8px;">
                {badge(f"{eval_item.etapa} — {eval_item.ronda}", col_noticia)}
                <strong>{eval_item.candidato}</strong>
                <span class="small-muted">({eval_item.partido})</span>
            </div>
            """
            
            # Titular
            titular_html = f'<div style="font-weight: 800; font-size: 1.1rem; margin-bottom: 8px;">{eval_item.titular}</div>'
            
            # Total y shock
            shock_color = "#27AE60" if eval_item.shock_opinion_publica > 0 else "#EB5757" if eval_item.shock_opinion_publica < 0 else "#999999"
            total_html = f"""
            <div style="margin-top: 8px;">
                <span class="co-pill">{eval_item.total_final} pts</span>
                {f'<span style="color: {shock_color}; font-weight: 700; margin-left: 8px;">Shock: {eval_item.shock_opinion_publica:+d}</span>' if eval_item.shock_opinion_publica != 0 else ''}
            </div>
            """
            
            # Escándalo
            escandalo_html = ""
            if eval_item.escandalo.visible:
                sev_color = severity_color(eval_item.escandalo.severidad)
                escandalo_html = f'<div style="margin-top: 8px; padding: 8px; background: rgba(235, 87, 87, 0.1); border-radius: 8px; border-left: 4px solid {sev_color};"><strong>🚨 Escándalo ({eval_item.escandalo.severidad}):</strong> {eval_item.escandalo.motivo}</div>'
            
            contenido = contexto_html + titular_html + total_html + escandalo_html
            card("", contenido, border_color=col_noticia)


# ========== PANTALLA: RÚBRICA ==========
if pagina_seleccionada == "📋 Rúbrica":
    st.title("📋 Rúbrica de Evaluación")
    
    rubrica_html = """
    <h3>Dimensiones de Evaluación (0-20 puntos cada una)</h3>
    <p>Cada entrega es evaluada en 5 dimensiones, cada una con un puntaje de 0 a 20 puntos.<br/>
    El total máximo sin shock es 100 puntos.</p>
    
    <ol style="line-height: 1.8;">
        <li><strong>Claridad</strong> (0-20)
            <ul>
                <li>¿Es claro el mensaje?</li>
                <li>¿Se entiende qué se propone?</li>
                <li>¿La comunicación es efectiva?</li>
            </ul>
        </li>
        <li><strong>Estrategia</strong> (0-20)
            <ul>
                <li>¿La pieza está bien pensada estratégicamente?</li>
                <li>¿Apunta al público correcto?</li>
                <li>¿Tiene coherencia con el contexto?</li>
            </ul>
        </li>
        <li><strong>Credibilidad</strong> (0-20)
            <ul>
                <li>¿Genera confianza?</li>
                <li>¿Es creíble?</li>
                <li>¿Hay consistencia con el perfil del candidato?</li>
            </ul>
        </li>
        <li><strong>Emoción/Identidad</strong> (0-20)
            <ul>
                <li>¿Mueve emocionalmente?</li>
                <li>¿Conecta con la identidad del público?</li>
                <li>¿Genera identificación?</li>
            </ul>
        </li>
        <li><strong>Riesgo/Backlash</strong> (0-20)
            <ul>
                <li>¿Qué tan arriesgado es?</li>
                <li>¿Puede generar reacciones negativas?</li>
                <li><strong>Nota:</strong> Un puntaje ALTO en esta dimensión indica MÁS riesgo (no es positivo)</li>
            </ul>
        </li>
    </ol>
    
    <h3>Shock de Opinión Pública (-3 a +3)</h3>
    <p>Un ajuste pequeño que refleja reacciones inesperadas de la opinión pública y los medios.<br/>
    Puede ser positivo o negativo, pero siempre debe estar justificado por el contexto.</p>
    <p><strong>Total Final = Suma de scores (0-100) + Shock (-3 a +3)</strong></p>
    
    <h3>Escándalo</h3>
    <p>Si la entrega contiene elementos problemáticos que puedan generar controversia pública:</p>
    <ul>
        <li><strong>Visible:</strong> Sí/No</li>
        <li><strong>Severidad:</strong> Baja, Media o Alta</li>
        <li><strong>Motivo:</strong> Breve descripción</li>
    </ul>
    
    <h3>Impacto Político</h3>
    <p>Evalúa el impacto en 5 dimensiones cualitativas:</p>
    <ul>
        <li><strong>Instalación:</strong> Sube / Baja / Se mantiene</li>
        <li><strong>Persuasión:</strong> Sube / Baja / Se mantiene</li>
        <li><strong>Movilización:</strong> Sube / Baja / Se mantiene</li>
        <li><strong>Reputación:</strong> Sube / Baja / Se mantiene</li>
        <li><strong>Riesgo:</strong> Sube / Baja / Se mantiene</li>
    </ul>
    """
    
    card("📋 Rúbrica Completa", rubrica_html, border_color="#111111")


# ========== PANTALLA: CONFIGURACIÓN ==========
if pagina_seleccionada == "⚙️ Configuración":
    st.title("⚙️ Configuración")
    
    st.subheader("🔧 Configuración Técnica")
    
    modelo_ollama = st.text_input(
        "Modelo Ollama",
        value="qwen2.5:3b-instruct",
        help="Nombre del modelo local configurado en Ollama"
    )
    
    url_ollama = st.text_input(
        "URL Ollama",
        value="http://localhost:11434/api/generate",
        help="URL del endpoint de generación de Ollama"
    )
    
    # Test de conexión
    if st.button("🔌 Probar Conexión", type="primary"):
        with st.spinner("Probando conexión..."):
            ok, mensaje = test_conexion_ollama(url_ollama, modelo_ollama)
            if ok:
                st.success(mensaje)
            else:
                st.error(mensaje)
    
    st.divider()
    
    # Estadísticas
    st.subheader("📊 Estadísticas")
    total_evaluaciones = len(st.session_state.evaluaciones)
    card("Total de evaluaciones", f"<strong>{total_evaluaciones}</strong> entregas evaluadas", border_color="#666666")
    
    if total_evaluaciones > 0:
        ranking = obtener_ranking(st.session_state.evaluaciones)
        if ranking:
            card("Equipos activos", f"<strong>{len(ranking)}</strong> equipos en competencia", border_color="#666666")


# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown(
    "<div style='text-align: center; color: gray; font-size: 0.9rem;'>Prototipo</div>",
    unsafe_allow_html=True
)
