from src.speech_tagging.ma import ma
from src.speech_tagging.models.meeting import MeetingModel
from src.speech_tagging.models.audio import AudioModel
from src.speech_tagging.models.organization import OrganizationModel


class MeetingSchema(ma.ModelSchema):
    class Meta:
        model = MeetingModel
        include_fk = True
        dump_only = ("id",)
