from db import db

class OutfitsModel(db.Model):
    __tablename__ = "outfits"

    id = db.Column(db.Integer, primary_key=True)
    favorite = db.Column(db.Boolean, nullable=False, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    kira_id = db.Column(db.Integer, db.ForeignKey("wardrobe_items.id", ondelete="CASCADE"), nullable=False)
    tego_id = db.Column(db.Integer, db.ForeignKey("wardrobe_items.id", ondelete="CASCADE"), nullable=False)
    wonju_id = db.Column(db.Integer, db.ForeignKey("wardrobe_items.id", ondelete="CASCADE"), nullable=False)

    user = db.relationship("UserModel", back_populates="outfits")
    kira = db.relationship("WardrobeItemsModel", foreign_keys=[kira_id], backref="used_in_kira")
    tego = db.relationship("WardrobeItemsModel", foreign_keys=[tego_id], backref="used_in_tego")
    wonju = db.relationship("WardrobeItemsModel", foreign_keys=[wonju_id], backref="used_in_wonju")
