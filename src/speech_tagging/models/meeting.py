from src.speech_tagging.db import db
from src.speech_tagging.models.organization import OrganizationModel
from typing import List

from src.speech_tagging.models.audio import AudioModel
from src.speech_tagging.commons import audio_helper



class MeetingModel(db.Model):
    __tablename__ = "meetings"

    id = db.Column(db.Integer, primary_key=True)
    total_attendee = db.Column(db.Integer, nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    organization = db.relationship('OrganizationModel', lazy=True)

    meeting_location = db.Column(db.String(200), unique=False, nullable=True)
    # audio_filename = db.Column(db.String(200), unique=True, nullable=False)
    
    audio_id = db.Column(db.Integer, db.ForeignKey('audio.id'), nullable=False)
    audio = db.relationship('AudioModel',lazy=True)
    transcription_filename = db.Column(db.String(500), unique=True, nullable=True)

    @classmethod
    def find_all(cls) -> List["MeetingModel"]:
        return cls.query.all()

    # @classmethod
    # def find_by_audio_filename(cls, audio_filename):
    #     return cls.query.filter_by(audio_filename=audio_filename).first()

    @classmethod
    def find_by_audio_filename(cls, audio_id):
        return cls.query.filter_by(audio_id=audio_id).first()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()