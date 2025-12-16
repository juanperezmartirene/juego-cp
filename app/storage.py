"""
Manejo de almacenamiento de logs y evaluaciones.
Guarda trazas completas en formato JSONL.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from app.models import Evaluacion


LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


def guardar_evaluacion(
    evaluacion: Evaluacion,
    prompt_completo: str,
    respuesta_llm: str,
    modelo_usado: str = "llama2"
) -> str:
    """
    Guarda una evaluación completa en el log JSONL.
    
    Args:
        evaluacion: Objeto Evaluacion con los resultados
        prompt_completo: Prompt completo enviado al LLM
        respuesta_llm: Respuesta completa del LLM
        modelo_usado: Nombre del modelo usado
    
    Returns:
        Ruta del archivo de log
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_file = LOGS_DIR / f"session_{timestamp}.jsonl"
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "modelo": modelo_usado,
        "prompt_completo": prompt_completo,
        "respuesta_llm": respuesta_llm,
        "evaluacion": evaluacion.to_dict()
    }
    
    with open(session_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    return str(session_file)


def cargar_evaluaciones() -> list:
    """
    Carga todas las evaluaciones guardadas desde los archivos de log.
    
    Returns:
        Lista de objetos Evaluacion
    """
    evaluaciones = []
    
    if not LOGS_DIR.exists():
        return evaluaciones
    
    for log_file in sorted(LOGS_DIR.glob("session_*.jsonl")):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        log_entry = json.loads(line)
                        eval_dict = log_entry.get('evaluacion', {})
                        if eval_dict:
                            evaluacion = Evaluacion.from_dict(eval_dict)
                            evaluaciones.append(evaluacion)
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"Error al cargar {log_file}: {e}")
            continue
    
    return evaluaciones


def obtener_ranking(evaluaciones: list) -> list:
    """
    Calcula el ranking acumulado de equipos.
    
    Args:
        evaluaciones: Lista de objetos Evaluacion
    
    Returns:
        Lista de diccionarios con 'equipo', 'partido', 'total_acumulado', 'cantidad_entregas'
        ordenada por total_acumulado descendente
    """
    acumulados = {}
    
    for eval in evaluaciones:
        equipo = eval.equipo
        if equipo not in acumulados:
            acumulados[equipo] = {
                'equipo': equipo,
                'partido': eval.partido,
                'total_acumulado': 0,
                'cantidad_entregas': 0
            }
        acumulados[equipo]['total_acumulado'] += eval.total_final
        acumulados[equipo]['cantidad_entregas'] += 1
    
    ranking = sorted(
        acumulados.values(),
        key=lambda x: x['total_acumulado'],
        reverse=True
    )
    
    return ranking

