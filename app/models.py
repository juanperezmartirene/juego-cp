"""
Modelos de datos para el juego Ciudad Oriental (GM-LLM).
Define los esquemas de datos para equipos, evaluaciones y rankings.
"""

from typing import List, Optional
from dataclasses import dataclass, asdict
import json

def _normalizar_impacto_valor(value: str) -> str:
    """
    Normaliza valores para ImpactoPolitico.
    Acepta variantes comunes y corrige confusiones típicas del LLM.
    """
    if not isinstance(value, str):
        return value

    v = value.strip()

    # Correcciones por confusión con severidad de escándalo
    severidad_to_impacto = {
        "Alta": "Sube",
        "Media": "Se mantiene",
        "Baja": "Baja",
    }
    if v in severidad_to_impacto:
        return severidad_to_impacto[v]

    # Normalizar variantes de texto comunes
    aliases = {
        "Se mantiene": "Se mantiene",
        "Se Mantiene": "Se mantiene",
        "Mantiene": "Se mantiene",
        "Igual": "Se mantiene",
        "Sin cambios": "Se mantiene",
        "Sube": "Sube",
        "Aumenta": "Sube",
        "Baja": "Baja",
        "Desciende": "Baja",
    }
    return aliases.get(v, v)

@dataclass
class Scores:
    """Puntajes en las 5 dimensiones (0-20 cada una)."""
    claridad: int
    estrategia: int
    credibilidad: int
    emocion_identidad: int
    riesgo_backlash: int

    def __post_init__(self):
        """Validar que los scores estén en el rango correcto."""
        for field in ['claridad', 'estrategia', 'credibilidad', 'emocion_identidad', 'riesgo_backlash']:
            value = getattr(self, field)
            if not isinstance(value, int) or value < 0 or value > 20:
                raise ValueError(f"{field} debe ser un entero entre 0 y 20, recibido: {value}")

    def total(self) -> int:
        """Suma total de los scores."""
        return sum([
            self.claridad,
            self.estrategia,
            self.credibilidad,
            self.emocion_identidad,
            self.riesgo_backlash
        ])


@dataclass
class Escandalo:
    """Información sobre escándalo público."""
    visible: bool
    severidad: str  # "Baja", "Media", "Alta"
    motivo: str

    def __post_init__(self):
        """Validar severidad."""
        if self.severidad not in ["Baja", "Media", "Alta"]:
            raise ValueError(f"severidad debe ser 'Baja', 'Media' o 'Alta', recibido: {self.severidad}")


@dataclass
class ImpactoPolitico:
    """Impacto político en diferentes dimensiones."""
    instalacion: str  # "Sube", "Baja", "Se mantiene"
    persuasion: str
    movilizacion: str
    reputacion: str
    riesgo: str

    def __post_init__(self):
        """Validar valores."""
        validos = ["Sube", "Baja", "Se mantiene"]
        for field in ['instalacion', 'persuasion', 'movilizacion', 'reputacion', 'riesgo']:
            value = getattr(self, field)
            if value not in validos:
                raise ValueError(f"{field} debe ser uno de {validos}, recibido: {value}")


@dataclass
class Evaluacion:
    """Evaluación completa de una entrega por el LLM."""
    equipo: str
    partido: str
    candidato: str
    etapa: str
    ronda: str
    scores: Scores
    total_sin_shock: int
    shock_opinion_publica: int  # -3 a +3
    total_final: int
    escandalo: Escandalo
    fortalezas: List[str]
    debilidades: List[str]
    titular: str
    devolucion_gm: str
    impacto_politico: ImpactoPolitico

    def __post_init__(self):
        """Validar shock y totales."""
        if not (-3 <= self.shock_opinion_publica <= 3):
            raise ValueError(f"shock_opinion_publica debe estar entre -3 y +3, recibido: {self.shock_opinion_publica}")
        if self.total_sin_shock != self.scores.total():
            raise ValueError(f"total_sin_shock ({self.total_sin_shock}) debe igualar la suma de scores ({self.scores.total()})")
        if self.total_final != self.total_sin_shock + self.shock_opinion_publica:
            raise ValueError(f"total_final ({self.total_final}) debe igualar total_sin_shock + shock ({self.total_sin_shock + self.shock_opinion_publica})")

    def to_dict(self) -> dict:
        """Convertir a diccionario para JSON."""
        d = asdict(self)
        d['scores'] = asdict(self.scores)
        d['escandalo'] = asdict(self.escandalo)
        d['impacto_politico'] = asdict(self.impacto_politico)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> 'Evaluacion':
        """Crear desde diccionario."""
        data['scores'] = Scores(**data['scores'])
        data['escandalo'] = Escandalo(**data['escandalo'])
        impacto = data.get('impacto_politico', {})
        for k in ['instalacion', 'persuasion', 'movilizacion', 'reputacion', 'riesgo']:
            if k in impacto:
                impacto[k] = _normalizar_impacto_valor(impacto[k])
        data['impacto_politico'] = ImpactoPolitico(**impacto)
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'Evaluacion':
        """Crear desde string JSON."""
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON inválido: {e}")
        except (KeyError, TypeError, ValueError) as e:
            raise ValueError(f"Error al parsear evaluación: {e}")


@dataclass
class Equipo:
    """Equipo de precandidato."""
    nombre: str
    partido: str
    candidato: str
    perfil: str

