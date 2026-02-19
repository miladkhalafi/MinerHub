FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY agent/ ./agent/

# Install frontend dependencies and build (if frontend exists)
COPY frontend/ ./frontend/
RUN if [ -f frontend/package.json ]; then \
      cd frontend && npm install && npm run build && cd ..; \
    fi

EXPOSE 8000 3000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
