from speech_tagging.db import db
from flask_login import UserMixin
from typing import List


class OrganizationModel(UserMixin,db.Model):
    __tablename__ = "organization"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300), nullable=True)
    location = db.Column(db.String(120), nullable=True)
    contact_no = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(300), nullable=False, unique=True)
    password = db.Column(db.String(300), nullable=True)
    authenticated = db.Column(db.Boolean, default=False)
    organization_id = db.Column(db.String(300), nullable=True, unique=True)
    # token = db.Column(db.String(50),nullable=True)


    is_email_confirmed = db.Column(db.Boolean, default=False)

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    @classmethod
    def find_by_organization_id(cls, organization_id):
        return cls.query.filter_by(organization_id=organization_id).first()

    @classmethod
    def find_all(cls) -> List["OrganizationModel"]:
        return cls.query.order_by(cls.name).all()

    def organization_json(self):
        return {
            "name": self.name,
            "location":self.location,
            "contact_number":self.contact_no,
            "email":self.email,
            "organization_id":self.organization_id
        }
    
    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()