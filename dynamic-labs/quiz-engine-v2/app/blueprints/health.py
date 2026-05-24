from flask import Blueprint, jsonify, redirect, url_for

from ..db import get_db

bp = Blueprint("health", __name__)


@bp.get("/")
def index():
    return redirect(url_for("student.student_home"))


@bp.get("/healthz")
def healthz():
    get_db().execute("SELECT 1")
    return jsonify(status="ok")
