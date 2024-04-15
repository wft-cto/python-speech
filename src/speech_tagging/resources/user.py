from sqlalchemy import asc
from sqlalchemy.exc import IntegrityError

from flask_restful import Resource,reqparse
from flask import request

from src.speech_tagging.models.user_registration import User
from src.speech_tagging.models.organization import OrganizationModel
from src.speech_tagging.models.audio import AudioModel

from src.speech_tagging.schemas.user import UserSchema
from src.speech_tagging.schemas.organization import OrganizationSchema
from src.speech_tagging.schemas.audio import AudioModelSchema
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager,login_user
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,create_refresh_token)

import strgen
import random

import jwt

user_schema = UserSchema()
organization_schema = OrganizationSchema()
audios_model_schema = AudioModelSchema(many=True)



class UserDetail(Resource):
    @classmethod
    def get(cls,user_id):
        """

        :return:
        """
        user_obj = User.find_by_id(user_id)
        if user_obj is None:
            return {"data": 
                            {},
                    "message":"User not Found",
                    "success":"False"
                    }, 404            
        user_detail = user_schema.dump(user_obj)
        
        organization_obj = OrganizationModel.find_by_id(user_obj.organization_id)
        if organization_obj is None:
            return {"data": 
                            {},
                    "message":"Organization not Found",
                    "success":"False"
                    }, 404                   
        
        organization_detail = organization_schema.dump(organization_obj)
        
        audios = AudioModel.query.filter_by(user_id=user_id).order_by(asc(AudioModel.filename))
        # print(audios)
        audios = audios_model_schema.dump(audios)
        all_detail = {
            "user":user_detail,
            "organization":organization_detail,
            "audios":audios
        }
        

        return {
                "data": all_detail,
                "message":"",
                "success":True
            }, 200


    parser = reqparse.RequestParser()
    parser.add_argument('username',
                        type=str,
                        required=True,
                        help='Username cannot be blank!')
    parser.add_argument('first_name',
                        type=str,
                        required=True,
                        help='Firstname cannot be blank!')
    parser.add_argument('last_name',
                        type=str,
                        required=True,
                        help='Lastname cannot be blank!')                        
    parser.add_argument('gender',
                        type=str,
                        required=True,
                        help='Gender cannot be blank!')                    
    parser.add_argument('organization_id',
                        type=int,
                        required=True,
                        help='Organization id cannot be blank!')
                        
    @classmethod
    def put(cls,user_id):
        cls.data = cls.parser.parse_args()

        user_obj = User.find_by_id(user_id)
        if user_obj is None:
            return {"data": 
                            {},
                    "message":"User not Found",
                    "success":"False"
                    }, 404            

        try:
            user_obj.username = cls.data["username"]
            user_obj.first_name = cls.data["first_name"]
            user_obj.last_name = cls.data["last_name"]
            user_obj.gender = cls.data["gender"]
            user_obj.organization_id = cls.data["organization_id"]
            user_obj.save_to_db()

            return {"message": "User profile updated successfully",
                    "data":None,
                    "success": True}, 201
        except IntegrityError:
            return {"message": "Username already exists",
                    "data": None,
                    "success": False}, 500
        else:
            return {"message": "User profile could not be updated",
                    "data": None,
                    "success": False}, 500



    def delete(self,user_id):
        user = User.find_by_id(user_id)
        print("user", user)
        if not user :
            return {"data": {},
                    "message": "User with id doesn't exist",
                    "success": False
                    }, 400

        try:
            user.delete_from_db()

            return {"message": "User deleted successfully",
                    "data": None,
                    "success": True}, 201
        except Exception as e:
            return {"message": "User could not be deleted",
                    "error": e,
                    "data": None,
                    "success": False}, 500


class UserDetailFromEmail(Resource):
    @classmethod
    def get(cls, email):
        """

        :return:
        """
        user_obj = User.find_by_email(email)
        if user_obj is None:
            return {"data":
                        {},
                    "message": "User not Found",
                    "success": "False"
                    }, 404
        user_detail = user_schema.dump(user_obj)

        organization_obj = OrganizationModel.find_by_id(user_obj.organization_id)
        if organization_obj is None:
            return {"data":
                        {},
                    "message": "Organization not Found",
                    "success": "False"
                    }, 404

        organization_detail = organization_schema.dump(organization_obj)

        audios = AudioModel.query.filter_by(user_id=user_obj.id).order_by(asc(AudioModel.filename))
        # print(audios)
        audios = audios_model_schema.dump(audios)
        all_detail = {
            "user": user_detail,
            "organization": organization_detail,
            "audios": audios
        }

        return {
                   "data": all_detail,
                   "message": "",
                   "success": True
               }, 200


class UserAppleLogin(Resource):
    def post(cls):

        loginDetails = request.get_json()


        print(loginDetails)
        try: 
            userIdentified = loginDetails["userIdentifier"]

            data = jwt.decode(loginDetails["identityToken"], '', verify=False)

            print("Decoded data>>>>>>", data)

            print("userIdentified>>>>>>>>>>>", userIdentified)
            # app.logger.info("userIdentified>>>>>>>>>>>", userIdentified)

            if userIdentified:

                email = loginDetails["email"]

                if not email: 
                    email = data["email"]

                if email:

                    user = User.query.filter_by(email=email).first()

                    if not user:
                        user_id = random.randint(0, 500)
                        print(user_id)

                        password = strgen.StringGenerator("[\d\w]{15}").render()

                        first_name = loginDetails["first_name"]

                        last_name = loginDetails["last_name"]

                        if not last_name:
                            last_name = first_name

                        # if not first_name:
                        #     first_name = email[0:5]

                        # if not last_name:
                        #     last_name = email[0:5]

                        old_user = User.query.filter_by(id=user_id).first()

                        if not old_user:
                            user = User(email=email,id=user_id, username=email, password=password, first_name=first_name, last_name=last_name, organization_id=1, user_type=loginDetails["user_type"], userIdentifier=userIdentified)
                            user.save_to_db()

                else:

                    user = User.query.filter_by(userIdentifier=userIdentified).first()

                
                if user:
                    login_user(user)
                    access_token = create_access_token(identity=user.id)
                    refresh_token = create_refresh_token(identity=user.id)

                else:
                    print("User not find")
                    return {
                        "message" : "Please logout your apple id from the device settings. And then try again!!"
                    }, 400



                return {"data":
                    {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "id": user_schema.dump(user),
                        "organization_id": 1
                    },
                        "message": "User logged in successfully",
                        "success": True
                    }, 201

        except Exception as e:
            print("Error >>>>>>", e)

            return {
                "Error": e
            }, 400

class WixTestUrl(Resource):
    @classmethod
    def post(cls):

        urlDetails = request.get_json()

        print("urlDetails>>>>>", urlDetails)

class UserLogin(Resource):
    parser = reqparse.RequestParser()

    parser.add_argument('email',
                        type=str,
                        required=True,
                        help='This field cannot be blank!')
    parser.add_argument('password',
                        type=str,
                        required=True,
                        help='This field cannot be blank!')
    @classmethod
    def post(cls):
        cls.data = cls.parser.parse_args()

        email = cls.data["email"]
        password = cls.data["password"]


        user = User.query.filter_by(email=email).first()
        if not user:
            return {"data":{},
                    "message": "Please check your login details and try again.",
                    "success": False
                    }, 400
        else:
            if user.is_email_confirmed:
                pass
            else:
                return {"data":{},
                        "message": "Account not activated yet. Please check the mail to activate the account.",
                        "success": False
                        }, 400
            # check if user actually exists
            # take the user supplied password, hash it, and compare it to the hashed password in database
            if not user or not check_password_hash(user.password, password):
                return {"data": {},
                                "message": "Please check your login details and try again.",
                                "success": False
                                }, 400  # if user doesn't exist or password is wrong, reload the page

            # if the above check passes, then we know the user has the right credentials
            else:
                user.authenticated = True
                user.save_to_db()
                login_user(user)
                access_token = create_access_token(identity=user.id)
                refresh_token = create_refresh_token(identity=user.id)

                try:
                    organization1 = OrganizationModel.query.filter_by(id=user.organization_id).first()
                except OrganizationModel.DoesNotExist:

                    return {"data": {},
                            "message": "Organization doesn't exists",
                            "success": False
                            }, 400
                return {"data":
                    {
                        # "token":token.decode('UTF-8'),
                        "token": access_token,
                        "refresh_token": refresh_token,
                        "user": user_schema.dump(user),
                        "organization": organization_schema.dump(organization1)
                    },
                    "message": "User logged in successfully",
                    "success": True
                }, 201