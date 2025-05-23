
import traceback
import io
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import UserModel, WardrobeItemsModel
from schemas import WardrobeItemsSchema
from utils.image_classifier import ImageClassifier
from utils.cloudinary_upload import upload_image_to_cloudinary
from utils.color_extractor import get_dominant_color
from cloudinary.uploader import destroy
import re
from db import db
from utils.image_hash import calculate_image_hash
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from utils.remove_bg import remove_background

classifier = ImageClassifier()
blp = Blueprint("user_wardrobe", __name__, description="Wardrobe endpoints")

@blp.route("/user/wardrobe-items")
class UserWardrobeItems(MethodView):
    @jwt_required()
    @blp.response(200, WardrobeItemsSchema(many=True))
    def get(self):
        user_id = get_jwt_identity()
        user = UserModel.query.get_or_404(user_id)
        return user.wardrobe_items.all()

    @jwt_required()
    @blp.response(201, WardrobeItemsSchema)
    def post(self):
        user_id = get_jwt_identity()
        name = request.form.get("name")
        image_file = request.files.get("image")

        if not name or not image_file:
            abort(400, message="Both 'name' and 'image' are required.")

        try:
            # Step 1: Check for duplicate image using hash
            image_hash = calculate_image_hash(image_file)

            duplicate_item = WardrobeItemsModel.query.filter_by(
                user_id=user_id,
                image_hash=image_hash
            ).first()
            if duplicate_item:
                abort(400, message="This image has already been uploaded.")

            # Step 2: Remove background from image
            img_no_bg = remove_background(image_file)  # Should return PIL.Image

            # Step 3: Classify image type
            img_for_model = img_no_bg.convert("RGB")  # Ensure no alpha for model
            attire_type = classifier.predict_type(img_for_model)

            # Step 4: Extract dominant color
            color_hex = get_dominant_color(img_no_bg)

            # Step 5: Prepare image for upload
            temp_stream = io.BytesIO()
            img_no_bg.save(temp_stream, format="PNG")  # Preserve transparency
            temp_stream.seek(0)

            # Step 6: Upload to cloud
            image_url = upload_image_to_cloudinary(
                temp_stream,
                user_id,
                subfolder="attire",
                is_unique=True
            )

            # Step 7: Save record to DB
            wardrobe_item = WardrobeItemsModel(
                name=name,
                type=attire_type,
                color=color_hex,
                image_url=image_url,
                user_id=user_id,
                image_hash=image_hash
            )

            db.session.add(wardrobe_item)
            db.session.commit()
            return wardrobe_item

        except SQLAlchemyError as e:
            traceback.print_exc()
            abort(500, message=f"Database error: {str(e)}")

        except ValueError as e:
            traceback.print_exc()
            abort(400, message=f"Validation error: {str(e)}")

        except Exception as e:
            traceback.print_exc()
            abort(500, message=f"Internal Server Error:\n{traceback.format_exc()}")


# upload
@blp.route("/wardrobe-items/<int:item_id>")
class WardrobeItem(MethodView):
    @jwt_required()
    @blp.response(200, WardrobeItemsSchema)
    def patch(self, item_id):
        item = WardrobeItemsModel.query.filter_by(id=item_id).first()
        if not item:
            abort(404, message="Wardrobe item not found.")

        # Accept both form-data and JSON input
        new_name = (
            request.form.get("name") or
            request.json.get("name") if request.is_json else None
        )

        if not new_name:
            abort(400, message="Field 'name' is required for update.")

        item.name = new_name
        try:
            db.session.commit()
            return item
        except SQLAlchemyError as e:
            abort(500, message=str(e))

    @jwt_required()
    def delete(self, item_id):
        item = WardrobeItemsModel.query.get_or_404(item_id)

        # Extract public_id from image_url
        try:
            match = re.search(r"upload\/(?:v\d+\/)?(.+?)\.(jpg|png|jpeg|webp)", item.image_url)
            if match:
                public_id = match.group(1)
                destroy(public_id)
        except Exception as e:
            print(f"Warning: Failed to delete Cloudinary image: {str(e)}")

        try:
            db.session.delete(item)
            db.session.commit()
            return {"message": "Item deleted successfully."}
        except IntegrityError as e:
            db.session.rollback()
            abort(400,
                  message=f"Oops! You can’t delete this item yet — it's still part of an outfit using this {item.type}. Please remove that outfit first to proceed.")
        except SQLAlchemyError as e:
            db.session.rollback()
            abort(500, message="An unexpected database error occurred: " + str(e))