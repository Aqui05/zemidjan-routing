# Construit avec le contexte = racine du repo (voir docker-compose.yml),
# car ce service a besoin a la fois de src/ (coeur de la simulation,
# partage avec les scripts main.py/tests) et de backend/app/ (l'API).
FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY backend/app ./app

ENV PYTHONPATH=/app/src
EXPOSE 8000

CMD ["uvicorn", "main:app", "--app-dir", "app", "--host", "0.0.0.0", "--port", "8000"]
