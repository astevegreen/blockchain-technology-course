FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

WORKDIR /app

COPY instructor_auth_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared /app/shared
COPY instructor_auth_service /app/instructor_auth_service
COPY hlf/web_ui/instructor_login.html /app/hlf/web_ui/instructor_login.html
COPY hlf/web_ui/instructor_sessions.html /app/hlf/web_ui/instructor_sessions.html

EXPOSE 8080

# The auth service is stateless, so multiple threaded workers are safe.
# This avoids the worker churn seen with a single sync worker under
# nginx auth_request fan-out.
CMD ["sh", "-c", "gunicorn --worker-class gthread --threads 4 --workers 2 --timeout 120 --graceful-timeout 30 --keep-alive 5 --access-logfile - --error-logfile - --bind 0.0.0.0:${PORT:-8080} instructor_auth_service.app:app"]
