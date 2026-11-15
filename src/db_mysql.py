from decimal import Decimal
from typing import List, Dict, Any, Optional
import mysql.connector
from src.config import Config

def get_connection():
    return mysql.connector.connect(**Config.MYSQL_CONFIG)

def _clean_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convierte Decimal a float para que FastAPI y FastMCP puedan serializar a JSON."""
    return [
        {k: (float(v) if isinstance(v, Decimal) else v) for k, v in row.items()}
        for row in rows
    ]

def filter_tests(
    psi_id: Optional[str] = None,
    fuel_material: Optional[str] = None,
    min_o2_pct: Optional[float] = None,
    max_pressure_psi: Optional[float] = None,
    limit: int = 25
) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    sql = """
        SELECT t.*, i.acronym, i.safety_pillar 
        FROM experimental_tests t
        JOIN investigations i ON t.psi_id = i.psi_id
        WHERE 1=1
    """
    params = []
    if psi_id:
        sql += " AND t.psi_id = %s"
        params.append(psi_id)
    if fuel_material:
        sql += " AND t.fuel_material LIKE %s"
        params.append(f"%{fuel_material}%")
    if min_o2_pct is not None:
        sql += " AND t.o2_percentage >= %s"
        params.append(min_o2_pct)
    if max_pressure_psi is not None:
        sql += " AND t.ambient_pressure_psi <= %s"
        params.append(max_pressure_psi)
        
    sql += " ORDER BY t.o2_percentage DESC LIMIT %s"
    params.append(limit)
    
    cursor.execute(sql, tuple(params))
    data = _clean_rows(cursor.fetchall())
    cursor.close()
    conn.close()
    return data

def rank_investigations_by_habitat(target_o2: float) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT 
            i.psi_id, i.acronym, i.title, i.fuel_phase, i.safety_pillar,
            i.hardware_rack, i.max_o2_tested_pct, i.simulates_partial_gravity,
            COUNT(t.test_uid) AS total_tests,
            ROUND(
                CASE WHEN i.max_o2_tested_pct >= %s THEN 40 ELSE (i.max_o2_tested_pct / %s) * 40 END +
                CASE WHEN i.simulates_partial_gravity = 1 THEN 30 ELSE 0 END +
                CASE WHEN i.safety_pillar IN ('Prevention', 'Suppression') THEN 30 ELSE 15 END, 1
            ) AS relevance_score
        FROM investigations i
        LEFT JOIN experimental_tests t ON i.psi_id = t.psi_id
        GROUP BY i.psi_id
        ORDER BY relevance_score DESC
    """
    cursor.execute(sql, (target_o2, target_o2))
    data = _clean_rows(cursor.fetchall())
    cursor.close()
    conn.close()
    return data