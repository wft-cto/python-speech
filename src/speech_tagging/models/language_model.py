from speech_tagging.db import db
from typing import List
from sqlalchemy.schema import UniqueConstraint

class LanguageModelModel(db.Model):
    __tablename__ = "language_model"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    model_name = db.Column(db.String(500), nullable=False)
    model_description = db.Column(db.String(2000), nullable=True)
    customization_id = db.Column(db.String(500), unique=True, nullable=True)

    organization = db.relationship('OrganizationModel', lazy=True)

    __table_args__ = (
        UniqueConstraint("organization_id", "model_name"),
    )

    @classmethod
    def find_all(cls) -> List["LanguageModelModel"]:
        return cls.query.all()

    @classmethod
    def find_by_model_name(cls, model_name):
        return cls.query.filter_by(model_name=model_name).first()

    @classmethod
    def find_all_language_model_of_an_organization(cls, organization_id):
        return cls.query.filter_by(organization_id=organization_id).all()


    @classmethod
    def find_by_organization_id_and_model_name(cls,org_id, model_name):
        return cls.query.filter_by(organization_id=org_id).filter_by(model_name=model_name).first()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()
