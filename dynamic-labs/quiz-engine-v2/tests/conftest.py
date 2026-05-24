import pytest

from app import create_app
from app.db import init_db


@pytest.fixture
def app_factory(tmp_path):
    def build_app(**overrides):
        config = {
            "DATABASE_PATH": str(tmp_path / "quiz-engine-test.sqlite"),
            "SECRET_KEY": "test-secret",
            "TESTING": True,
            "INSTRUCTOR_AUTH_MODE": "test-header",
            "TEST_INSTRUCTOR_HEADER": "X-Test-Instructor",
        }
        config.update(overrides)
        app = create_app(config)
        with app.app_context():
            init_db()
        return app

    return build_app


@pytest.fixture
def app(app_factory):
    return app_factory()


@pytest.fixture
def client(app):
    return app.test_client()
