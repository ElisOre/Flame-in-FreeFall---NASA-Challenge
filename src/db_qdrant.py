import json
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
from src.config import Config

if Config.QDRANT_URL:
    qdrant = QdrantClient(url=Config.QDRANT_URL, api_key=Config.QDRANT_API_KEY)
else:
    qdrant = QdrantClient(path=Config.QDRANT_PATH)

encoder = SentenceTransformer("all-MiniLM-L6-v2")

def ensure_qdrant_seeded():
    """Crea o actualiza la colección vectorial si aún no tiene el esquema bilingüe (text_en / text_es)."""
    needs_seed = False

    if not qdrant.collection_exists(Config.QDRANT_COLLECTION):
        needs_seed = True
    else:
        existing_points, _ = qdrant.scroll(collection_name=Config.QDRANT_COLLECTION, limit=1)
        if not existing_points or "text_en" not in existing_points[0].payload:
            qdrant.delete_collection(Config.QDRANT_COLLECTION)
            needs_seed = True

    if needs_seed:
        print("[Qdrant] Cargando datos semilla bilingües desde data/psi_knowledge.json...")
        qdrant.create_collection(
            collection_name=Config.QDRANT_COLLECTION,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
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
                    vector=encoder.encode(combined_text).tolist(),
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
    query_vec = encoder.encode(query).tolist()
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