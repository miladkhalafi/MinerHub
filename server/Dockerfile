# Stage 1: Build frontend
FROM node:20-slim AS frontend-builder
WORKDIR /frontend
COPY server/frontend/package*.json ./
RUN npm install
COPY server/frontend/ ./
RUN npm run build

# Stage 2: Python app
FROM python:3.11-slim

WORKDIR /app

# Build context is project root (.)
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server/app ./app/
COPY agent/ ./agent/
COPY --from=frontend-builder /frontend/dist ./frontend/dist

EXPOSE 8000 3000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
