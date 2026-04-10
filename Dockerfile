# syntax=docker/dockerfile:1
FROM python:3.11-slim

# ── System deps ──────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ────────────────────────
WORKDIR /app

# ── Install Python dependencies ──────────────
COPY server/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

# ── Copy project files ───────────────────────
COPY . /app/

# ── Non-root user (security best practice) ───
RUN useradd -m -u 1000 appuser && chown -R appuser /app
USER appuser

# ── Health check ─────────────────────────────
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# ── Expose port (HF Spaces requires 7860) ────
EXPOSE 7860

# ── Start server ─────────────────────────────
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
