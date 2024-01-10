from speech_tagging.ma import ma
from speech_tagging.models.language_model import LanguageModelModel
from speech_tagging.models.organization import OrganizationModel
from speech_tagging.models.corpus import CorpusModel
from marshmallow import fields, Schema
from werkzeug.datastructures import FileStorage


class FileStorageField(fields.Field):
    default_error_messages = {
        "invalid": "Not a valid text."
    }

    def _deserialize(self, value, attr, data) -> FileStorage:
        if value is None:
            return None

        if not isinstance(value, FileStorage):
            self.fail("invalid")

        return value


class TextFileSchema(Schema):
    text_file = FileStorageField(required=True)


class CorpusSchema(ma.ModelSchema):
    class Meta:
        model = CorpusModel
        include_fk = True
        dump_only = ("id",)
