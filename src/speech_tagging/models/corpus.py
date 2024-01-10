from speech_tagging.db import db
from speech_tagging.models.organization import OrganizationModel
from typing import List


class CorpusModel(db.Model):
    __tablename__ = "corpus_model"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    corpus_name = db.Column(db.String(500), nullable=False)
    corpus_path = db.Column(db.String(2000), nullable=True)

    organization = db.relationship('OrganizationModel', lazy=True)


    @classmethod
    def find_all(cls) -> List["CorpusModel"]:
        return cls.query.all()

    @classmethod
    def find_by_corpus_name(cls, corpus_name):
        return cls.query.filter_by(corpus_name=corpus_name).first()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()

    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()