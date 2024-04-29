from speech_tagging.ma import ma
from speech_tagging.models.meeting import MeetingModel
from speech_tagging.models.audio import AudioModel
from speech_tagging.models.organization import OrganizationModel


class MeetingSchema(ma.ModelSchema):
    class Meta:
        model = MeetingModel
        include_fk = True
        dump_only = ("id",)
