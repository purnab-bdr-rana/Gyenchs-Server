from db import db

class UserModel(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    profile_picture = db.Column(db.String(255))
    role = db.Column(db.String(80), nullable=False)
    verification_code = db.Column(db.Integer)
    code_sent_at = db.Column(db.DateTime)
    temp_new_password = db.Column(db.String(255))
    temp_new_email = db.Column(db.String(255))
    email_verification_code = db.Column(db.Integer)
    email_code_sent_at = db.Column(db.DateTime(timezone=True))
    code_verified = db.Column(db.Boolean, default=False)
    password = db.Column(db.String(255), nullable=True)

    wardrobe_items = db.relationship("WardrobeItemsModel", back_populates="user", lazy="dynamic", cascade="all, delete")
    outfits = db.relationship(
        "OutfitsModel",
        back_populates="user",
        cascade="all, delete",
        foreign_keys="[OutfitsModel.user_id]"
    )


