from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from app import db
from app.models import Item, ItemImage, ItemStatus
from app.forms import ItemForm
from app.storage import upload_item_image, delete_item_images, ALLOWED_MIMETYPES, MAX_IMAGES

items_bp = Blueprint("items", __name__)


def _handle_image_uploads(item: Item) -> None:
    """
    Read all uploaded files from the multipart request, compress and upload
    each one to Supabase Storage, then persist ItemImage rows.
    Flashes a warning (but does not abort) for any individual failure.
    """
    files = request.files.getlist("images")
    uploaded = 0

    for f in files:
        if not f or not f.filename:
            continue
        if uploaded >= MAX_IMAGES:
            flash(f"Maximum {MAX_IMAGES} images per listing — extras were skipped.", "warning")
            break
        if f.mimetype not in ALLOWED_MIMETYPES:
            flash(f"'{f.filename}' is not a supported image type and was skipped.", "warning")
            continue

        try:
            public_url = upload_item_image(f.stream, current_user.id, item.id)
            db.session.add(ItemImage(item_id=item.id, image_path=public_url))
            uploaded += 1
        except Exception as exc:
            flash(f"Upload failed for '{f.filename}': {exc}", "warning")

    if uploaded:
        db.session.commit()


# ── Routes ─────────────────────────────────────────────────────────────────────

@items_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    """Create a new listing."""
    form = ItemForm()
    if form.validate_on_submit():
        item = Item(
            owner_id=current_user.id,
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            condition=form.condition.data,
        )
        db.session.add(item)
        db.session.commit()          # commit first so item.id exists for storage path

        _handle_image_uploads(item)  # compress → Supabase → ItemImage rows

        flash("Listing created!", "success")
        return redirect(url_for("items.detail", item_id=item.id))
    return render_template("items/new.html", form=form)


@items_bp.route("/<int:item_id>")
def detail(item_id):
    """Item detail page."""
    item = Item.query.get_or_404(item_id)
    return render_template("items/detail.html", item=item)


@items_bp.route("/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def edit(item_id):
    """Edit an existing listing — also appends any newly uploaded images."""
    item = Item.query.get_or_404(item_id)
    if item.owner_id != current_user.id:
        abort(403)

    form = ItemForm(obj=item)
    if form.validate_on_submit():
        item.title       = form.title.data
        item.description = form.description.data
        item.category    = form.category.data
        item.condition   = form.condition.data
        db.session.commit()

        _handle_image_uploads(item)  # append new photos if supplied

        flash("Listing updated.", "success")
        return redirect(url_for("items.detail", item_id=item.id))
    return render_template("items/edit.html", form=form, item=item)


@items_bp.route("/<int:item_id>/delete", methods=["POST"])
@login_required
def delete(item_id):
    """Delete listing + purge all its images from Supabase Storage."""
    item = Item.query.get_or_404(item_id)
    if item.owner_id != current_user.id:
        abort(403)

    # Collect URLs before cascade-delete removes the rows
    image_urls = [img.image_path for img in item.images]

    db.session.delete(item)
    db.session.commit()

    # Best-effort storage cleanup — don't let a storage failure surface to user
    try:
        delete_item_images(image_urls)
    except Exception:
        pass

    flash("Listing deleted.", "info")
    return redirect(url_for("dashboard.index"))
