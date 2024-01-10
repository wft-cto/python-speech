from speech_tagging.ma import ma
from speech_tagging.models.attendee import AttendeeModel
from marshmallow import Schema, fields


class TimeSchema(Schema):
    start = fields.Float(required=True)
    end = fields.Float(required=True)


class AttendeeSchema(ma.ModelSchema):
    class Meta:
        model = AttendeeModel
        include_fk = True
        dump_only = ("id",)


class AttendeeVoiceSchema(Schema):
    attendee_id = fields.Int(required=True)
    # audio_name = fields.Str(required=True)
    audio_id = fields.Int(required=True)
    voice_list = fields.List(fields.Nested(TimeSchema),required=True)


