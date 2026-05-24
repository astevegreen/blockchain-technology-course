FROM node:20-alpine AS socketio-client-build

WORKDIR /vendor

RUN npm init -y
RUN npm install socket.io-client@4.7.5
RUN mkdir -p /build/vendor
RUN cp /vendor/node_modules/socket.io-client/dist/socket.io.min.js /build/vendor/socket.io.min.js

FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "from importlib.metadata import version; assert version('python-socketio').startswith('5.'); assert version('python-engineio').startswith('4.')"

# Copy application files
COPY app.py .
COPY word_bank.py .
COPY instructor_auth/ ./instructor_auth/
COPY templates/ ./templates/
COPY --from=socketio-client-build /build/vendor/ ./static/vendor/

# Expose the port Gunicorn will listen on
EXPOSE 5000

# Run the application using Gunicorn with Eventlet workers for Socket.IO
# support. Disable Gunicorn's hard timeout because Socket.IO long-poll and
# websocket sessions can legitimately outlive the default 30s window.
CMD ["gunicorn", "-k", "eventlet", "-w", "1", "--timeout", "0", "--graceful-timeout", "30", "--access-logfile", "-", "--error-logfile", "-", "--bind", "0.0.0.0:5000", "app:app"]
