from src.speech_tagging.ma import ma
from src.speech_tagging.models.language_model import LanguageModelModel
from src.speech_tagging.models.organization import OrganizationModel


class LanguageSchema(ma.ModelSchema):
    class Meta:
        model = LanguageModelModel
        include_fk = True
        dump_only = ("id","organization",)
