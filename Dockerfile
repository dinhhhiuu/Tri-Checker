# ── Build stage ─────────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Only copy what the server needs (no pygame, no ML models)
COPY requirements-server.txt ./
RUN pip install --no-cache-dir -r requirements-server.txt

COPY src/core/   src/core/
COPY src/network/ src/network/
COPY server.py   ./

# Railway / Render inject PORT via environment variable
ENV PORT=5000
EXPOSE 5000

CMD ["python", "server.py", "--host", "0.0.0.0"]
