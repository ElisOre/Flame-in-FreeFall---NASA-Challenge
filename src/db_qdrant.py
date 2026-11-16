import hashlib
import json
import math
import re
import urllib.request
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from src.config import Config

VECTOR_SIZE = 384

if Config.QDRANT_URL:
    qdrant = QdrantClient(url=Config.QDRANT_URL, api_key=Config.QDRANT_API_KEY)
else:
    qdrant = QdrantClient(path=Config.QDRANT_PATH)

def _local_fallback_embedding(text: str, dim: int = VECTOR_SIZE) -> List[float]:
    """Vectorizador ligero por n-gramas y palabras clave en Python puro (0 MB de RAM extra)."""
    vec = [0.0] * dim
    tokens = re.findall(r"[a-z0-9áéíóúñ]+", text.lower())
    for tok in tokens:
        idx = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16) % dim
        vec[idx] += 1.0
        if len(tok) >= 4:
            for i in range(len(tok) - 2):
                gram = tok[i:i+3]
                g_idx = int(hashlib.md5(gram.encode("utf-8")).hexdigest(), 16) % dim
                vec[g_idx] += 0.5
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]

def get_embedding(text: str) -> List[float]:
    """Obtiene embeddings de 384 dimensiones vía Gemini API con respaldo local automático."""
    api_key = (Config.LLM_API_KEY or "").strip()
    if api_key and not api_key.startswith("AQ."):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={api_key}"
            payload = json.dumps({
                "model": "models/gemini-embedding-001",
                "content": {"parts": [{"text": text}]},
                "outputDimensionality": VECTOR_SIZE
            }).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                values = data.get("embedding", {}).get("values")
                if values and len(values) == VECTOR_SIZE:
                    return values
        except Exception:
            pass
    return _local_fallback_embedding(text)

def ensure_qdrant_seeded():
    """Crea o actualiza la colección vectorial con los datos semilla bilingües."""
    needs_seed = False

    if not qdrant.collection_exists(Config.QDRANT_COLLECTION):
        needs_seed = True
    else:
        existing_points, _ = qdrant.scroll(collection_name=Config.QDRANT_COLLECTION, limit=1)
        if (
            not existing_points
            or "text_en" not in existing_points[0].payload
            or len(existing_points[0].vector or []) != VECTOR_SIZE
        ):
            qdrant.delete_collection(Config.QDRANT_COLLECTION)
            needs_seed = True

    if needs_seed:
        print("[Qdrant] Cargando datos semilla bilingües desde data/psi_knowledge.json...")
        qdrant.create_collection(
            collection_name=Config.QDRANT_COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )
        with open(Config.JSON_SEED_FILE, "r", encoding="utf-8") as f:
            docs = json.load(f)

        points = []
        for doc in docs:
            combined_text = f"{doc['text_en']} {doc['text_es']}"
            payload = {**doc, "text": doc["text_en"]}
            points.append(
                PointStruct(
                    id=doc["id"],
                    vector=get_embedding(combined_text),
                    payload=payload
                )
            )
        qdrant.upsert(collection_name=Config.QDRANT_COLLECTION, points=points)
        print(f"[Qdrant] {len(points)} documentos bilingües vectorizados automáticamente.")

ensure_qdrant_seeded()

def semantic_search(
    query: str,
    fuel_phase: Optional[str] = None,
    top_k: int = 4,
    lang: str = "en"
) -> List[Dict[str, Any]]:
    query_vec = get_embedding(query)
    q_filter = None
    if fuel_phase:
        q_filter = Filter(must=[FieldCondition(key="fuel_phase", match=MatchValue(value=fuel_phase))])

    hits = qdrant.query_points(
        collection_name=Config.QDRANT_COLLECTION,
        query=query_vec,
        query_filter=q_filter,
        limit=top_k
    ).points

    results = []
    for h in hits:
        text_en = h.payload.get("text_en") or h.payload.get("text", "")
        text_es = h.payload.get("text_es") or text_en
        results.append({
            "psi_id": h.payload.get("psi_id"),
            "acronym": h.payload.get("acronym"),
            "fuel_phase": h.payload.get("fuel_phase"),
            "safety_pillar": h.payload.get("safety_pillar"),
            "score": round(h.score, 4),
            "text_en": text_en,
            "text_es": text_es,
            "text": text_es if lang == "es" else text_en
        })
    return results