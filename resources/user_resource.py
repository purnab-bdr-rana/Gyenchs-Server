from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from db import db
from schemas import UserSchema, UserUpdateSchema
from models import UserModel
from utils.cloudinary_upload import upload_image_to_cloudinary
from flask_jwt_extended import jwt_required, get_jwt_identity


blp = Blueprint("users", __name__, description="Operations on users")

@blp.route("/user")
class User(MethodView):
    @jwt_required()
    @blp.response(200, UserSchema)
    def get(self):
        user_id = get_jwt_identity()
        user = UserModel.query.get_or_404(user_id)
        return user

    @jwt_required()
    def delete(self):
        user_id = get_jwt_identity()
        user = UserModel.query.get_or_404(user_id)

        db.session.delete(user)
        db.session.commit()

        return {"message": "User deleted."}, 200

    # Upload/update profile picture
    @jwt_required()
    def patch(self):
        user_id = get_jwt_identity()
        user = UserModel.query.get_or_404(user_id)

        if 'profile_picture' not in request.files:
            return {"message": "No image file provided."}, 400

        image_file = request.files['profile_picture']

        try:
            image_url = upload_image_to_cloudinary(image_file, user_id, subfolder="profile", is_unique=False)
            user.profile_picture = image_url
            db.session.commit()
            return {"message": "Profile picture updated.", "image_url": image_url}, 200
        except Exception as e:
            return {"message": str(e)}, 500

    # update user details..
    @jwt_required()
    @blp.arguments(UserUpdateSchema)
    @blp.response(200, UserSchema)
    def put(self, user_data):
        user_id = get_jwt_identity()
        user = UserModel.query.get(user_id)

        if user:
            if "name" in user_data:
                user.name = user_data["name"]
            if "password" in user_data:
                user.password = user_data["password"]
        else:
            user = UserModel(id=user_id, **user_data)

        db.session.add(user)
        db.session.commit()

        return user


