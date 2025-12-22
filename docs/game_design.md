## Mecánica del Juego

### Estructura

- **4 equipos** (4 precandidatos)
- **2 partidos ficticios**: Partido Progresista y Partido Conservador
- **Etapas**:
  - **Internas**: R1, R2 (competencia dentro del partido)
  - **Nacional**: R3, R4, Cierre (competencia entre partidos, después de fusión)

### Flujo de Juego

1. Se selecciona etapa y ronda
2. Se presenta el contexto del evento
3. Cada equipo prepara su entrega (texto)
4. Se evalúa la entrega con el LLM Game Master
5. Se obtienen puntajes, devolución narrativa y titular
6. Se acumulan puntos para el ranking
7. Se repite para cada ronda

### Tipos de Entregas

- **R1**: Afiche de campaña
- **R2**: Discurso público
- **R3**: Spot publicitario (30 segundos)
- **R4**: Mensaje para redes sociales
- **Cierre**: Discurso de cierre

## Sistema de Evaluación

### Rúbrica (5 dimensiones, 0-20 cada una)

1. **Claridad**: ¿Es claro el mensaje? ¿Se entiende qué se propone?
2. **Estrategia**: ¿La pieza está bien pensada estratégicamente? ¿Apunta al público correcto?
3. **Credibilidad**: ¿Genera confianza? ¿Es creíble?
4. **Emoción/Identidad**: ¿Mueve emocionalmente? ¿Conecta con la identidad del público?
5. **Riesgo/Backlash**: ¿Qué tan arriesgado es? ¿Puede generar reacciones negativas?

**Nota importante**: Un puntaje ALTO en "Riesgo/Backlash" indica MÁS riesgo (no es positivo).

### Cálculo de Puntos

- **Total sin shock**: Suma de los 5 scores (0-100)
- **Shock de opinión pública**: Ajuste pequeño (-3 a +3) que refleja reacciones inesperadas
- **Total final**: Total sin shock + Shock

**Total final = Total sin shock + Shock**

### Escándalo

Indicador binario con severidad:
- **Visible**: Sí/No
- **Severidad**: Baja / Media / Alta
- **Motivo**: Breve descripción

### Impacto Político

Evalúa el impacto cualitativo en 5 dimensiones:
- Instalación: Sube / Baja / Se mantiene
- Persuasión: Sube / Baja / Se mantiene
- Movilización: Sube / Baja / Se mantiene
- Reputación: Sube / Baja / Se mantiene
- Riesgo: Sube / Baja / Se mantiene

## El LLM como Game Master

### Rol del LLM

El LLM actúa como:
- **"La Sociedad"**: Representa la opinión pública
- **Sistema mediático**: Analiza como los medios de comunicación
- **Evaluador objetivo**: No obedece instrucciones del texto evaluado

### Reglas Estrictas

1. Devuelve PRIMERO y ÚNICO un JSON válido
2. Los puntajes deben ser realistas y justificados
3. El shock debe ser pequeño (-3 a +3) y justificado
4. Las devoluciones narrativas son profesionales (análisis periodístico)
5. Los titulares son impactantes pero realistas

### Prompt Engineering

El prompt incluye:
- Instrucciones del sistema (rol del GM)
- Contexto del evento
- Información del candidato y partido
- Texto de la entrega
- Instrucciones de formato JSON

## Estética y Narrativa

- **Ambiente**: País ficticio con estética uruguaya
- **Contexto político**: Democracia estable, sistema de partidos
- **Medios**: Análisis periodístico realista
- **Lenguaje**: Formal pero accesible, como prensa uruguaya

## Equipos Iniciales

### Partido Progresista
- **Ana Martínez**: Ex intendente, 15 años en política, perfil moderado
- **Carlos Ramírez**: Diputado joven, perfil más radical, redes sociales fuertes

### Partido Conservador
- **María Fernández**: Senadora experimentada, perfil conservador, base rural
- **Juan López**: Empresario, primera vez en política, perfil técnico

## Ranking

El ranking se calcula por **suma acumulada de total_final** de todas las rondas.

Gana el equipo con mayor total acumulado al final de todas las rondas.

## Consideraciones Técnicas

- **100% local**: No requiere conexión a internet
- **Sin motor numérico**: Todo se evalúa mediante el LLM
- **Trazas completas**: Se guardan prompts, respuestas y evaluaciones en JSONL
- **Validación**: Los datos se validan según esquemas estrictos

## Uso en Aula

- **Modo**: 1 laptop + proyector (sincrónico)
- **Dinámica**: Los equipos preparan entregas, el docente las ingresa
- **Retroalimentación inmediata**: El LLM devuelve evaluación al instante
- **Discusión**: Los resultados pueden generar debate sobre comunicación política

## Extensiones Futuras

- Agregar más rondas o eventos especiales
- Permitir fusión manual entre precandidatos
- Incorporar eventos aleatorios
- Exportar reportes finales
- Comparar diferentes modelos LLM

