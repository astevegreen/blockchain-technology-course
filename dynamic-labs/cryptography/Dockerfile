FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir streamlit cryptography

RUN useradd -m student
USER student
WORKDIR /home/student/lab

COPY --chown=student:student Lab_2_Home.py lab_core.py lesson_loader.py progress_beacon.py terminal_ui.py STUDENT_README.md ./
COPY --chown=student:student pages/ ./pages/
COPY --chown=student:student lessons/ ./lessons/
COPY --chown=student:student .streamlit/ ./.streamlit/

EXPOSE 8501

CMD ["streamlit", "run", "Lab_2_Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
