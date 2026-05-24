FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY instructor_auth ./instructor_auth
COPY app ./app
COPY tests ./tests
COPY --chmod=755 docker/entrypoint.sh /usr/local/bin/quiz-engine-entrypoint

RUN chmod +x /usr/local/bin/quiz-engine-entrypoint \
    && mkdir -p /data \
    && chown -R 10001:0 /app /data

USER 10001

ENV QUIZ_ENGINE_DB_PATH=/data/quiz-engine.sqlite
ENV QUIZ_ENGINE_TEST_INSTRUCTOR_HEADER=X-Test-Instructor

EXPOSE 8000

ENTRYPOINT ["/bin/sh", "/usr/local/bin/quiz-engine-entrypoint"]
CMD ["flask", "--app", "app:create_app", "run", "--host=0.0.0.0", "--port=8000"]
