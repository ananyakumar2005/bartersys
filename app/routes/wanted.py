from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import ItemRequest
from app.forms import ItemRequestForm

wanted_bp = Blueprint("wanted", __name__)


@wanted_bp.route("/")
def index():
    """Browse all wanted posts."""
    posts = ItemRequest.query.filter_by(fulfilled=False).order_by(ItemRequest.created_at.desc()).all()
    return render_template("wanted/index.html", posts=posts)


@wanted_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    """Create a new wanted post."""
    form = ItemRequestForm()
    if form.validate_on_submit():
        post = ItemRequest(
            user_id=current_user.id,
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
        )
        db.session.add(post)
        db.session.commit()
        flash("Wanted post created!", "success")
        return redirect(url_for("wanted.index"))
    return render_template("wanted/new.html", form=form)


@wanted_bp.route("/<int:post_id>/fulfill", methods=["POST"])
@login_required
def fulfill(post_id):
    """Mark a wanted post as fulfilled."""
    post = ItemRequest.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        from flask import abort
        abort(403)
    post.fulfilled = True
    db.session.commit()
    flash("Marked as fulfilled!", "success")
    return redirect(url_for("wanted.index"))
