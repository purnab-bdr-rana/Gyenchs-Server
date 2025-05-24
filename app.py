import os
from datetime import timedelta

from flask_compress import Compress
from flask_cors import CORS
from flask import Flask, jsonify
from flask_smorest import Api
from db import db

from flask_jwt_extended import JWTManager
from blocklist import BLOCKLIST
from flask_migrate import Migrate

from resources.auth_resource import blp as AuthBlueprint
from resources.user_resource import blp as UserBlueprint
from resources.wardrobe_items_resource import blp as WardrobeItemsBlueprint
from resources.outfits_resource import blp as OutfitsBlueprint

from authlib.integrations.flask_client import OAuth

def create_app(db_url=None):
    app = Flask(__name__)
    app.secret_key = os.getenv("APP_SECRET_KEY")

    Compress(app)

    CORS(app, resources={r"/*": {"origins": [
        "http://localhost:5173",
        "https://gyencha.purnabdrrana.com"
    ]}})
    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["API_TITLE"] = "Gyencha Backend REST API docs"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/api-docs"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or os.getenv("DATABASE_URL", "sqlite:///data.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    oauth = OAuth(app)
    app.oauth = oauth

    google = oauth.register(
        name='google',
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

    migrate = Migrate(app, db)

    api = Api(app)

    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=2)

    jwt = JWTManager(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        return jwt_payload['jti'] in BLOCKLIST

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {"description": "The token has been revoked.", "error": "token_revoked"}
            ),
            401,
        )

    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {
                    "description": "The token is not fresh.",
                    "error": "fresh_token_required",
                }
            ),
            401,
        )

    @jwt.additional_claims_loader
    def add_claims_to_jwt(identity):
        if identity == 1:
            return {"is_admin": True}
        return {"is_admin": False}

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return (
            jsonify({"message": "The token has expired.", "error": "token_expired"}),
            401,
        )

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return (
            jsonify(
                {"message": "Signature verification failed.", "error": "invalid_token"}
            ),
            401,
        )

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return (
            jsonify(
                {
                    "description": "Request does not contain an access token.",
                    "error": "authorization_required",
                }
            ),
            401,
        )

    with app.app_context():
        from models.user_model import UserModel
        from models.wardrobe_items_model import WardrobeItemsModel
        from models.outfits import OutfitsModel

        db.create_all()

    api.register_blueprint(AuthBlueprint)
    api.register_blueprint(UserBlueprint)
    api.register_blueprint(WardrobeItemsBlueprint)
    api.register_blueprint( OutfitsBlueprint)

    return app



