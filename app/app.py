"""
Aplicación Streamlit principal para Ciudad Oriental (GM-LLM).
Interfaz para el juego de campaña política evaluado por LLM local (Ollama).
"""

import streamlit as st
import requests
import json
from pathlib import Path
import sys

# Agregar el directorio raíz al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models import Evaluacion, Equipo
from app.events import obtener_evento, EVENTOS
from app.prompts import SYSTEM_PROMPT, construir_prompt_usuario, extraer_json_de_respuesta
from app.storage import guardar_evaluacion, cargar_evaluaciones, obtener_ranking


# Configuración de página
st.set_page_config(
    page_title="Prueba de juego Ciencia Política",
    page_icon="🏛️",
    layout="wide"
)

# Inicialización de estado de sesión
if 'evaluaciones' not in st.session_state:
    st.session_state.evaluaciones = cargar_evaluaciones()

# Equipos precargados
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
        partido="Partido Nacional",
        candidato="María Fernández",
        perfil="Senadora experimentada, perfil conservador, base rural"
    ),
    Equipo(
        nombre="Equipo 4",
        partido="Partido Nacional",
        candidato="Juan López",
        perfil="Empresario, primera vez en política, perfil técnico"
    )
]

# Título principal
st.title("🏛️ Prueba de juego Ciencia Política")
st.markdown("### Juego de Campaña Política con LLM")

# Sidebar para configuración
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Modelo de Ollama
    modelo_ollama = st.text_input(
        "Modelo Ollama",
        value="qwen2.5:3b-instruct",
        help="Nombre del modelo local configurado en Ollama"
    )
    
    # URL de Ollama
    url_ollama = st.text_input(
        "URL Ollama",
        value="http://localhost:11434/api/generate",
        help="URL del endpoint de generación de Ollama"
    )
    
    st.divider()
    
    # Selección de etapa
    etapa = st.selectbox(
        "Etapa",
        ["Internas", "Nacional"],
        help="Etapa actual del juego"
    )
    
    # Selección de ronda
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

# Contenido principal
if evento is None:
    st.error("Error al cargar el evento. Por favor, selecciona una ronda válida.")
    st.stop()

# Tabs principales
tab1, tab2, tab3 = st.tabs(["🎯 Evaluar Entrega", "📊 Ranking", "📋 Rúbrica"])

with tab1:
    st.header("Evaluar Nueva Entrega")
    
    # Selección de equipo
    equipo_seleccionado = st.selectbox(
        "Equipo",
        options=range(len(EQUIPOS_INICIALES)),
        format_func=lambda i: f"{EQUIPOS_INICIALES[i].nombre} - {EQUIPOS_INICIALES[i].candidato} ({EQUIPOS_INICIALES[i].partido})",
        help="Selecciona el equipo que presenta la entrega"
    )
    
    equipo = EQUIPOS_INICIALES[equipo_seleccionado]
    
    # Mostrar información del equipo
    with st.expander("👤 Información del Equipo", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Partido:** {equipo.partido}")
            st.write(f"**Candidato:** {equipo.candidato}")
        with col2:
            st.write(f"**Perfil:** {equipo.perfil}")
    
    # Visualización y edición del evento
    st.subheader("📄 Contexto del Evento")
    st.markdown(evento['descripcion'])
    
    # Campo de texto para situación interna (editable)
    situacion_interna = st.text_area(
        "Situación Interna del Partido",
        value="Tensiones entre corrientes históricas y nuevas generaciones.",
        help="Describe la situación interna actual del partido",
        height=100
    )
    
    # Campo de texto grande para la entrega
    st.subheader(f"📝 Entrega: {evento['tipo_entrega']}")
    entrega_textual = st.text_area(
        "Texto de la Entrega",
        placeholder=f"Escribe aquí tu {evento['tipo_entrega'].lower()}...",
        height=300,
        help="Ingresa el texto completo de la entrega a evaluar"
    )
    
    # Botón de evaluación
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        evaluar = st.button("🎲 Evaluar con GM", type="primary", use_container_width=True)
    with col2:
        if st.button("🔄 Limpiar", use_container_width=True):
            st.rerun()
    
    # Procesamiento de evaluación
    if evaluar:
        if not entrega_textual.strip():
            st.error("⚠️ Por favor, ingresa el texto de la entrega antes de evaluar.")
        else:
            with st.spinner("La ciudadanía está evaluando..."):
                try:
                    # Construir prompt
                    prompt_usuario = construir_prompt_usuario(
                        etapa=etapa,
                        ronda=ronda,
                        evento=evento,
                        partido=equipo.partido,
                        candidato=equipo.candidato,
                        perfil=equipo.perfil,
                        situacion_interna=situacion_interna,
                        entrega_textual=entrega_textual
                    )
                    
                    # Llamada a Ollama
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
                        # Extraer JSON de la respuesta
                        json_str = extraer_json_de_respuesta(respuesta_llm)
                        
                        # Parsear evaluación
                        evaluacion = Evaluacion.from_json(json_str)
                        
                        # Guardar en sesión y en log
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

    # Mostrar última evaluación si existe
    if st.session_state.evaluaciones:
        ultima = st.session_state.evaluaciones[-1]
        if ultima.equipo == equipo.candidato and ultima.ronda == ronda:
            st.divider()
            st.subheader("📊 Última Evaluación de este Equipo en esta Ronda")
            
            # Puntajes
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Claridad", ultima.scores.claridad)
            with col2:
                st.metric("Estrategia", ultima.scores.estrategia)
            with col3:
                st.metric("Credibilidad", ultima.scores.credibilidad)
            with col4:
                st.metric("Emoción/Identidad", ultima.scores.emocion_identidad)
            with col5:
                st.metric("Riesgo/Backlash", ultima.scores.riesgo_backlash)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total sin shock", ultima.total_sin_shock)
            with col2:
                st.metric("Shock opinión pública", ultima.shock_opinion_publica)
            with col3:
                st.metric("Total Final", ultima.total_final, delta=f"{ultima.shock_opinion_publica:+d}")
            
            # Titular
            st.markdown(f"### 📰 {ultima.titular}")
            
            # Escándalo
            if ultima.escandalo.visible:
                severidad_color = {
                    "Baja": "🟡",
                    "Media": "🟠",
                    "Alta": "🔴"
                }
                st.warning(
                    f"{severidad_color.get(ultima.escandalo.severidad, '⚠️')} **ESCÁNDALO** ({ultima.escandalo.severidad}): {ultima.escandalo.motivo}"
                )
            
            # Devolución GM
            st.markdown("### 💬 Devolución de la ciudadanía")
            st.markdown(ultima.devolucion_gm)
            
            # Fortalezas y debilidades
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### ✅ Fortalezas")
                for fortaleza in ultima.fortalezas:
                    st.write(f"• {fortaleza}")
            with col2:
                st.markdown("#### ❌ Debilidades")
                for debilidad in ultima.debilidades:
                    st.write(f"• {debilidad}")
            
            # Impacto político
            st.markdown("### 📈 Impacto Político")
            impactos = ultima.impacto_politico
            cols = st.columns(5)
            impactos_data = [
                ("Instalación", impactos.instalacion),
                ("Persuasión", impactos.persuasion),
                ("Movilización", impactos.movilizacion),
                ("Reputación", impactos.reputacion),
                ("Riesgo", impactos.riesgo)
            ]
            for col, (nombre, valor) in zip(cols, impactos_data):
                with col:
                    if valor == "Sube":
                        st.success(f"{nombre}: ⬆️")
                    elif valor == "Baja":
                        st.error(f"{nombre}: ⬇️")
                    else:
                        st.info(f"{nombre}: ➡️")

with tab2:
    st.header("📊 Ranking Acumulado")
    
    ranking = obtener_ranking(st.session_state.evaluaciones)
    
    if not ranking:
        st.info("📭 Aún no hay evaluaciones. Realiza tu primera evaluación en la pestaña 'Evaluar Entrega'.")
    else:
        # Tabla de ranking
        for i, pos in enumerate(ranking, 1):
            with st.container():
                col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
                with col1:
                    if i == 1:
                        st.markdown(f"### 🥇 {i}°")
                    elif i == 2:
                        st.markdown(f"### 🥈 {i}°")
                    elif i == 3:
                        st.markdown(f"### 🥉 {i}°")
                    else:
                        st.markdown(f"### {i}°")
                with col2:
                    st.markdown(f"**{pos['equipo']}** ({pos['partido']})")
                with col3:
                    st.metric("Total Acumulado", pos['total_acumulado'])
                with col4:
                    st.write(f"Entregas: {pos['cantidad_entregas']}")
                st.divider()
        
        # Gráfico de barras (simple)
        st.subheader("Visualización")
        import pandas as pd
        df_ranking = pd.DataFrame(ranking)
        st.bar_chart(df_ranking.set_index('equipo')['total_acumulado'])

with tab3:
    st.header("📋 Rúbrica de Evaluación")
    st.markdown("""
    ### Dimensiones de Evaluación (0-20 puntos cada una)
    
    Cada entrega es evaluada en 5 dimensiones, cada una con un puntaje de 0 a 20 puntos.
    El total máximo sin shock es 100 puntos.
    
    1. **Claridad** (0-20)
       - ¿Es claro el mensaje?
       - ¿Se entiende qué se propone?
       - ¿La comunicación es efectiva?
    
    2. **Estrategia** (0-20)
       - ¿La pieza está bien pensada estratégicamente?
       - ¿Apunta al público correcto?
       - ¿Tiene coherencia con el contexto?
    
    3. **Credibilidad** (0-20)
       - ¿Genera confianza?
       - ¿Es creíble?
       - ¿Hay consistencia con el perfil del candidato?
    
    4. **Emoción/Identidad** (0-20)
       - ¿Mueve emocionalmente?
       - ¿Conecta con la identidad del público?
       - ¿Genera identificación?
    
    5. **Riesgo/Backlash** (0-20)
       - ¿Qué tan arriesgado es?
       - ¿Puede generar reacciones negativas?
       - Nota: Un puntaje ALTO en esta dimensión indica MÁS riesgo (no es positivo)
    
    ### Shock de Opinión Pública (-3 a +3)
    
    Un ajuste pequeño que refleja reacciones inesperadas de la opinión pública y los medios.
    Puede ser positivo o negativo, pero siempre debe estar justificado por el contexto.
    
    **Total Final = Suma de scores (0-100) + Shock (-3 a +3)**
    
    ### Escándalo
    
    Si la entrega contiene elementos problemáticos que puedan generar controversia pública:
    - **Visible**: Sí/No
    - **Severidad**: Baja, Media o Alta
    - **Motivo**: Breve descripción
    
    ### Impacto Político
    
    Evalúa el impacto en 5 dimensiones cualitativas:
    - **Instalación**: Sube / Baja / Se mantiene
    - **Persuasión**: Sube / Baja / Se mantiene
    - **Movilización**: Sube / Baja / Se mantiene
    - **Reputación**: Sube / Baja / Se mantiene
    - **Riesgo**: Sube / Baja / Se mantiene
    """)

# Footer
st.divider()
st.markdown(
    "<div style='text-align: center; color: gray;'>Ciudad Oriental (GM-LLM) - Prototipo Educativo</div>",
    unsafe_allow_html=True
)

