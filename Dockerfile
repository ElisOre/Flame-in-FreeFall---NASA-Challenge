FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias para MySQL y compilación ligera
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-descargar el modelo de SentenceTransformers en la imagen para arranque instantáneo
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copiar todo el proyecto (respeta .gitignore; nunca sube .env)
COPY . .

# Puerto estándar de Hugging Face Spaces
ENV API_PORT=7860
EXPOSE 7860

CMD ["python", "main_api.py"]