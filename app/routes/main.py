from flask import Blueprint, jsonify, render_template
from sqlalchemy import text
from app import db
from app.models import Item, ItemStatus

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Home / browse all available listings."""
    items = Item.query.filter_by(status=ItemStatus.AVAILABLE).order_by(Item.created_at.desc()).all()
    return render_template("main/index.html", items=items)


@main_bp.route("/healthz")
def healthz():
    """Lightweight health check endpoint that pings the database to keep both Render and Supabase active."""
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "degraded", "database_error": str(e)}), 500

