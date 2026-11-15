from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from src.config import Config
from src.db_mysql import filter_tests, rank_investigations_by_habitat
from src.db_qdrant import semantic_search

app = FastAPI(title="NASA Flame in FreeFall dashboard API")

# Permite que el frontend consuma los datos sin bloqueo por CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/ranking")
def api_get_ranking(habitat: str = "lunar_base"):
    """Endpoint para la tabla de Ranking de la página web"""
    o2_map = {"lunar_base": 30.0, "spacesuit": 100.0, "iss": 21.0}
    return rank_investigations_by_habitat(o2_map.get(habitat, 30.0))

@app.get("/api/tests")
def api_get_tests(
    psi_id: Optional[str] = None,
    fuel_material: Optional[str] = None,
    min_o2_pct: Optional[float] = None,
    max_pressure_psi: Optional[float] = None
):
    """Endpoint para alimentar los gráficos de dispersión (% O2 vs Presión PSI)"""
    return filter_tests(psi_id, fuel_material, min_o2_pct, max_pressure_psi)

@app.get("/api/search")
def api_semantic_search(q: str, fuel_phase: Optional[str] = None):
    """Endpoint para el buscador inteligente con IA/Qdrant"""
    return semantic_search(query=q, fuel_phase=fuel_phase)

if __name__ == "__main__":
    uvicorn.run("main_api:app", host="0.0.0.0", port=Config.API_PORT, reload=False)