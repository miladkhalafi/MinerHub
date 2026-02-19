FROM python:3.11-slim

WORKDIR /app

# Build context is project root (.)
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server/app ./app/
COPY agent/ ./agent/
COPY server/frontend/ ./frontend/
RUN if [ -f frontend/package.json ]; then \
      cd frontend && npm install && npm run build && cd ..; \
    fi

EXPOSE 8000 3000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
