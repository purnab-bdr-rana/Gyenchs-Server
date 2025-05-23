from marshmallow import Schema, fields

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    email = fields.Str(required=True)
    role = fields.Str(dump_only=True)
    profile_picture = fields.Str(dump_only=True)
    verification_code = fields.Int(dump_only=True, load_only=True)
    password = fields.Str(required=True, load_only=True)

class UserUpdateSchema(Schema):
    name = fields.Str()
    # email is excluded or made optional
    password = fields.Str(load_only=True)

class PlainWardrobeItemsSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)

class WardrobeItemsSchema(PlainWardrobeItemsSchema):
    type = fields.Str(dump_only=True)
    image_url = fields.Str(dump_only=True)
    color = fields.Str(dump_only=True)
    user_id = fields.Int(dump_only=True, load_only=True)
    user = fields.Nested(UserSchema(), dump_only=True, load_only=True)


class PlainOutfitSchema(Schema):
    id = fields.Int(dump_only=True)
    favorite = fields.Bool(required=True)

class OutfitSchema(PlainOutfitSchema):
    user_id = fields.Int(required=True, load_only=True)
    kira_id = fields.Int(required=True, load_only=True)
    tego_id = fields.Int(required=True, load_only=True)
    wonju_id = fields.Int(required=True, load_only=True)

    user = fields.Nested(UserSchema, dump_only=True, load_only=True)
    kira = fields.Nested(WardrobeItemsSchema, dump_only=True)
    tego = fields.Nested(WardrobeItemsSchema, dump_only=True)
    wonju = fields.Nested(WardrobeItemsSchema, dump_only=True)
