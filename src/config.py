import os
from pathlib import Path
from dotenv import load_dotenv

# Calcula la carpeta raíz del proyecto automáticamente
BASE_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = BASE_DIR

# Carga las variables del archivo .env ubicado en la raíz
load_dotenv(BASE_DIR / ".env")

class Config:
    # Rutas de archivos semilla (los que SÍ van en GitHub para alimentar la web)
    DATA_DIR = BASE_DIR / "data"
    SQL_SEED_FILE = DATA_DIR / "init_mysql.sql"
    JSON_SEED_FILE = DATA_DIR / "psi_knowledge.json"

    # Credenciales de MySQL
    MYSQL_CONFIG = {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", 3306)),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "Flame_in_FreeFall_NASA_Challenge")
    }

    # Configuración de Qdrant
    QDRANT_PATH = str(BASE_DIR / os.getenv("QDRANT_PATH", "qdrant_psi_db"))
    QDRANT_URL = os.getenv("QDRANT_URL", "").strip()
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "").strip()
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "psi_combustion_knowledge")

    # IA y Servidor Web
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    API_PORT = int(os.getenv("API_PORT", 8000))