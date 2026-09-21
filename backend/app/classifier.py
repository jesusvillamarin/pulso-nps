from __future__ import annotations

import hashlib
import json
import logging
import os
import random
from typing import Any

from .config import CONFIDENCE_THRESHOLD, TYPESAFE_MOCK
from .taxonomy import TONE_CRITERIA

logger = logging.getLogger(__name__)


def _choice_payload(answer: Any) -> tuple[str, float, dict[str, float]]:
    probabilities = getattr(answer, "probabilities", {}) or {}
    if hasattr(probabilities, "model_dump"):
        probabilities = probabilities.model_dump()
    probabilities = {str(key): float(value) for key, value in dict(probabilities).items()}
    return str(answer.choice), float(answer.confidence), probabilities


def _mock_pick(comment: str, options: list[str], kind: str) -> tuple[str, float, dict[str, float]]:
    text = comment.lower()
    if kind == "tone":
        signals = {
            "Agresivo": ["inaceptable", "estafa", "idiotas", "denuncia"],
            "Frustrado": ["frustr", "sigue", "otra vez", "nadie responde"],
            "Decepcionado": ["decepcion", "esperaba", "lástima"],
            "Confundido": ["no entiendo", "cómo", "tengo dudas", "confuso"],
            "Feliz": ["me encanta", "fantástico", "perfecto", "excelente"],
            "Positivo": ["bueno", "buena", "rápido", "recomendar"],
        }
    else:
        signals = {
            "Facturación": ["cobr", "factura", "reembolso", "precio", "plan"],
            "Atención": ["soporte", "atención", "responde", "equipo"],
            "Operaciones": ["entrega", "envío", "stock", "esperando"],
            "Producto": ["versión", "producto", "error", "integr", "registro", "plataforma"],
        }
    fallback = "Neutral" if kind == "tone" and "Neutral" in options else options[-1]
    picked = next((name for name, words in signals.items() if name in options and any(word in text for word in words)), fallback)
    seed = int(hashlib.sha256(f"{comment}:{kind}".encode()).hexdigest()[:8], 16)
    confidence = 0.42 + random.Random(seed).random() * 0.55
    rest = (1 - confidence) / max(1, len(options) - 1)
    probabilities = {option: (confidence if option == picked else rest) for option in options}
    return picked, confidence, probabilities


def _mock_category(comment: str, categories: list[dict[str, str]]) -> tuple[str, float, dict[str, float]]:
    options = [item["name"] for item in categories]
    text = comment.lower()
    keywords = {
        "Cobros": ["cobr", "cargo"], "Reembolsos": ["reembolso"], "Planes y precios": ["plan", "precio"],
        "Trato": ["amable", "trato"], "Resolución": ["resolv", "solución"], "Tiempo de respuesta": ["espera", "responde"],
        "Usabilidad": ["intuit", "fácil", "registro"], "Funcionalidad": ["función", "básico"], "Errores": ["error", "fallo"],
        "Integraciones": ["integr"], "Entrega": ["entrega", "envío"], "Disponibilidad": ["stock", "dispon"],
    }
    picked = next((name for name in options if any(word in text for word in keywords.get(name, []))), options[0])
    confidence = 0.78
    rest = (1 - confidence) / max(1, len(options) - 1)
    return picked, confidence, {option: (confidence if option == picked else rest) for option in options}


def classify_batch(items: list[dict[str, Any]], taxonomy: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if TYPESAFE_MOCK or not os.getenv("TYPESAFE_API_KEY"):
        return _classify_mock(items, taxonomy)

    from typesafe_sdk import Choice, TypeSafeClient

    area_criteria = {area["name"]: area.get("description") or None for area in taxonomy}
    state = {"comments": [{"row_id": item["row_index"], "text": item["comment"]} for item in items]}
    first_questions: dict[str, Any] = {}
    for index, _item in enumerate(items):
        first_questions[f"area_{index}"] = Choice(
            instructions=f"Clasifica el tema principal de `comments[{index}].text` en un área. Elige Otros si ninguna encaja.",
            criteria=area_criteria,
        )
        first_questions[f"tone_{index}"] = Choice(
            instructions=f"Identifica el tono emocional dominante de `comments[{index}].text`.",
            criteria=TONE_CRITERIA,
        )

    with TypeSafeClient(model="jev-latest") as client:
        first = client.system_one(state=state, questions=first_questions)
        areas: list[tuple[str, float, dict[str, float]]] = []
        tones: list[tuple[str, float, dict[str, float]]] = []
        second_questions: dict[str, Any] = {}
        for index, _item in enumerate(items):
            area_answer = _choice_payload(first.choices[f"area_{index}"])
            tone_answer = _choice_payload(first.choices[f"tone_{index}"])
            areas.append(area_answer)
            tones.append(tone_answer)
            area = next((entry for entry in taxonomy if entry["name"] == area_answer[0]), taxonomy[-1])
            criteria = {category["name"]: category.get("description") or None for category in area["categories"]}
            second_questions[f"category_{index}"] = Choice(
                instructions=(
                    f"El comentario `comments[{index}].text` fue asignado al área '{area['name']}'. "
                    "Elige la categoría más específica dentro de esa área."
                ),
                criteria=criteria,
            )
        second = client.system_one(state=state, questions=second_questions)

    model = str(getattr(first, "model", "jev-latest"))
    results = []
    for index, item in enumerate(items):
        category = _choice_payload(second.choices[f"category_{index}"])
        area, tone = areas[index], tones[index]
        results.append(_result(item, area, category, tone, model))
    return results


def _classify_mock(items: list[dict[str, Any]], taxonomy: list[dict[str, Any]]) -> list[dict[str, Any]]:
    area_options = [area["name"] for area in taxonomy]
    tone_options = list(TONE_CRITERIA)
    results = []
    for item in items:
        area = _mock_pick(item["comment"], area_options, "area")
        tone = _mock_pick(item["comment"], tone_options, "tone")
        area_config = next(entry for entry in taxonomy if entry["name"] == area[0])
        category = _mock_category(item["comment"], area_config["categories"])
        results.append(_result(item, area, category, tone, "mock-local"))
    return results


def _result(
    item: dict[str, Any],
    area: tuple[str, float, dict[str, float]],
    category: tuple[str, float, dict[str, float]],
    tone: tuple[str, float, dict[str, float]],
    model: str,
) -> dict[str, Any]:
    return {
        "row_index": item["row_index"],
        "area": area[0], "area_confidence": area[1], "area_probabilities": area[2],
        "category": category[0], "category_confidence": category[1], "category_probabilities": category[2],
        "tone": tone[0], "tone_confidence": tone[1], "tone_probabilities": tone[2],
        "model": model,
        "needs_review": min(area[1], category[1], tone[1]) < CONFIDENCE_THRESHOLD,
    }
