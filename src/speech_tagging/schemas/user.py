from src.speech_tagging.ma import ma
from src.speech_tagging.models.user_registration import User


class UserSchema(ma.ModelSchema):
    class Meta:
        model = User
        include_fk = True
        dump_only = ("id",)
        load_only = ("password",)
