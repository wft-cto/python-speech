import json
from os.path import join, dirname

from flask_restful import Resource
from flask import request
from flask_uploads import UploadNotAllowed

from speech_tagging.schemas.language_model import LanguageSchema
from speech_tagging.schemas.corpus import CorpusSchema, TextFileSchema
from speech_tagging.watson_speech.custom_language_model import CustomLanguageModel
from speech_tagging.models.organization import OrganizationModel
from speech_tagging.commons.messages import *
from sqlalchemy.exc import IntegrityError
from speech_tagging.models.language_model import LanguageModelModel
from speech_tagging.models.corpus import CorpusModel

from speech_tagging.definitions import CORPUS_FOLDER
from speech_tagging.commons import audio_helper
from speech_tagging.commons import text_helper
from speech_tagging.definitions import *
import os



from speech_tagging.commons.utils import get_all_textfile_from_folder

lm_schema = LanguageSchema()
language_schemas = LanguageSchema(many=True)

corpus_schema = CorpusSchema()
corpus_schemas = CorpusSchema(many=True)

text_file_schema = TextFileSchema()

watson_language_model = CustomLanguageModel()



class LanguageModel(Resource):
    @classmethod
    def post(cls):
        """

        :param audio_link:
        :return:
        """
        language_model_json = request.get_json()
        language_model = lm_schema.load(language_model_json)

        organization_id = language_model_json['organization_id']
        if not OrganizationModel.find_by_id(organization_id):
            return {
                "data":{},
                "success":False,
                "message":ORGANIZATION_DOES_NOT_EXIST.format(organization_id)
            },400

        model_name = language_model_json.get("model_name")

        if LanguageModelModel.find_by_organization_id_and_model_name(organization_id,model_name) is not None:
            return {
                       "data": {},
                       "success": False,
                       "message": MODEL_NAME_ALREADY_EXISTS.format(model_name)
                   }, 400

        model_description = language_model_json.get("model_description")

        customization_id = watson_language_model.create_language_model(model_name,model_description)

        language_model_json.update({"customization_id":customization_id})
        language_model = lm_schema.load(language_model_json)

        try:
            language_model.save_to_db()
            return {"data":
                        {
                        "language_model":lm_schema.dump(language_model)
                        },
                "message":"Created",
                "success":True
                }, 201
        except IntegrityError :
            return {
                       "data":{},
                        "success":False,
                        "message":MODEL_NAME_ALREADY_EXISTS.format(model_name)
                    }, 400

class DeleteLanguageModel(Resource):
    @classmethod
    def delete(cls, organization_id, model_name):
        if OrganizationModel.find_by_id(organization_id) is None:
            return {
                       "data": {},
                       "success": False,
                       "message": ORGANIZATION_DOES_NOT_EXIST.format(organization_id)
                   }, 400
        model = LanguageModelModel.find_by_organization_id_and_model_name(organization_id, model_name)
        if model is None:
            return {
                       "data": {},
                       "success": False,
                       "message": MODEL_NAME_DOES_NOT_EXIST.format(model_name)
                   }, 400

        success = watson_language_model.delete_language_model(model.customization_id)

        if success:
            model.delete_from_db()
            return {"data":
                {
                },
                       "message": "Language model {} deleted".format(model.model_name),
                       "success": success
                   }, 200
        else:
            return {"data":
                {
                },
                       "message": "Failed to delete Language model {} ".format(model.model_name),
                       "success": success
                   }, 400


class LanguageModelList(Resource):
    @classmethod
    def get(cls,organization_id):
        if OrganizationModel.find_by_id(organization_id) is None:
            return {
                       "data": {},
                       "success": False,
                       "message": ORGANIZATION_DOES_NOT_EXIST.format(organization_id)
                   }, 400

        models = LanguageModelModel.find_all_language_model_of_an_organization(organization_id)
        models = [{"id":model.id, "model_name":model.model_name, "model_description":model.model_description} for model in models]
        return {"data":
            {
                "models": models
            },
                   "message": "All models",
                   "success": True
               }, 201

class AvailableLanguageModelList(Resource):
    @classmethod
    def get(cls,organization_id):
        if OrganizationModel.find_by_id(organization_id) is None:
            return {
                       "data": {},
                       "success": False,
                       "message": ORGANIZATION_DOES_NOT_EXIST.format(organization_id)
                   }, 400

        all_models = watson_language_model.list_language_models()
        all_models_for_organization = LanguageModelModel.find_all_language_model_of_an_organization(organization_id)
        all_models_name_for_organization = [model.model_name for model in all_models_for_organization]

        available_models = [{"name":model["name"]} for model in all_models['customizations']
                            if model["status"] == "available" and model["name"] in all_models_name_for_organization]

        return {"data":
            {
                "models": available_models
            },
                   "message": "available models",
                   "success": True
               }, 201


class LanguageModelDetail(Resource):
    @classmethod
    def get(cls, organization_id,model_name):
        if OrganizationModel.find_by_id(organization_id) is None:
            return {
                       "data": {},
                       "success": False,
                       "message": ORGANIZATION_DOES_NOT_EXIST.format(organization_id)
                   }, 400
        model = LanguageModelModel.find_by_organization_id_and_model_name(organization_id, model_name)
        if model is None:
            return {
                       "data": {},
                       "success": False,
                       "message": MODEL_NAME_DOES_NOT_EXIST.format(model_name)
                   }, 400

        lm_details = watson_language_model.get_language_model(model.customization_id)
        lm_corpus = watson_language_model.list_text_corpora(model.customization_id)

        lm_details.update(lm_corpus)
        return {"data":
            {
                "details": lm_details
            },
                   "message": "Details of {}".format(model.model_name),
                   "success": True
               }, 200


class TrainLanguageModel(Resource):
    @classmethod
    def post(cls,organization_id, model_name):

        if OrganizationModel.find_by_id(organization_id) is None:
            return {
                       "data": {},
                       "success": False,
                       "message": ORGANIZATION_DOES_NOT_EXIST.format(organization_id)
                   }, 400
        model = LanguageModelModel.find_by_organization_id_and_model_name(organization_id, model_name)
        if model is None:
            return {
                       "data": {},
                       "success": False,
                       "message": MODEL_NAME_DOES_NOT_EXIST.format(model_name)
                   }, 400

        success = watson_language_model.train_language_model(model.customization_id)
        if success:
            return {"data":
                {
                    "models": lm_schema.dump(model)
                },
                       "message": "Training of {} is successful".format(model.model_name),
                       "success": success
                   }, 201
        else:
            return {"data":
                {
                },
                       "message": "Training of {} failed. Please check if there is text corpus available for the model".format(model.model_name),
                       "success": success
                   }, 500

class ListCorpus(Resource):
    @classmethod
    def get(cls, organization_id,model_name):
        if OrganizationModel.find_by_id(organization_id) is None:
            return {
                       "data": {},
                       "success": False,
                       "message": ORGANIZATION_DOES_NOT_EXIST.format(organization_id)
                   }, 400
        model = LanguageModelModel.find_by_organization_id_and_model_name(organization_id, model_name)
        if model is None:
            return {
                       "data": {},
                       "success": False,
                       "message": MODEL_NAME_DOES_NOT_EXIST.format(model_name)
                   }, 400

        corpus_details = watson_language_model.list_text_corpora(model.customization_id)

        return {"data":
            {
                "models": corpus_details
            },
                   "message": "Detail list of text corpus for language model {}".format(model.model_name),
                   "success": True
               }, 201

class Corpus(Resource):
    @classmethod
    def post(cls):
        corpus_data_json = request.form.to_dict()

        try:
            model_name = corpus_data_json.pop("model_name")
        except:
            raise
            return {"data":
                        {},
                    "message": "Model name missing ",
                    # "message": str(e),
                    "success": False
                    }, 400


        corpus_file = text_file_schema.load(request.files)
        corpus_data = corpus_schema.load(corpus_data_json)

        try:
            # Check if file with same name exist or not
            filename = corpus_file["text_file"].filename
            corpus_name = corpus_data_json["corpus_name"]

            if filename.split(".")[1] != "txt":
                return {"data":
                                    {},
                            "message": "Invalid file extension. Use .txt file",
                            # "message": str(e),
                            "success":False
                            }, 400

            organization_id = corpus_data_json["organization_id"]
            if OrganizationModel.find_by_id(organization_id) is None:
                return {"data":
                            {},
                        "message": "Organization not found",
                        # "message": str(e),
                        "success": False
                        }, 400

            model = LanguageModelModel.find_by_organization_id_and_model_name(organization_id, model_name)

            if model is None:
                return {"data":
                            {},
                        "message": "Invalid organization or model name",
                        # "message": str(e),
                        "success": False
                        }, 400

            filepath = os.path.join(PATH_FILES_CORPUS,filename)
            corpus_file['text_file'].save(filepath)

            corpus_data_json.update({"corpus_path":filepath})
            corpus_data = corpus_schema.load(corpus_data_json)

            corpus_data.save_to_db()


            customization_id = model.customization_id

            success = watson_language_model.add_text_corpus(customization_id=customization_id, corpus_name=corpus_name,
                                                            text_path=filepath)

            if success:
                return {"data":
                            {},
                        "message": "Corpus added successfully",
                        # "message": str(e),
                        "success": success
                        }, 200
            else:
                return {"data":
                            {},
                        "message": "Adding corpus unsuccessful",
                        # "message": str(e),
                        "success": False
                        }, 400

            # return {"data":
            #             {"file":corpus_schema.dump(corpus_data)},
            #         "message": "File Uploaded Successfully",
            #         # "message": str(e),
            #         "success": True
            #         }, 200

            # save(self, storage, folder=None, name=None)
            # text_file_path = text_helper.save_text_file(corpus_file["text_file"], folder=CORPUS_FOLDER)
            # here we only return the basename of the audio and hide the internal folder structure from our user
        except Exception as error:
            return {"data":
                        {},
                    "message": "Upload Error",
                    # "message": str(e),
                    "success": False
                    }, 500


class AddCorpus(Resource):
    @classmethod
    def post(cls,organization_id,model_name, corpus_id):
        corpus = CorpusModel.find_by_id(corpus_id)

        if corpus is None:
            return {"data":
                        {},
                    "message": "Corpus not found",
                    # "message": str(e),
                    "success": False
                    }, 400

        file_path = corpus.corpus_path
        corpus_name = corpus.corpus_name

        model = LanguageModelModel.find_by_organization_id_and_model_name(organization_id,model_name)

        if model is None:
            return {"data":
                        {},
                    "message": "Invalid organization or model name",
                    # "message": str(e),
                    "success": False
                    }, 400

        customization_id = model.customization_id

        success = watson_language_model.add_text_corpus(customization_id=customization_id,corpus_name=corpus_name,text_path=file_path)

        if success:
            return {"data":
                        {},
                    "message": "Corpus added successfully",
                    # "message": str(e),
                    "success": success
                    }, 200
        else:
            return {"data":
                        {},
                    "message": "Adding corpus unsuccessful",
                    # "message": str(e),
                    "success": False
                    }, 400


