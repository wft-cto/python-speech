from src.speech_tagging.db import db
from datetime import datetime
from src.speech_tagging.models.organization import OrganizationModel
from src.speech_tagging.models.user_registration import User
from typing import List

class AudioModel(db.Model):
    __tablename__ = "audio"
    id = db.Column(db.Integer, primary_key=True)
    # filename = db.Column(db.String(200), unique=True, nullable=False)
    filename = db.Column(db.String(200),unique=True,nullable=False)
    path = db.Column(db.String(300))
    organization_id = db.Column(db.Integer,db.ForeignKey('organization.id'),nullable=False)
    organization = db.relationship('OrganizationModel',lazy=True)

    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    user = db.relationship('User',lazy=True)

    attendees = db.Column(db.String, nullable=False)

    created_date = db.Column(db.DateTime,default=datetime.utcnow)
    date = db.Column(db.DateTime)


    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()
    
    @classmethod
    def find_all(cls) -> List["AudioModel"]:
        return cls.query.all()
    
    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()