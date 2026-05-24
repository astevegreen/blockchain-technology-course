import os

from app.app import create_app, socketio


app = create_app()


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    socketio.run(app, host=host, port=port, debug=app.config["DEBUG"])
