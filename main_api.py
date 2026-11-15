import json
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
def api_si_interpret(q: str, habitat: str = "lunar_base", fuel_phase: Optional[str] = None):
    """Combina búsqueda vectorial en Qdrant + datos tabulares en MySQL + síntesis SI."""
    o2_map = {"lunar_base": 30.0, "spacesuit": 100.0, "iss": 21.0}
    target_o2 = o2_map.get(habitat, 30.0)

    vector_hits = semantic_search(query=q, fuel_phase=fuel_phase, top_k=3)
    ranking = rank_investigations_by_habitat(target_o2)
    matched_psi_ids = [h["psi_id"] for h in vector_hits if h.get("psi_id")]

    related_tests = []
    for pid in matched_psi_ids[:2]:
        related_tests.extend(filter_tests(psi_id=pid, limit=5))

    # Síntesis estructurada respaldada por los datos reales de MySQL y Qdrant
    top_hit = vector_hits[0] if vector_hits else None
    top_rank = ranking[0] if ranking else None

    fallback_summary = (
        f"Análisis SI para entorno '{habitat}' (objetivo referencia: {target_o2}% O₂): "
        + (f"La investigación con mayor afinidad semántica es {top_hit['psi_id']} ({top_hit['acronym']}, "
           f"pilar: {top_hit['safety_pillar']}, similitud {(top_hit['score']*100):.1f}%). " if top_hit else "")
        + (f"En el ranking atmosférico de MySQL lidera {top_rank['psi_id']} ({top_rank['acronym']}) "
           f"con hasta {top_rank['max_o2_tested_pct']}% O₂ evaluado y score {top_rank['relevance_score']}/100. " if top_rank else "")
        + "Nota de gravedad parcial: los límites entre 0g (ISS) y 1g acotan el riesgo lunar (0.16g) y marciano (0.38g)."
    )

    ai_interpretation = fallback_summary

    # Si hay LLM_API_KEY (Gemini) en .env, enriquecemos la redacción usando el contexto recuperado
    if Config.LLM_API_KEY and Config.LLM_API_KEY.startswith("AIza"):
        try:
            prompt = (
                "Eres un especialista de seguridad contra incendios espaciales de la NASA (proyecto Flame in Freefall). "
                "Responde en español, de forma concisa y técnica (máximo 110 palabras), usando SOLO estos datos recuperados:\n"
                f"Pregunta del usuario: {q}\n"
                f"Entorno objetivo: {habitat} ({target_o2}% O2)\n"
                f"Contexto Qdrant: {json.dumps(vector_hits, ensure_ascii=False)}\n"
                f"Pruebas MySQL relacionadas: {json.dumps(related_tests[:4], ensure_ascii=False)}"
            )
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={Config.LLM_API_KEY}"
            payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                ai_interpretation = result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            ai_interpretation = fallback_summary

    return {
        "query": q,
        "habitat": habitat,
        "interpretation": ai_interpretation,
        "vector_matches": vector_hits,
        "related_tests": related_tests,
        "top_ranked_psi_id": top_rank["psi_id"] if top_rank else None
    }

# Sirve index.html, css/ y js/ directamente desde http://localhost:8000 (siempre al final)
app.mount("/", StaticFiles(directory=str(Config.DATA_DIR.parent), html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run("main_api:app", host="0.0.0.0", port=Config.API_PORT, reload=False)