from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.models import BarterRequest, Item, RequestStatus, ItemStatus
from app.forms import BarterRequestForm

requests_bp = Blueprint("requests", __name__)


@requests_bp.route("/send/<int:item_id>", methods=["GET", "POST"])
@login_required
def send(item_id):
    """Create a barter request for an item."""
    item = Item.query.get_or_404(item_id)
    if item.owner_id == current_user.id:
        flash("You cannot request your own item.", "warning")
        return redirect(url_for("items.detail", item_id=item_id))
    if item.status != ItemStatus.AVAILABLE:
        flash("This item is not available for barter.", "warning")
        return redirect(url_for("items.detail", item_id=item_id))

    form = BarterRequestForm()
    # Populate offered items dropdown with requester's available items
    form.offered_item_id.choices = [
        (i.id, i.title)
        for i in current_user.items.filter_by(status=ItemStatus.AVAILABLE).all()
    ]
    form.offered_item_id.choices.insert(0, (0, "— No specific item offered —"))

    if form.validate_on_submit():
        offered = form.offered_item_id.data or None
        req = BarterRequest(
            requester_id=current_user.id,
            item_id=item.id,
            offered_item_id=offered if offered else None,
            message=form.message.data,
        )
        db.session.add(req)
        db.session.commit()
        flash("Barter request sent!", "success")
        return redirect(url_for("requests.sent"))
    return render_template("requests/send.html", form=form, item=item)


@requests_bp.route("/incoming")
@login_required
def incoming():
    """Requests made to the current user's items."""
    reqs = (
        BarterRequest.query
        .join(Item, BarterRequest.item_id == Item.id)
        .filter(Item.owner_id == current_user.id)
        .order_by(BarterRequest.created_at.desc())
        .all()
    )
    return render_template("requests/incoming.html", requests=reqs)


@requests_bp.route("/sent")
@login_required
def sent():
    """Requests the current user has made."""
    reqs = (
        current_user.sent_requests
        .order_by(BarterRequest.created_at.desc())
        .all()
    )
    return render_template("requests/sent.html", requests=reqs)


@requests_bp.route("/<int:req_id>/accept", methods=["POST"])
@login_required
def accept(req_id):
    req = BarterRequest.query.get_or_404(req_id)
    if req.item.owner_id != current_user.id:
        abort(403)
    if req.status != RequestStatus.PENDING:
        flash("This request is no longer pending.", "warning")
        return redirect(url_for("requests.incoming"))
    req.status = RequestStatus.ACCEPTED
    req.item.status = ItemStatus.TRADED
    if req.offered_item:
        req.offered_item.status = ItemStatus.TRADED
    db.session.commit()
    flash("Request accepted! Trade confirmed.", "success")
    return redirect(url_for("requests.incoming"))


@requests_bp.route("/<int:req_id>/reject", methods=["POST"])
@login_required
def reject(req_id):
    req = BarterRequest.query.get_or_404(req_id)
    if req.item.owner_id != current_user.id:
        abort(403)
    if req.status != RequestStatus.PENDING:
        flash("This request is no longer pending.", "warning")
        return redirect(url_for("requests.incoming"))
    req.status = RequestStatus.REJECTED
    db.session.commit()
    flash("Request rejected.", "info")
    return redirect(url_for("requests.incoming"))
