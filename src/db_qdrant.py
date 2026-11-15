import json
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
from src.config import Config

# Conecta a Qdrant Cloud si hay URL en .env, o a la carpeta local si no la hay
if Config.QDRANT_URL:
    qdrant = QdrantClient(url=Config.QDRANT_URL, api_key=Config.QDRANT_API_KEY)
else:
    qdrant = QdrantClient(path=Config.QDRANT_PATH)

encoder = SentenceTransformer("all-MiniLM-L6-v2")

def ensure_qdrant_seeded():
    """Si la base vectorial no existe en esta PC/Servidor, la construye sola desde data/psi_knowledge.json"""
    if not qdrant.collection_exists(Config.QDRANT_COLLECTION):
        print("[Qdrant] Creando colección y cargando datos semilla desde data/psi_knowledge.json...")
        qdrant.create_collection(
            collection_name=Config.QDRANT_COLLECTION,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        with open(Config.JSON_SEED_FILE, "r", encoding="utf-8") as f:
            docs = json.load(f)
            
        points = [
            PointStruct(
                id=doc["id"],
                vector=encoder.encode(doc["text"]).tolist(),
                payload=doc
            )
            for doc in docs
        ]
        qdrant.upsert(collection_name=Config.QDRANT_COLLECTION, points=points)
        print(f"[Qdrant] {len(points)} documentos vectorizados automáticamente.")

# Se ejecuta automáticamente al arrancar el proyecto
ensure_qdrant_seeded()

def semantic_search(query: str, fuel_phase: Optional[str] = None, top_k: int = 4) -> List[Dict[str, Any]]:
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
    
    return [
        {
            "psi_id": h.payload.get("psi_id"),
            "acronym": h.payload.get("acronym"),
            "fuel_phase": h.payload.get("fuel_phase"),
            "safety_pillar": h.payload.get("safety_pillar"),
            "score": round(h.score, 4),
            "text": h.payload.get("text")
        }
        for h in hits
    ]