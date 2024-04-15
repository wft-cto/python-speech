import enum
from flask_login import UserMixin

from src.speech_tagging.db import db
from typing import List
from src.speech_tagging.models.organization import OrganizationModel
# class GenderEnum(enum.Enum):
#     male = "M"
#     female = "F"
#     other = "O"

class User(UserMixin,db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    first_name = db.Column(db.String(200),nullable=False)
    last_name = db.Column(db.String(200),nullable=False)
    # gender = db.Column(db.Enum(GenderEnum),nullable=False)
    gender = db.Column(db.String(50),nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200),nullable=False)
    authenticated = db.Column(db.Boolean, default=False)
    is_email_confirmed = db.Column(db.Boolean, nullable=True)
    # token = db.Column(db.String(50),nullable=True)

    #Changes for apple login
    user_type = db.Column(db.String(50),nullable=True)
    userIdentifier = db.Column(db.String(120), nullable=True)

    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    organization = db.relationship('OrganizationModel',lazy=True)    
    # organization = db.relationship('OrganizationModel', backref=db.backref('children'))    
    
    def __repr__(self):
        return '<User %r>' % self.username
    
    def is_active(self):
        """True, as all users are active."""
        return True

    def get_id(self):
        """Return the usernameto satisfy Flask-Login's requirements."""
        return self.id

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()
    
    @classmethod
    def find_all(cls) -> List["User"]:
        return cls.query.all()
    
    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()