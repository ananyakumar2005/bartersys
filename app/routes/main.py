from flask import Blueprint, render_template
from app.models import Item, ItemStatus

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Home / browse all available listings."""
    items = Item.query.filter_by(status=ItemStatus.AVAILABLE).order_by(Item.created_at.desc()).all()
    return render_template("main/index.html", items=items)
