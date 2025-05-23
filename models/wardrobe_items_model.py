from db import db
from sqlalchemy import Enum

class WardrobeItemsModel(db.Model):
    __tablename__ = "wardrobe_items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(Enum("kira", "tego", "wonju", name="item_type"), nullable=False)
    image_url = db.Column(db.String(255))
    color = db.Column(db.String(80), nullable=False)
    image_hash = db.Column(db.String(64), nullable=False, unique=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=False, nullable=False)

    user = db.relationship("UserModel", back_populates="wardrobe_items")
