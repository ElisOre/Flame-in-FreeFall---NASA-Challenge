from typing import Optional
from fastmcp import FastMCP
from src.db_mysql import filter_tests, rank_investigations_by_habitat
from src.db_qdrant import semantic_search

mcp = FastMCP("NASA-FlameInFreefall-MCP")

@mcp.tool()
def search_psi_knowledge(query: str, fuel_phase: Optional[str] = None):
    """Busca conceptos científicos, objetivos, llamas frías y aplicaciones en la Tierra en Qdrant."""
    return semantic_search(query=query, fuel_phase=fuel_phase)

@mcp.tool()
def get_experimental_data(
    psi_id: Optional[str] = None,
    fuel_material: Optional[str] = None,
    min_o2_pct: Optional[float] = None,
    max_pressure_psi: Optional[float] = None
):
    """Obtiene pruebas numéricas exactas de presión (psi), oxígeno (%) y tasas de quemado desde MySQL."""
    return filter_tests(psi_id, fuel_material, min_o2_pct, max_pressure_psi)

@mcp.tool()
def rank_for_habitat(habitat: str = "lunar_base"):
    """Clasifica investigaciones para 'lunar_base' (30% O2, 10.2 psi), 'spacesuit' (100% O2) o 'iss' (21% O2)."""
    o2_map = {"lunar_base": 30.0, "spacesuit": 100.0, "iss": 21.0}
    target_o2 = o2_map.get(habitat, 30.0)
    return {
        "habitat": habitat,
        "target_o2_pct": target_o2,
        "ranking": rank_investigations_by_habitat(target_o2)
    }

if __name__ == "__main__":
    mcp.run()