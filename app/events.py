"""
Eventos del juego Ciudad Oriental (GM-LLM).
Define los textos base para cada etapa y ronda con estética uruguaya ficticia.
"""

EVENTOS = {
    "R1": {
        "titulo": "Ronda 1 - Internas Partido A",
        "descripcion": """Primera ronda de las internas. Los precandidatos deben presentar su primer afiche de campaña.
        
El país enfrenta desafíos económicos y sociales. Los medios de comunicación están expectantes.
La ciudadanía busca propuestas claras y candidatos que generen confianza.

Contexto interno del partido: Hay tensiones entre corrientes históricas y nuevas generaciones.""",
        "tipo_entrega": "Afiche de campaña"
    },
    "R2": {
        "titulo": "Ronda 2 - Internas Partido A",
        "descripcion": """Segunda ronda de las internas. Es hora del primer discurso público en un acto partidario.
        
La campaña se intensifica. Los otros precandidatos ya mostraron sus cartas.
Los medios analizan cada movimiento. La opinión pública sigue de cerca.

Contexto interno del partido: Se avecinan definiciones importantes. Algunos sectores presionan por alianzas.""",
        "tipo_entrega": "Discurso público"
    },
    "R3": {
        "titulo": "Ronda 3 - Nacional (después de fusión)",
        "descripcion": """Primera ronda de la etapa nacional. Tu partido se unificó y ahora compites contra el otro partido.
        
El escenario cambió completamente. Ya no es solo tu partido, ahora es el país completo el que observa.
Los medios nacionales cubren cada detalle. Las redes sociales están en ebullición.

Contexto: La fusión partidaria generó nuevas dinámicas. Hay que demostrar unidad y proyecto nacional.""",
        "tipo_entrega": "Spot publicitario (30 segundos)"
    },
    "R4": {
        "titulo": "Ronda 4 - Nacional (penúltima)",
        "descripcion": """Cuarta ronda, la campaña está en su punto máximo.
        
Quedan pocas semanas para las elecciones. Los debates están en boca de todos.
La ciudadanía está decidiendo. Cada palabra cuenta, cada gesto es analizado.

Contexto: La contienda está reñida. Los ataques entre partidos se intensifican.""",
        "tipo_entrega": "Mensaje para redes sociales"
    },
    "Cierre": {
        "titulo": "Ronda Final - Cierre de campaña",
        "descripcion": """Última ronda antes de las elecciones. Todo llega a su punto culminante.
        
Es el momento final. Los precandidatos hacen su última apelación a la ciudadanía.
Los medios hacen balances. Los analistas proyectan resultados. La tensión es máxima.

Contexto: Última oportunidad de convencer a los indecisos y movilizar a los propios.""",
        "tipo_entrega": "Discurso de cierre"
    }
}


def obtener_evento(ronda: str) -> dict:
    """
    Obtener información del evento para una ronda.
    
    Args:
        ronda: Identificador de ronda ("R1", "R2", "R3", "R4", "Cierre")
    
    Returns:
        Diccionario con título, descripción y tipo de entrega
    """
    if ronda not in EVENTOS:
        raise ValueError(f"Ronda desconocida: {ronda}. Debe ser una de: {list(EVENTOS.keys())}")
    return EVENTOS[ronda]

