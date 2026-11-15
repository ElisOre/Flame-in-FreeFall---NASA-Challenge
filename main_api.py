import json
import re
import urllib.error
import urllib.request
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from qdrant_client.models import Filter, FieldCondition, MatchValue
import uvicorn

from src.config import Config
from src.db_mysql import filter_tests, rank_investigations_by_habitat, get_investigation_detail
from src.db_qdrant import semantic_search, qdrant

app = FastAPI(title="NASA Flame in Freefall Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def detect_query_language(text: str, fallback: str = "en") -> str:
    """Detecta si la consulta está en español ('es') o inglés ('en') para el modo fallback."""
    t = text.lower().strip()
    if re.search(r"[¿¡áéíóúñ]", t):
        return "es"
    es_words = {"qué", "que", "cuál", "cual", "cómo", "como", "para", "sobre", "oxígeno",
                "oxigeno", "llama", "llamas", "gota", "gotas", "luna", "lunar", "espacio",
                "incendio", "fuego", "hollín", "hollin", "supresión", "supresion", "en", "las", "los"}
    en_words = {"what", "which", "how", "for", "about", "oxygen", "flame", "flames",
                "droplet", "droplets", "moon", "space", "fire", "soot", "suppression",
                "the", "with", "microgravity", "flammability"}
    tokens = set(re.findall(r"\b\w+\b", t))
    es_score = len(tokens & es_words)
    en_score = len(tokens & en_words)
    if es_score > en_score:
        return "es"
    if en_score > es_score:
        return "en"
    return fallback if fallback in ("en", "es") else "en"

@app.get("/api/ranking")
def api_get_ranking(habitat: str = "lunar_base"):
    o2_map = {"lunar_base": 30.0, "spacesuit": 100.0, "iss": 21.0}
    return rank_investigations_by_habitat(o2_map.get(habitat, 30.0))

@app.get("/api/tests")
def api_get_tests(
    psi_id: Optional[str] = None,
    fuel_material: Optional[str] = None,
    min_o2_pct: Optional[float] = None,
    max_pressure_psi: Optional[float] = None
):
    return filter_tests(psi_id, fuel_material, min_o2_pct, max_pressure_psi)

@app.get("/api/search")
def api_semantic_search(q: str, fuel_phase: Optional[str] = None):
    return semantic_search(query=q, fuel_phase=fuel_phase)

@app.get("/api/investigation/{psi_id}")
def api_investigation_detail(psi_id: str):
    detail = get_investigation_detail(psi_id)
    points, _ = qdrant.scroll(
        collection_name=Config.QDRANT_COLLECTION,
        scroll_filter=Filter(must=[FieldCondition(key="psi_id", match=MatchValue(value=psi_id))]),
        limit=5
    )
    detail["vector_notes"] = [p.payload for p in points]
    return detail

@app.get("/api/interpret")
def api_si_interpret(
    q: str,
    habitat: str = "lunar_base",
    fuel_phase: Optional[str] = None,
    ui_lang: str = "en"
):
    """Combina búsqueda vectorial en Qdrant + MySQL y responde en el idioma en que se preguntó."""
    o2_map = {"lunar_base": 30.0, "spacesuit": 100.0, "iss": 21.0}
    target_o2 = o2_map.get(habitat, 30.0)
    detected_lang = detect_query_language(q, fallback=ui_lang)

    vector_hits = semantic_search(query=q, fuel_phase=fuel_phase, top_k=3, lang=detected_lang)
    ranking = rank_investigations_by_habitat(target_o2)
    matched_psi_ids = [h["psi_id"] for h in vector_hits if h.get("psi_id")]

    related_tests = []
    for pid in matched_psi_ids[:3]:
        related_tests.extend(filter_tests(psi_id=pid, limit=6))
    # Si las investigaciones vectoriales no tienen corridas tabulares propias (ej. PSI-60), traer muestra general
    if not related_tests:
        related_tests = filter_tests(limit=8)

    top_hit = vector_hits[0] if vector_hits else None
    top_rank = ranking[0] if ranking else None

    if detected_lang == "es":
        fallback_summary = (
            f"Análisis SI para entorno '{habitat}' (referencia: {target_o2}% O₂): "
            + (f"La investigación con mayor afinidad semántica es {top_hit['psi_id']} ({top_hit['acronym']}, "
               f"pilar: {top_hit['safety_pillar']}, similitud {(top_hit['score']*100):.1f}%). " if top_hit else "")
            + (f"En el ranking atmosférico de MySQL lidera {top_rank['psi_id']} ({top_rank['acronym']}) "
               f"con hasta {top_rank['max_o2_tested_pct']}% O₂ evaluado (score {top_rank['relevance_score']}/100). " if top_rank else "")
            + "Nota de gravedad parcial: los límites entre 0g (ISS) y 1g acotan el riesgo lunar (0.16g) y marciano (0.38g)."
        )
    else:
        fallback_summary = (
            f"SI Analysis for '{habitat}' environment (reference threshold: {target_o2}% O₂): "
            + (f"The highest semantic match is {top_hit['psi_id']} ({top_hit['acronym']}, "
               f"pillar: {top_hit['safety_pillar']}, similarity {(top_hit['score']*100):.1f}%). " if top_hit else "")
            + (f"In the MySQL atmospheric ranking, {top_rank['psi_id']} ({top_rank['acronym']}) leads "
               f"with up to {top_rank['max_o2_tested_pct']}% O₂ tested (score {top_rank['relevance_score']}/100). " if top_rank else "")
            + "Partial-gravity note: 0g (ISS) and 1g results bound expected fire behavior in lunar (0.16g) and Martian (0.38g) gravity."
        )

    ai_interpretation = fallback_summary

    api_key = (Config.LLM_API_KEY or "").strip()

    if api_key:
        try:
            prompt = (
                "You are a NASA spacecraft fire safety specialist (Flame in Freefall project). "
                "CRITICAL RULE: Detect the language of 'User question' and write your ENTIRE response strictly in THAT exact language.\n"
                "Provide a thorough, structured technical analysis (220-320 words) organized with clear bullet points covering:\n"
                "1) Key experimental findings & physics in microgravity (0g),\n"
                "2) Quantitative comparison of O2%, pressure (psi), airflow, and burning/spread rates from the retrieved tests,\n"
                "3) Engineering implications for crew habitat safety and partial-gravity bounding (0g vs 1g).\n"
                "Ground every metric strictly in the retrieved data below:\n"
                f"User question: {q}\n"
                f"Target environment: {habitat} ({target_o2}% O2)\n"
                f"Qdrant semantic context: {json.dumps(vector_hits, ensure_ascii=False)}\n"
                f"Related MySQL test runs: {json.dumps(related_tests, ensure_ascii=False)}"
            )

            # Enrutamiento automático según el tipo de clave de Google
            if api_key.startswith("AQ."):
                # Clave de Vertex AI Express Mode (Google Cloud)
                url = f"https://aiplatform.googleapis.com/v1/publishers/google/models/gemini-2.5-flash:generateContent?key={api_key}"
            else:
                # Clave estándar de Google AI Studio (AIzaSy...)
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

            # ... (misma URL y payload, aumentando maxOutputTokens a 900)
            payload = json.dumps({
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.25,
                    "maxOutputTokens": 900
                }
            }).encode("utf-8")

            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                ai_interpretation = result["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="ignore")
            print(f"[Gemini API Error {e.code}]: {error_body}")
            ai_interpretation = fallback_summary
        except Exception as e:
            print(f"[Gemini Connection Error]: {e}")
            ai_interpretation = fallback_summary

    return {
        "query": q,
        "detected_lang": detected_lang,
        "habitat": habitat,
        "interpretation": ai_interpretation,
        "vector_matches": vector_hits,
        "related_tests": related_tests,
        "top_ranked_psi_id": top_rank["psi_id"] if top_rank else None
    }

app.mount("/", StaticFiles(directory=str(Config.DATA_DIR.parent), html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run("main_api:app", host="0.0.0.0", port=Config.API_PORT, reload=False)