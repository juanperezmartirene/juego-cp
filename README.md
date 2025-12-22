# Ciudad Oriental (GM-LLM)

Prototipo funcional de un minijuego educativo donde un LLM local (vía Ollama) actúa como evaluador de piezas de campaña política.

## Descripción

"Juego pensado para uso sincrónico en aula (1 laptop + proyector), donde equipos compiten presentando piezas de campaña política (afiches, discursos, spots, etc.) que son evaluadas por un LLM local.

El LLM devuelve:
- Puntajes numéricos (0-20) en 5 dimensiones (total 0-100)
- Un shock de opinión pública (-3 a +3)
- Devolución narrativa + titular
- Indicador de escándalo visible (Sí/No, severidad)

## Requisitos

- Python 3.8+
- Ollama instalado y corriendo localmente
- Un modelo LLM configurado en Ollama (por defecto: `llama2`)

## Instalación

1. Clonar o descargar el repositorio

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Asegurarse de que Ollama esté corriendo:
```bash
ollama serve
```

4. (Opcional) Verificar que el modelo esté disponible:
```bash
ollama list
```

Si necesitas descargar un modelo:
```bash
ollama pull llama2
```

## Uso

Ejecutar la aplicación Streamlit:

```bash
streamlit run app/app.py
```

La aplicación se abrirá en el navegador (por defecto en `http://localhost:8501`).

### Configuración en la Interfaz

- **Modelo Ollama**: Nombre del modelo a usar (por defecto: `llama2`)
- **URL Ollama**: Endpoint de Ollama (por defecto: `http://localhost:11434/api/generate`)
- **Etapa**: Seleccionar entre "Internas" o "Nacional"
- **Ronda**: Seleccionar entre "R1", "R2", "R3", "R4", "Cierre"

### Flujo de Juego

1. Seleccionar etapa y ronda
2. Seleccionar equipo (4 equipos precargados)
3. Revisar el contexto del evento
4. Ajustar situación interna del partido (opcional)
5. Ingresar el texto de la entrega
6. Hacer clic en "Evaluar con GM"
7. Revisar resultados en la misma pantalla
8. Ver ranking acumulado en la pestaña "Ranking"

## Estructura del Proyecto

```
ciudad-oriental-llm-gm/
├── app/
│   ├── app.py          # Aplicación principal Streamlit
│   ├── prompts.py      # Prompts para el LLM
│   ├── events.py       # Eventos y rondas del juego
│   ├── models.py       # Modelos de datos y validación
│   └── storage.py      # Manejo de logs y almacenamiento
├── logs/               # Logs de sesiones (JSONL)
├── docs/
│   └── game_design.md  # Documentación de diseño
├── .gitignore
├── README.md
└── requirements.txt
```

## Almacenamiento

Todas las evaluaciones se guardan automáticamente en `logs/session_YYYYMMDD_HHMMSS.jsonl` con:
- Timestamp
- Modelo usado
- Prompt completo enviado al LLM
- Respuesta completa del LLM
- Evaluación parseada

## Rúbrica

El juego evalúa 5 dimensiones (0-20 puntos cada una):

1. **Claridad**: ¿Es claro el mensaje?
2. **Estrategia**: ¿Está bien pensada estratégicamente?
3. **Credibilidad**: ¿Genera confianza?
4. **Emoción/Identidad**: ¿Mueve emocionalmente?
5. **Riesgo/Backlash**: ¿Puede generar reacciones negativas? (alto = más riesgo)

Total sin shock: 0-100 puntos
Shock de opinión pública: -3 a +3
**Total final: suma de scores + shock**

## Equipos Precargados

El juego incluye 4 equipos iniciales:
- **Equipo 1**: Ana Martínez (Partido Progresista)
- **Equipo 2**: Carlos Ramírez (Partido Progresista)
- **Equipo 3**: María Fernández (Partido Nacional)
- **Equipo 4**: Juan López (Partido Nacional)

## Notas Técnicas

- El sistema corre 100% local, sin conexión a internet
- Todo el procesamiento se hace mediante Ollama
- Los logs se guardan en formato JSONL para análisis posterior
- La validación de datos se hace en `models.py` usando dataclasses

## Troubleshooting

**Error: "Error de conexión con Ollama"**
- Verificar que Ollama esté corriendo: `ollama serve`
- Verificar que la URL en la configuración sea correcta

**Error: "El LLM no devolvió respuesta"**
- Verificar que el modelo especificado exista: `ollama list`
- Intentar con un modelo más pequeño o descargar el modelo: `ollama pull llama2`

**Error: "Error al parsear JSON del LLM"**
- El LLM puede no estar devolviendo JSON válido
- Revisar la respuesta en el expander de errores
- Considerar usar un modelo más potente o ajustar el prompt

## Licencia

Prototipo educativo - Uso interno.

