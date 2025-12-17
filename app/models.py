"""
Modelos de datos para el juego Ciudad Oriental (GM-LLM).
Define los esquemas de datos para equipos, evaluaciones y rankings.

Versión robusta:
- Normaliza claves (tildes / aliases), valores (sinónimos), tipos (str->int/bool),
  y repara estructuras comunes devueltas por LLM.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List
import json


# -----------------------------
# Normalizadores generales
# -----------------------------

def _strip(s: Any) -> Any:
    return s.strip() if isinstance(s, str) else s


def _to_int(x: Any, default: int | None = None) -> int:
    if isinstance(x, bool):
        return int(x)
    if isinstance(x, int):
        return x
    if isinstance(x, float):
        return int(x)
    if isinstance(x, str):
        t = x.strip()
        # soporta "10/20"
        if "/" in t:
            t = t.split("/", 1)[0].strip()
        # soporta "10 puntos"
        t = "".join(ch for ch in t if ch.isdigit() or ch == "-" )
        if t in ("", "-", "--"):
            return default if default is not None else 0
        try:
            return int(t)
        except ValueError:
            return default if default is not None else 0
    return default if default is not None else 0


def _to_bool(x: Any, default: bool = False) -> bool:
    if isinstance(x, bool):
        return x
    if isinstance(x, int):
        return x != 0
    if isinstance(x, str):
        t = x.strip().lower()
        if t in ("true", "t", "1", "si", "sí", "s", "yes", "y"):
            return True
        if t in ("false", "f", "0", "no", "n"):
            return False
    return default


def _to_list_str(x: Any) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [str(_strip(i)) for i in x if str(i).strip() != ""]
    if isinstance(x, str):
        t = x.strip()
        if t == "":
            return []
        # Si viene un string largo, lo guardamos como item único
        return [t]
    # cualquier otra cosa
    return [str(x)]


def _clamp_int(x: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, x))


def _norm_key(k: str) -> str:
    """
    Normaliza claves (tildes y aliases frecuentes).
    """
    if not isinstance(k, str):
        return k
    kk = k.strip()

    # Normalización simple de tildes en claves conocidas
    aliases = {
        # top-level
        "equipo_nombre": "equipo",
        "team": "equipo",
        "candidate": "candidato",
        "stage": "etapa",
        "round": "ronda",
        "shock": "shock_opinion_publica",
        "total": "total_final",
        # nested impacto_politico
        "instalación": "instalacion",
        "persuasión": "persuasion",
        "movilización": "movilizacion",
        "reputación": "reputacion",
        # nested scores
        "emoción_identidad": "emocion_identidad",
        "emocion/identidad": "emocion_identidad",
        "riesgo/backlash": "riesgo_backlash",
        # escandalo
        "escándalo": "escandalo",
    }
    return aliases.get(kk, kk)


def _normalize_keys_deep(obj: Any) -> Any:
    """
    Recorre dicts/listas y normaliza claves.
    """
    if isinstance(obj, dict):
        new: Dict[str, Any] = {}
        for k, v in obj.items():
            nk = _norm_key(k)
            new[nk] = _normalize_keys_deep(v)
        return new
    if isinstance(obj, list):
        return [_normalize_keys_deep(i) for i in obj]
    return obj


# -----------------------------
# Normalizadores específicos
# -----------------------------

def _normalizar_impacto_valor(value: Any) -> str:
    """
    Normaliza valores para ImpactoPolitico.
    Valores válidos finales: "Sube", "Baja", "Se mantiene".
    """
    if value is None:
        return "Se mantiene"
    v = _strip(value)
    if not isinstance(v, str):
        v = str(v)

    t = v.strip()

    mapping = {
        # correctos
        "Sube": "Sube",
        "Baja": "Baja",
        "Se mantiene": "Se mantiene",

        # mayúsculas / variantes
        "SE MANTIENE": "Se mantiene",
        "Se Mantiene": "Se mantiene",
        "Mantiene": "Se mantiene",
        "Sin cambio": "Se mantiene",
        "Sin cambios": "Se mantiene",
        "Igual": "Se mantiene",
        "Estable": "Se mantiene",
        "Neutral": "Se mantiene",

        "Aumenta": "Sube",
        "Sube mucho": "Sube",
        "Mejora": "Sube",
        "Crece": "Sube",
        "Al alza": "Sube",

        "Desciende": "Baja",
        "Cae": "Baja",
        "Empeora": "Baja",
        "Baja mucho": "Baja",
        "A la baja": "Baja",

        # Confusión con severidad de escándalo (Baja/Media/Alta)
        "Alta": "Sube",
        "Media": "Se mantiene",
        "Baja": "Baja",

        # Variantes Bajo/Medio/Alto
        "Alto": "Sube",
        "Medio": "Se mantiene",
        "Bajo": "Baja",

        # minúsculas comunes
        "sube": "Sube",
        "baja": "Baja",
        "se mantiene": "Se mantiene",
        "alto": "Sube",
        "medio": "Se mantiene",
        "bajo": "Baja",
    }

    return mapping.get(t, t)


def _normalizar_severidad(value: Any) -> str:
    if value is None:
        return "Baja"
    v = _strip(value)
    if not isinstance(v, str):
        v = str(v)
    t = v.strip()

    mapping = {
        "Baja": "Baja",
        "Media": "Media",
        "Alta": "Alta",
        # variantes
        "baja": "Baja",
        "media": "Media",
        "alta": "Alta",
        "Bajo": "Baja",
        "Medio": "Media",
        "Alto": "Alta",
        "bajo": "Baja",
        "medio": "Media",
        "alto": "Alta",
    }
    return mapping.get(t, "Baja")


# -----------------------------
# Dataclasses
# -----------------------------

@dataclass
class Scores:
    claridad: int
    estrategia: int
    credibilidad: int
    emocion_identidad: int
    riesgo_backlash: int

    def __post_init__(self):
        # Tipos y clamps (tolerante)
        self.claridad = _clamp_int(_to_int(self.claridad, 0), 0, 20)
        self.estrategia = _clamp_int(_to_int(self.estrategia, 0), 0, 20)
        self.credibilidad = _clamp_int(_to_int(self.credibilidad, 0), 0, 20)
        self.emocion_identidad = _clamp_int(_to_int(self.emocion_identidad, 0), 0, 20)
        self.riesgo_backlash = _clamp_int(_to_int(self.riesgo_backlash, 0), 0, 20)

    def total(self) -> int:
        return self.claridad + self.estrategia + self.credibilidad + self.emocion_identidad + self.riesgo_backlash


@dataclass
class Escandalo:
    visible: bool
    severidad: str
    motivo: str

    def __post_init__(self):
        self.visible = _to_bool(self.visible, False)
        self.severidad = _normalizar_severidad(self.severidad)
        self.motivo = (self.motivo or "").strip()


@dataclass
class ImpactoPolitico:
    instalacion: str
    persuasion: str
    movilizacion: str
    reputacion: str
    riesgo: str

    def __post_init__(self):
        self.instalacion = _normalizar_impacto_valor(self.instalacion)
        self.persuasion = _normalizar_impacto_valor(self.persuasion)
        self.movilizacion = _normalizar_impacto_valor(self.movilizacion)
        self.reputacion = _normalizar_impacto_valor(self.reputacion)
        self.riesgo = _normalizar_impacto_valor(self.riesgo)

        validos = {"Sube", "Baja", "Se mantiene"}
        for field in ["instalacion", "persuasion", "movilizacion", "reputacion", "riesgo"]:
            v = getattr(self, field)
            if v not in validos:
                # fallback duro: si viene cualquier otra cosa, no rompemos el juego
                setattr(self, field, "Se mantiene")


@dataclass
class Evaluacion:
    equipo: str
    partido: str
    candidato: str
    etapa: str
    ronda: str
    scores: Scores
    total_sin_shock: int
    shock_opinion_publica: int
    total_final: int
    escandalo: Escandalo
    fortalezas: List[str]
    debilidades: List[str]
    titular: str
    devolucion_gm: str
    impacto_politico: ImpactoPolitico

    def __post_init__(self):
        self.equipo = (self.equipo or "").strip()
        self.partido = (self.partido or "").strip()
        self.candidato = (self.candidato or "").strip()
        self.etapa = (self.etapa or "").strip()
        self.ronda = (self.ronda or "").strip()

        self.shock_opinion_publica = _clamp_int(_to_int(self.shock_opinion_publica, 0), -3, 3)

        # Recalcular totales para robustez (fuente de verdad: scores + shock)
        self.total_sin_shock = self.scores.total()
        self.total_final = self.total_sin_shock + self.shock_opinion_publica

        self.fortalezas = _to_list_str(self.fortalezas)
        self.debilidades = _to_list_str(self.debilidades)
        self.titular = (self.titular or "").strip()
        self.devolucion_gm = (self.devolucion_gm or "").strip()

    def to_dict(self) -> dict:
        d = asdict(self)
        d["scores"] = asdict(self.scores)
        d["escandalo"] = asdict(self.escandalo)
        d["impacto_politico"] = asdict(self.impacto_politico)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Evaluacion":
        """
        Crea Evaluacion desde un dict ya parseado, aplicando normalizaciones robustas.
        """
        if not isinstance(data, dict):
            raise ValueError("La evaluación debe ser un objeto JSON (dict).")

        # Normalizar claves (incluye tildes y aliases)
        data = _normalize_keys_deep(data)

        # Normalizar estructuras esperadas
        scores_raw = data.get("scores", {}) or {}
        esc_raw = data.get("escandalo", {}) or {}
        imp_raw = data.get("impacto_politico", {}) or {}

        # Impacto: normalizar claves con tildes si aparecen
        # (ya se hace en normalize_keys_deep, pero cubrimos casos residuales)
        for old, new in {
            "reputación": "reputacion",
            "movilización": "movilizacion",
            "persuasión": "persuasion",
            "instalación": "instalacion",
        }.items():
            if old in imp_raw and new not in imp_raw:
                imp_raw[new] = imp_raw.pop(old)

        # Completar defaults para impacto si faltan campos
        for k in ["instalacion", "persuasion", "movilizacion", "reputacion", "riesgo"]:
            imp_raw.setdefault(k, "Se mantiene")

        # Normalizar valores impacto
        for k in list(imp_raw.keys()):
            imp_raw[k] = _normalizar_impacto_valor(imp_raw[k])

        # Completar defaults para scores si faltan campos
        for k in ["claridad", "estrategia", "credibilidad", "emocion_identidad", "riesgo_backlash"]:
            scores_raw.setdefault(k, 0)

        # Escándalo defaults
        esc_raw.setdefault("visible", False)
        esc_raw.setdefault("severidad", "Baja")
        esc_raw.setdefault("motivo", "")

        # Listas
        fortalezas = _to_list_str(data.get("fortalezas", []))
        debilidades = _to_list_str(data.get("debilidades", []))

        # Construcción de objetos
        data["scores"] = Scores(**scores_raw)
        data["escandalo"] = Escandalo(**esc_raw)
        data["impacto_politico"] = ImpactoPolitico(**imp_raw)

        # Normalizar ints (aunque luego recalculamos)
        data["total_sin_shock"] = _to_int(data.get("total_sin_shock", data["scores"].total()), data["scores"].total())
        data["shock_opinion_publica"] = _to_int(data.get("shock_opinion_publica", 0), 0)
        data["total_final"] = _to_int(data.get("total_final", data["total_sin_shock"] + data["shock_opinion_publica"]),
                                      data["total_sin_shock"] + data["shock_opinion_publica"])

        data["fortalezas"] = fortalezas
        data["debilidades"] = debilidades
        data.setdefault("titular", "")
        data.setdefault("devolucion_gm", "")

        # Campos top-level obligatorios con fallback razonable
        data.setdefault("equipo", data.get("candidato", ""))
        data.setdefault("partido", "")
        data.setdefault("candidato", "")
        data.setdefault("etapa", "")
        data.setdefault("ronda", "")

        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "Evaluacion":
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON inválido: {e}")
        except Exception as e:
            raise ValueError(f"Error al parsear evaluación: {e}")


@dataclass
class Equipo:
    nombre: str
    partido: str
    candidato: str
    perfil: str
