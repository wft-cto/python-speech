from marshmallow import fields, Schema
from speech_tagging.models.attendee import attendee_audio
from speech_tagging.ma import ma

class AttendeeAudioModelSchema(ma.ModelSchema):
    class Meta:
        model = attendee_audio
        include_fk = True
        dump_only = ("id")
