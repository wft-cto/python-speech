from speech_tagging.db import db
from typing import List
from sqlalchemy.schema import UniqueConstraint
from speech_tagging.models.organization import OrganizationModel
from speech_tagging.models.audio import AudioModel

attendee_audio = db.Table('attendee_audio',
    db.Column('audio_id', db.Integer, db.ForeignKey('audio.id'), primary_key=True),
    db.Column('attendee_id', db.Integer, db.ForeignKey('attendees.id'), primary_key=True)
)


class AttendeeModel(db.Model):
    __tablename__ = "attendees"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    first_name = db.Column(db.String(200), nullable=False)
    last_name = db.Column(db.String(200), unique=False, nullable=False)
    gender = db.Column(db.String(200), unique=False, nullable=True)
    email = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(50), nullable=False)

    organization = db.relationship('OrganizationModel', lazy=True)
    
    # attendee_audio = db.relationship("AudioModel",secondary=attendee_audio, lazy='subquery')
    audios = db.relationship("AudioModel",secondary=attendee_audio,backref=db.backref('attendee'))

    __table_args__ = (
        UniqueConstraint("organization_id", "email","phone"),
    )

    def json(self):
        json = {
            "id":self.id,
            "first_name":self.first_name,
            "last_name":self.last_name,
            "gender":self.gender,
            "email":self.email,
            "phone":self.phone,
            "audios":self.audios
        }

        return json

    @classmethod
    def find_all(cls) -> List["AttendeeModel"]:
        return cls.query.order_by(cls.first_name).order_by(cls.last_name).all()

    @classmethod
    def find_by_email(cls,email):
        return cls.query.filter_by(email=email).first()

    @classmethod
    def find_by_organization_id_and_email(cls, org_id, email):
        return cls.query.filter_by(organization_id=org_id).filter_by(email=email).first()

    @classmethod
    def find_by_organization_id_and_phone(cls, org_id, phone):
        return cls.query.filter_by(organization_id=org_id).filter_by(phone=phone).first()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    def save_to_db(self) -> None:
        db.session.add(self)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            raise

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()