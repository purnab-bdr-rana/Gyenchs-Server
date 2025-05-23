from flask.views import MethodView
from flask_smorest import Blueprint, abort
from db import db
from models import WardrobeItemsModel, OutfitsModel, UserModel
from schemas import OutfitSchema
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import jwt_required, get_jwt_identity

from utils.outfits_recommendation import get_closest_item_by_hue

blp = Blueprint("outfits", __name__, description="Operations on recommended outfits")

@blp.route("/wardrobe-items/<int:item_id>/recommend")
class RecommendOutfit(MethodView):

    # recommend outfits
    @jwt_required()
    @blp.response(201, OutfitSchema)
    def post(self, item_id):
        user_id = get_jwt_identity()
        item = WardrobeItemsModel.query.filter_by(id=item_id, user_id=user_id).first()
        if not item:
            abort(404, message="Item not found.")
        all_items = WardrobeItemsModel.query.filter_by(user_id=user_id).all()

        kira = tego = wonju = None

        if item.type == "kira":
            kira = item
            tego = get_closest_item_by_hue(item.color, [i for i in all_items if i.type == "tego"])
            wonju = get_closest_item_by_hue(item.color, [i for i in all_items if i.type == "wonju"])
        elif item.type == "tego":
            tego = item
            kira = get_closest_item_by_hue(item.color, [i for i in all_items if i.type == "kira"])
            wonju = get_closest_item_by_hue(item.color, [i for i in all_items if i.type == "wonju"])
        elif item.type == "wonju":
            wonju = item
            kira = get_closest_item_by_hue(item.color, [i for i in all_items if i.type == "kira"])
            tego = get_closest_item_by_hue(item.color, [i for i in all_items if i.type == "tego"])
        else:
            abort(400, message="Invalid item type.")

        if not (kira and tego and wonju):
            abort(404, message="Not enough items to form an outfit.")

        # Check for existing outfit with same kira, tego, wonju
        existing_outfit = OutfitsModel.query.filter_by(
            user_id=user_id,
            kira_id=kira.id,
            tego_id=tego.id,
            wonju_id=wonju.id
        ).first()

        if existing_outfit:
            return existing_outfit

        # No duplicate found, create a new one
        outfit = OutfitsModel(
            user_id=user_id,
            kira_id=kira.id,
            tego_id=tego.id,
            wonju_id=wonju.id,
            favorite=False
        )

        try:
            db.session.add(outfit)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500, message=str(e))

        return outfit


# favorite / un-favorite
@blp.route("/outfits/<int:outfit_id>/favorite-unfavorite")
class FavoriteOutfit(MethodView):
    @jwt_required()
    def patch(self, outfit_id):
        user_id = get_jwt_identity()
        outfit = OutfitsModel.query.filter_by(id=outfit_id, user_id=user_id).first()
        if not outfit:
            abort(404, message="Outfit not found.")

        # Set this outfit as favorite
        outfit.favorite = not outfit.favorite
        try:
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500, message=str(e))

        if outfit.favorite:
            message = "You have favorite this outfit."
        else:
            message = "You have un-favorite this outfit."
        return {"message": message}


# get all outfits by user id
@blp.route("/user/outfits")
class AllUserOutfit(MethodView):
    @jwt_required()
    @blp.response(200, OutfitSchema(many=True))
    def get(self):
        user_id = get_jwt_identity()
        return OutfitsModel.query.filter_by(user_id=user_id).all()


# get all outfits by user id
@blp.route("/user/favorites")
class AllFavoriteOutfit(MethodView):
    @jwt_required()
    @blp.response(200, OutfitSchema(many=True))
    def get(self):
        user_id = get_jwt_identity()
        return OutfitsModel.query.filter_by(user_id=user_id, favorite=True).all()

# delete outfit by id
@blp.route("/outfit/<int:outfit_id>/delete")
class Outfit(MethodView):
    @jwt_required()
    def delete(self, outfit_id):
        outfit = OutfitsModel.query.get_or_404(outfit_id)

        db.session.delete(outfit)
        db.session.commit()

        return {"message": "Outfit deleted."}


# get outfit by id
@blp.route("/outfit/<int:outfit_id>/get")
class GetOutfit(MethodView):
    @jwt_required()
    @blp.response(200, OutfitSchema())
    def get(self, outfit_id):
        outfit = OutfitsModel.query.get_or_404(outfit_id)
        return outfit


# get lastest recommended outfits to show as a default
@blp.route("/user/recommended-outfit/default")
class GetLatestRecommendation(MethodView):

    @jwt_required()
    @blp.response(200, OutfitSchema)
    def get(self):
        user_id = get_jwt_identity()
        outfit = OutfitsModel.query.filter_by(user_id=user_id).order_by(OutfitsModel.id.desc()).first()
        if not outfit:
            abort(404, message="No recommendation found.")

        return outfit


# edit outfit by id
@blp.route("/outfit/<int:outfit_id>/edit")
class EditOutfit(MethodView):
    @jwt_required()
    @blp.arguments(OutfitSchema(partial=True))
    @blp.response(200, OutfitSchema())
    def patch(self, outfit_data, outfit_id):
        outfit = OutfitsModel.query.get(outfit_id)

        if not outfit:
            abort(404, message="Outfit not found.")

        # Update only the fields provided
        if "kira_id" in outfit_data:
            outfit.kira_id = outfit_data["kira_id"]
        if "tego_id" in outfit_data:
            outfit.tego_id = outfit_data["tego_id"]
        if "wonju_id" in outfit_data:
            outfit.wonju_id = outfit_data["wonju_id"]

        db.session.commit()
        return outfit


# create outfit
@blp.route("/outfit/create")
class CreateOutfit(MethodView):
    @jwt_required()
    @blp.arguments(OutfitSchema(only=("kira_id", "tego_id", "wonju_id")))
    @blp.response(201, OutfitSchema)
    def post(self, outfit_data):
        user_id = get_jwt_identity()
        kira_id = outfit_data["kira_id"]
        tego_id = outfit_data["tego_id"]
        wonju_id = outfit_data["wonju_id"]

        # Check for existing outfit with same kira, tego, wonju for this user
        existing_outfit = OutfitsModel.query.filter_by(
            user_id=user_id,
            kira_id=kira_id,
            tego_id=tego_id,
            wonju_id=wonju_id
        ).first()

        if existing_outfit:
            abort(400, message="Outfit already exists.")

        new_outfit = OutfitsModel(
            user_id=user_id,
            kira_id=kira_id,
            tego_id=tego_id,
            wonju_id=wonju_id
        )

        db.session.add(new_outfit)
        db.session.commit()

        return new_outfit
