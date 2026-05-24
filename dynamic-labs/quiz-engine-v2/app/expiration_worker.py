import atexit
import threading

from .attempts import finalize_expired_attempts


class ExpirationWorker:
    def __init__(self, app):
        self.app = app
        self.interval_seconds = float(app.config["EXPIRATION_WORKER_INTERVAL_SECONDS"])
        self.batch_size = int(app.config["EXPIRATION_WORKER_BATCH_SIZE"])
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            name="quiz-engine-expiration-worker",
            daemon=True,
        )

    def start(self):
        self._thread.start()

    def stop(self, timeout=2):
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout=timeout)

    def _run(self):
        while not self._stop.wait(self.interval_seconds):
            with self.app.app_context():
                finalize_expired_attempts(limit=self.batch_size)


def init_app(app):
    app.extensions["expiration_worker"] = None
    if app.config["TESTING"] or not app.config["EXPIRATION_WORKER_ENABLED"]:
        return
    worker = ExpirationWorker(app)
    app.extensions["expiration_worker"] = worker
    worker.start()
    atexit.register(worker.stop)
