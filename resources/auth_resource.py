from flask import url_for, request, current_app, redirect, jsonify
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt
from urllib.parse import quote
import json
from flask_cors import cross_origin

from blocklist import BLOCKLIST
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone

from db import db
from schemas import UserSchema
from models import UserModel
from utils.code_verification_utils import is_code_valid, generate_verification_code, is_email_code_valid
from utils.email_utils import send_verification_email, send_login_alert_email_async
from utils.get_user_location import get_location_from_ip

blp = Blueprint("Auth", "auth", description="Authentication routes")

# email subjects
email_subject = "🔐 Your Email Verification Code"
password_subject = "🔐 Your Password Verification Code"

pending_users = {}

# sign up users
@blp.route("/auth/signup")
class UserSignUp(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        if UserModel.query.filter_by(email=user_data['email']).first():
            abort(409, message="A user with that email already exists.")

        code = generate_verification_code()
        email = user_data['email']

        pending_users[email] = {
            "data": user_data,
            "code": code,
            "expires_at": datetime.utcnow().timestamp() + 600  # 10 min expiry
        }

        send_verification_email(email, "Signup Verification", code)

        return {"message": "Verification code sent to your email. Please confirm to complete signup.", "status": 200}, 200


# verify sign up
@blp.route("/auth/verify-signup")
class VerifySignUp(MethodView):
    def post(self):
        data = request.get_json()
        email = data.get("email")
        code = data.get("verification_code")

        pending = pending_users.get(email)

        if not pending or str(pending["code"]) != str(code):
            abort(400, message="Invalid or expired verification code.")

        if datetime.utcnow().timestamp() > pending["expires_at"]:
            del pending_users[email]
            abort(400, message="Verification code expired.")

        user_data = pending["data"]
        user = UserModel(
            name=user_data["name"],
            email=user_data["email"],
            role="user",
            password=pbkdf2_sha256.hash(user_data['password'])
        )

        db.session.add(user)
        db.session.commit()
        del pending_users[email]

        return {"message": "User signed up successfully."}, 201

# login users
@blp.route("/auth/login")
class UserLogin(MethodView):
    decorators = [cross_origin(origin='*')]
    @blp.arguments(UserSchema)
    def post(self, user_data):
        user = UserModel.query.filter_by(email=user_data["email"]).first()

        if user and user.password and pbkdf2_sha256.verify(user_data["password"], user.password):
            access_token = create_access_token(identity=str(user.id), fresh=True)
            refresh_token = create_refresh_token(user.id)
            user_schema = UserSchema()
            user_data_serialized = user_schema.dump(user)

            # Gather details fast (no blocking)
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            location = get_location_from_ip(ip)
            device = request.headers.get("User-Agent", "Unknown device")

            # Launch background email sending (non-blocking)
            send_login_alert_email_async(user.email, now, device, location)

            # Return immediately
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": user_data_serialized
            }

        abort(401, message="Invalid credentials.")



# login with google
@blp.route("/google")
class GoogleLogin(MethodView):
    def get(self):
        redirect_uri = url_for("Auth.GoogleAuthorize", _external=True)
        return current_app.oauth.google.authorize_redirect(redirect_uri)

@blp.route("/google/authorize")
class GoogleAuthorize(MethodView):
    def get(self):
        # Get token and user info from Google OAuth
        token = current_app.oauth.google.authorize_access_token()
        user_info = current_app.oauth.google.userinfo()

        if not user_info:
            return jsonify({"msg": "Failed to fetch user info"}), 400

        # Try to find the user by email
        user = UserModel.query.filter_by(email=user_info["email"]).first()

        # If user does not exist, create a new one
        if not user:
            user = UserModel(
                email=user_info["email"],
                name=user_info.get("name", ""),
                role="user",
                password=None,
            )
            db.session.add(user)
            db.session.commit()

        access_token = create_access_token(identity=str(user.id), fresh=True)
        refresh_token = create_refresh_token(user.id)

        current_user = {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "profile_picture": user.profile_picture,
        }
        # Redirect the user back to the frontend with the JWT token
        user_json = quote(json.dumps(current_user))

        return redirect(
            f"https://gyencha.purnabdrrana.com/callback?access-token={access_token}&refresh-token={refresh_token}&user={user_json}"
        )


# logout users
@blp.route("/auth/logout")
class UserLogout(MethodView):
    @jwt_required()
    def post(self):
        jti = get_jwt()['jti']
        BLOCKLIST.add(jti)
        return {"message": "Successfully logged out."}


# refresh access token
@blp.route("/auth/refresh")
class TokenRefresh(MethodView):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        # Make it clear that when to add the refresh token to the blocklist will depend on the app design
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"access_token": new_token}, 200



# password change for logged-in users
@blp.route("/auth/request-password-change")
class RequestPasswordChange(MethodView):
    @jwt_required()
    def post(self):
        data = request.get_json()
        user_id = get_jwt_identity()
        user = UserModel.query.get(user_id)

        if not user:
            abort(404, message="User not found.")

        if not pbkdf2_sha256.verify(data["current_password"], user.password):
            abort(401, message="Current password is incorrect.")

        code = generate_verification_code()
        user.verification_code = code
        user.code_sent_at = datetime.now(timezone.utc)
        user.temp_new_password = pbkdf2_sha256.hash(data["new_password"])

        email_sent = send_verification_email(user.email, password_subject, code)
        if not email_sent:
            abort(500, message="Failed to send verification email.")

        db.session.commit()

        return {"message": "Verification code sent to your email."}, 200


@blp.route("/auth/verify-password-change")
class VerifyPasswordChange(MethodView):
    @jwt_required()
    def post(self):
        data = request.get_json()
        user_id = get_jwt_identity()
        user = UserModel.query.get(user_id)

        if not is_code_valid(user, data["verification_code"]):
            abort(400, message="Invalid or expired code.")

        user.password = user.temp_new_password
        user.verification_code = None
        user.temp_new_password = None
        user.code_sent_at = None
        db.session.commit()

        return {"message": "Password changed successfully."}, 200


# for unauthorized users (not logged in)
@blp.route("/auth/request-reset-password")
class RequestResetPassword(MethodView):
    def post(self):
        data = request.get_json()

        if not data or "email" not in data:
            abort(400, message="Email is required.")

        user = UserModel.query.filter_by(email=data["email"]).first()
        if not user:
            abort(404, message="User not found.")

        code = generate_verification_code()
        user.verification_code = code
        user.code_sent_at = datetime.now(timezone.utc)

        if not send_verification_email(user.email, password_subject, code):
            abort(500, message="Failed to send verification email.")

        db.session.commit()

        return {"message": "Verification code sent."}, 200


# verify
@blp.route("/auth/verify-reset-code")
class VerifyResetCode(MethodView):
    def post(self):
        data = request.get_json()
        user = UserModel.query.filter_by(email=data["email"]).first()
        if not user or not is_code_valid(user, data["verification_code"]):
            abort(400, message="Invalid or expired code.")

        user.code_verified = True
        db.session.commit()

        return {"message": "Code verified. You may now reset your password."}, 200


# reset password for unauthorised users
@blp.route("/auth/reset-password")
class ResetPassword(MethodView):
    def post(self):
        data = request.get_json()
        user = UserModel.query.filter_by(email=data["email"]).first()
        if not user or not user.code_verified:
            abort(400, message="Verification required before password reset.")

        user.password = pbkdf2_sha256.hash(data["new_password"])
        user.verification_code = None
        user.code_sent_at = None
        user.code_verified = False
        db.session.commit()

        return {"message": "Password has been reset successfully."}, 200


# change email
@blp.route("/auth/request-email-change")
class RequestEmailChange(MethodView):
    @jwt_required()
    def post(self):
        data = request.get_json()
        new_email = data.get("new_email")
        user_id = get_jwt_identity()
        user = UserModel.query.get(user_id)

        if not new_email:
            abort(400, message="New email is required.")

        if UserModel.query.filter_by(email=new_email).first():
            abort(400, message="Email already in use.")

        code = generate_verification_code()
        user.temp_new_email = new_email
        user.email_verification_code = code
        user.email_code_sent_at = datetime.now(timezone.utc)

        if not send_verification_email(new_email, email_subject, code):
            abort(500, message="Failed to send verification email.")

        db.session.commit()
        return {"message": "Verification code sent to new email."}, 200


# verify email change
@blp.route("/auth/confirm-email-change")
class ConfirmEmailChange(MethodView):
    @jwt_required()
    def post(self):
        data = request.get_json()
        code = data.get("verification_code")
        user_id = get_jwt_identity()
        user = UserModel.query.get(user_id)

        if not code:
            abort(400, message="Verification code is required.")

        if not is_email_code_valid(user, code):
            abort(400, message="Invalid or expired code.")

        user.email = user.temp_new_email
        user.temp_new_email = None
        user.email_verification_code = None
        user.email_code_sent_at = None

        db.session.commit()
        return {"message": "Email updated successfully."}, 200
