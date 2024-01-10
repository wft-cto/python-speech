from marshmallow import fields, Schema
from werkzeug.datastructures import FileStorage
from speech_tagging.models.audio import AudioModel
from speech_tagging.ma import ma

class FileStorageField(fields.Field):
    default_error_messages = {
        "invalid": "Not a valid audio."
    }

    def _deserialize(self, value, attr, data,**kwargs) -> FileStorage:
        if value is None:
            return None

        if not isinstance(value, FileStorage):
            self.fail("invalid")

        return value


class AudioSchema(Schema):
    audio = FileStorageField(required=True)


class AudioModelSchema(ma.ModelSchema):
    class Meta:
        model = AudioModel
        include_fk = True
        dump_only = ("id")

