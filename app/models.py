from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


# ---------------------------------------------------------------------------
# Hostel
# ---------------------------------------------------------------------------

class Hostel(db.Model):
    __tablename__ = "hostels"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)

    users = db.relationship("User", back_populates="hostel", lazy="dynamic")

    def __repr__(self):
        return f"<Hostel {self.name}>"


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    hostel_id = db.Column(db.Integer, db.ForeignKey("hostels.id"), nullable=True)
    profile_pic = db.Column(db.Text, nullable=True)  # Supabase Storage URL
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    hostel = db.relationship("Hostel", back_populates="users")
    items = db.relationship("Item", back_populates="owner", lazy="dynamic",
                            foreign_keys="Item.owner_id")
    sent_requests = db.relationship("BarterRequest", back_populates="requester",
                                    lazy="dynamic", foreign_keys="BarterRequest.requester_id")
    wanted_posts = db.relationship("ItemRequest", back_populates="user", lazy="dynamic")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------------------------------------------------------------------
# Item (Listing)
# ---------------------------------------------------------------------------

class ItemStatus:
    AVAILABLE = "available"
    TRADED = "traded"
    PENDING = "pending"

    ALL = [AVAILABLE, TRADED, PENDING]


class Item(db.Model):
    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(80), nullable=True, index=True)
    condition = db.Column(db.String(40), nullable=True)  # e.g. "new", "good", "fair"
    status = db.Column(db.String(20), nullable=False, default=ItemStatus.AVAILABLE, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    owner = db.relationship("User", back_populates="items", foreign_keys=[owner_id])
    images = db.relationship("ItemImage", back_populates="item", cascade="all, delete-orphan",
                             lazy="select")
    incoming_requests = db.relationship("BarterRequest", back_populates="item",
                                        lazy="dynamic", foreign_keys="BarterRequest.item_id")

    def __repr__(self):
        return f"<Item {self.id}: {self.title}>"


# ---------------------------------------------------------------------------
# ItemImage
# ---------------------------------------------------------------------------

class ItemImage(db.Model):
    __tablename__ = "item_images"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    image_path = db.Column(db.Text, nullable=False)  # Supabase Storage public/signed URL

    item = db.relationship("Item", back_populates="images")

    def __repr__(self):
        return f"<ItemImage {self.id} for item {self.item_id}>"


# ---------------------------------------------------------------------------
# BarterRequest
# ---------------------------------------------------------------------------

class RequestStatus:
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

    ALL = [PENDING, ACCEPTED, REJECTED, CANCELLED]


class BarterRequest(db.Model):
    __tablename__ = "barter_requests"

    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    offered_item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=True)
    status = db.Column(db.String(20), nullable=False, default=RequestStatus.PENDING, index=True)
    message = db.Column(db.Text, nullable=True)  # Optional note from requester
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    requester = db.relationship("User", back_populates="sent_requests",
                                foreign_keys=[requester_id])
    item = db.relationship("Item", back_populates="incoming_requests",
                           foreign_keys=[item_id])
    offered_item = db.relationship("Item", foreign_keys=[offered_item_id])

    def __repr__(self):
        return f"<BarterRequest {self.id} [{self.status}]>"


# ---------------------------------------------------------------------------
# ItemRequest (Wanted board)
# ---------------------------------------------------------------------------

class ItemRequest(db.Model):
    __tablename__ = "item_requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(80), nullable=True, index=True)
    fulfilled = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="wanted_posts")

    def __repr__(self):
        return f"<ItemRequest {self.id}: {self.title}>"
