from marshmallow import Schema, fields


class RecognizeSpeakerSchema(Schema):
    meeting_id = fields.Int(required=True)
    attendees = fields.List(fields.Int(),required=False)