from src.speech_tagging.db import db
from src.speech_tagging.models.attendee import AttendeeModel

class EmbeddingModel(db.Model):
    __tablename__ = "embeddings"

    id = db.Column(db.Integer, primary_key=True)
    attendee_id = db.Column(db.Integer, db.ForeignKey('attendees.id'), nullable=False)
    attendees = db.relationship('AttendeeModel',lazy=True)
    filename = db.Column(db.String(200), unique=True, nullable=False)

    def __init__(self,attendee_id, filename):
        self.attendee_id = attendee_id
        self.filename = filename

    @classmethod
    def find_all(cls):
        return cls.query.all()

    @classmethod
    def find_by_filename(cls,filename):
        return cls.query.filter_by(filename=filename).first()

    @classmethod
    def find_by_attendee_id(cls,attendee_id):
        return cls.query.filter_by(attendee_id=attendee_id).all()

    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()
