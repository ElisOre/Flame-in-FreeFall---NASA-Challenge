from decimal import Decimal
from typing import List, Dict, Any, Optional
import mysql.connector
from src.config import Config

def get_connection():
    return mysql.connector.connect(**Config.MYSQL_CONFIG)

def _clean_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convierte Decimal a float para que FastAPI y FastMCP serialicen a JSON sin errores."""
    return [
        {k: (float(v) if isinstance(v, Decimal) else v) for k, v in row.items()}
        for row in rows
    ]

def filter_tests(
    psi_id: Optional[str] = None,
    fuel_material: Optional[str] = None,
    min_o2_pct: Optional[float] = None,
    max_pressure_psi: Optional[float] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    sql = """
        SELECT 
            t.*, i.acronym, i.title AS investigation_title, i.doi,
            i.safety_pillar, i.fuel_phase, i.hardware_rack, i.hardware_apparatus
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

    sql += " ORDER BY t.o2_percentage DESC, t.ambient_pressure_psi ASC LIMIT %s"
    params.append(limit)

    cursor.execute(sql, tuple(params))
    data = _clean_rows(cursor.fetchall())
    cursor.close()
    conn.close()
    return data

def rank_investigations_by_habitat(target_o2: float) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    # Compatible con MySQL 8+ ONLY_FULL_GROUP_BY
    sql = """
        SELECT 
            i.psi_id, i.acronym, i.title, i.doi, i.project_type, i.flight_platform,
            i.fuel_phase, i.safety_pillar, i.hardware_rack, i.hardware_apparatus,
            i.max_o2_tested_pct, i.simulates_partial_gravity,
            COUNT(t.test_uid) AS total_tests,
            ROUND(
                CASE WHEN i.max_o2_tested_pct >= %s THEN 40 ELSE (i.max_o2_tested_pct / %s) * 40 END +
                CASE WHEN i.simulates_partial_gravity = 1 THEN 30 ELSE 0 END +
                CASE WHEN i.safety_pillar IN ('Prevention', 'Suppression') THEN 30 ELSE 15 END, 1
            ) AS relevance_score
        FROM investigations i
        LEFT JOIN experimental_tests t ON i.psi_id = t.psi_id
        GROUP BY 
            i.psi_id, i.acronym, i.title, i.doi, i.project_type, i.flight_platform,
            i.fuel_phase, i.safety_pillar, i.hardware_rack, i.hardware_apparatus,
            i.max_o2_tested_pct, i.simulates_partial_gravity
        ORDER BY relevance_score DESC
    """
    cursor.execute(sql, (target_o2, target_o2))
    data = _clean_rows(cursor.fetchall())
    cursor.close()
    conn.close()
    return data

def get_investigation_detail(psi_id: str) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM investigations WHERE psi_id = %s", (psi_id,))
    inv_rows = _clean_rows(cursor.fetchall())
    investigation = inv_rows[0] if inv_rows else None

    tests = filter_tests(psi_id=psi_id, limit=50)
    cursor.close()
    conn.close()

    return {
        "investigation": investigation,
        "tests": tests
    }

def ensure_mysql_seeded():
    """Crea las tablas y carga los datos semilla en MySQL si la BD en la nube está vacía."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS investigations (
            psi_id VARCHAR(15) PRIMARY KEY,
            acronym VARCHAR(50) NOT NULL,
            title VARCHAR(255) NOT NULL,
            doi VARCHAR(100),
            project_type VARCHAR(50),
            flight_platform VARCHAR(100),
            fuel_phase VARCHAR(30),
            hardware_rack VARCHAR(100),
            hardware_apparatus VARCHAR(100),
            safety_pillar VARCHAR(50),
            simulates_partial_gravity TINYINT(1) DEFAULT 0,
            max_o2_tested_pct DECIMAL(5,2)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS experimental_tests (
            test_uid INT AUTO_INCREMENT PRIMARY KEY,
            psi_id VARCHAR(15),
            sample_or_test_id VARCHAR(100),
            fuel_material VARCHAR(100),
            sample_geometry VARCHAR(100),
            gravity_level VARCHAR(20),
            ambient_pressure_psi DECIMAL(6,2),
            o2_percentage DECIMAL(5,2),
            diluent_or_suppressant VARCHAR(50),
            airflow_velocity_cm_s DECIMAL(6,2),
            burning_or_spread_rate DECIMAL(8,4),
            test_outcome VARCHAR(100),
            FOREIGN KEY (psi_id) REFERENCES investigations(psi_id)
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM investigations")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT IGNORE INTO investigations VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            [
                ('PSI-60', 'SPICE Re-Analysis', 'Computational and Experimental Analysis of SPICE Data Sets', '10.60555/mzjm-yv57', 'Ground Investigation', 'Ground', 'Gaseous', 'MSG', 'SPICE Flow Duct', 'Predictive Modeling', 0, 21.00),
                ('PSI-69', 'FLEX', 'Flame Extinguishment Experiment', '10.60555/mbq8-0451', 'Microgravity Investigation', 'ISS', 'Liquid', 'CIR', 'MDCA', 'Suppression', 0, 30.00),
                ('PSI-25', 'BASS-II', 'Burning and Suppression of Solids - II', '10.60555/4qc4-de67', 'Microgravity Investigation', 'ISS', 'Solid', 'MSG', 'SPICE Flow Duct', 'Prevention', 0, 21.00),
                ('PSI-159', 'ACME CFI-G', 'Cool Flames Investigation with Gases', '10.60555/cyt1-kh64', 'Microgravity Investigation', 'ISS', 'Gaseous', 'CIR', 'ACME Burner', 'Prevention', 0, 85.00),
                ('PSI-EFIELD', 'ACME E-FIELD', 'Electric-Field Effects on Laminar Diffusion Flames', 'N/A', 'Microgravity Investigation', 'ISS', 'Gaseous', 'CIR', 'ACME High-Voltage Mesh', 'Predictive Modeling', 1, 21.00)
            ]
        )
        cursor.executemany(
            """INSERT INTO experimental_tests
               (psi_id, sample_or_test_id, fuel_material, sample_geometry, gravity_level,
                ambient_pressure_psi, o2_percentage, diluent_or_suppressant, airflow_velocity_cm_s,
                burning_or_spread_rate, test_outcome)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            [
                ('PSI-69', '20CAL08', 'Methanol', 'Droplet 1.69mm', '0g', 14.65, 21.00, 'N2', 0.0, 0.5200, 'Disruption'),
                ('PSI-69', '20CAL10', 'Methanol', 'Droplet 1.86mm', '0g', 14.73, 21.00, 'N2', 0.0, 0.6000, 'Extinction'),
                ('PSI-69', '30CAL02', 'Methanol', 'Droplet 2.06mm', '0g', 14.70, 21.00, 'CO2', 0.0, 0.6000, 'Extinction'),
                ('PSI-25', 'BASS2-PMMA-01', 'Acrylic PMMA', 'Rod', '0g', 14.70, 21.00, 'N2', 15.0, 1.2500, 'Steady Burn'),
                ('PSI-159', 'CFIG-HI-O2', 'Propane', 'Spherical Burner', '0g', 10.20, 85.00, 'N2', 5.0, 2.4000, 'Cool Flame Transition')
            ]
        )
        conn.commit()
        print("[MySQL] Tablas y datos semilla cargados automáticamente.")

    cursor.close()
    conn.close()

# Se ejecuta automáticamente al arrancar el servidor
ensure_mysql_seeded()