FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=5000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "from importlib.metadata import version; assert version('python-socketio').startswith('5.'); assert version('python-engineio').startswith('4.')"

COPY run.py ./
COPY app/ ./app/

RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

# This app keeps all room state in memory, so it must stay on a single
# worker. Disable Gunicorn's hard timeout because Socket.IO long-poll and
# websocket sessions can legitimately outlive the default 30s window.
CMD ["sh", "-c", "gunicorn --worker-class eventlet --workers 1 --timeout 0 --graceful-timeout 30 --bind 0.0.0.0:${PORT:-5000} --access-logfile - --error-logfile - run:app"]
