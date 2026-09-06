from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Item, BarterRequest, ItemRequest

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    """User dashboard — own listings, incoming & sent requests, wanted posts."""
    my_items = current_user.items.order_by(Item.created_at.desc()).all()
    incoming = (
        BarterRequest.query
        .join(Item, BarterRequest.item_id == Item.id)
        .filter(Item.owner_id == current_user.id)
        .order_by(BarterRequest.created_at.desc())
        .all()
    )
    sent = current_user.sent_requests.order_by(BarterRequest.created_at.desc()).all()
    wanted = current_user.wanted_posts.order_by(ItemRequest.created_at.desc()).all()

    return render_template(
        "dashboard/index.html",
        my_items=my_items,
        incoming=incoming,
        sent=sent,
        wanted=wanted,
    )
