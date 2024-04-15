from flask_restful import Resource,reqparse
from flask import request
from src.speech_tagging.models.organization import OrganizationModel
from src.speech_tagging.schemas.organization import OrganizationSchema
from validate_email import validate_email
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager,login_user
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,create_refresh_token)

import strgen

from sqlalchemy import asc

organization_schema = OrganizationSchema()
organizations_schema = OrganizationSchema(many=True)


# class OrganizationSignUp(Resource):

#     def post(self):
#         """
#         register organization
#         """
#         organization_json = request.get_json()
#         print(organization_json)
#         data = organization_schema.load(organization_json)
#         if organization_json is None:
#             return {"data": 
#                             {},
#                     "message":"Invalid data",
#                     "success":"False"
#                     }, 400
        
#         for key,value in organization_json.items():
#             if value:
#                 pass
#             else:
#                 return {"data": 
#                                 {},
#                         "message":"This " + key + " field is required",
#                         "success":False
#                         }, 400

#         for key, value in organization_json.items():
#             if value:
#                 if key == "email":
#                     if value:
#                         is_valid = validate_email(value)
#                         if is_valid:
#                             pass
#                         else:
#                             return {"data":
#                                                 {},
#                                             "message": "Enter valid email",
#                                             "success": False
#                                             }, 400
#                 else:
#                     pass
#             else:
#                 return {"data":
#                                     {},
#                                 "message": "This " + key + " field is required",
#                                 "success": False
#                                 }, 400

#         organization1 = OrganizationModel.query.filter_by(email=organization_json['email']).first()

        
#         if organization1 :
#             return  {"data": 
#                             {},
#                         "message":"Organization with this email already exists",
#                         "success":False
#                         }, 400

#         password = organization_json["password"]

#         while True:
#             organization_id = strgen.StringGenerator("[\d\w]{10}").render()
#             old_org_id = OrganizationModel.query.filter_by(organization_id=organization_id).first()
#             if not old_org_id:
#                 break

#         organization_json.update({"password":generate_password_hash(password,method='sha256'),"organization_id":organization_id})
#         organization = organization_schema.load(organization_json)


#         try:
#             token = generate_confirmation_token(email)
#             confirm_url = url_for('confirm_email', token=token, _external=True)
#             html = render_template('activate_account.html', confirm_url=confirm_url)
#             subject = "Please confirm your email"
#             send_email(email, subject, html)  
            
#             organization.save_to_db()
#         except Exception as e:
#             return {"data": 
#                             {},
#                     "message": "Something goes wrong in server",
#                     # "message": str(e),
#                     "success":False
#                     }, 500

#         organization_json.pop('password')

#         return {"data":
#                         {
#                         "organization": organization_json
#                         },
#                 "message":"Organization created successfully",
#                 "success":True
#                 }, 201


class OrganizationLogin(Resource):
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

        organization = OrganizationModel.query.filter_by(email=email).first()
        if organization is None:
            return {"data":
                    {},
                "message":"Please check your login details and try again.",
                "success":False
                }, 400
        else:
            if organization.is_email_confirmed:
                pass
            else:
                return {"data": 
                                    {},
                                "message":"Account not activated yet. Please check the mail to activate the account.",
                                "success":False
                                }, 400
            # check if organization actually exists
            # take the organization supplied password, hash it, and compare it to the hashed password in database
            if not organization or not check_password_hash(organization.password, password):
                return {"data": {},
                                "message": "Please check your login details and try again.",
                                "success": False
                                }, 400  # if user doesn't exist or password is wrong, reload the page

            # if the above check passes, then we know the user has the right credentials
            else:
                organization.authenticated = True;
                organization.save_to_db()
                login_user(organization)
                access_token = create_access_token(identity=organization.id)
                refresh_token = create_refresh_token(identity=organization.id)

                return {"data":
                    {
                        # "token":token.decode('UTF-8'),
                        "access_token": access_token,
                        "refresh_token":refresh_token,
                        "organization_id":organization.id
                    },
                    "message": "Organization logged in successfully",
                    "success": True
                }, 201

class OrganizationDetail(Resource):
    def get(self,email):
        organization = OrganizationModel.query.filter_by(email=email).first()

        if organization is None:
            return {"data":{},
                    "message": "Organization with given email does not exist.",
                    "success": False
                    }, 400

        return {"message": "Data retrieved successfully",
                "data": organization_schema.dump(organization),
                "success":True}, 201

    def delete(self,email):
        organization = OrganizationModel.query.filter_by(email=email).first()

        if organization is None:
            return {"data": {},
                    "message": "Please check your login details and try again.",
                    "success": False
                    }, 400

        try:
            organization.delete_from_db()

            return {"message": "Organization deleted successfully",
                    "data":None,
                    "success": True}, 201
        except:
            return {"message": "Organization could not be deleted",
                    "data": None,
                    "success": False}, 500


class OrganizationDetailById(Resource):
    def get(self,org_id):
        organization = OrganizationModel.find_by_id(_id=org_id)

        if organization is None:
            return {"data":{},
                    "message": "Organization with given id does not exist.",
                    "success": False
                    }, 400

        return {"message": "Data retrieved successfully",
                "data": organization_schema.dump(organization),
                "success":True}, 201

    def delete(self,org_id):
        organization = OrganizationModel.find_by_id(_id=org_id)

        if organization is None:
            return {"data": {},
                    "message": "Organization with given id does not exist.",
                    "success": False
                    }, 400

        try:
            organization.delete_from_db()

            return {"message": "Organization deleted successfully",
                    "data":None,
                    "success": True}, 201
        except:
            return {"message": "Organization could not be deleted",
                    "data": None,
                    "success": False}, 500


    parser = reqparse.RequestParser()
    parser.add_argument('name',
                        type=str,
                        required=True,
                        help='Organization name cannot be blank!')
    parser.add_argument('location',
                        type=str,
                        required=True,
                        help='Location cannot be blank!')
    parser.add_argument('contact_no',
                        type=str,
                        required=True,
                        help='Contact number cannot be blank!')

    @classmethod
    def put(cls,org_id):
        cls.data = cls.parser.parse_args()

        organization = OrganizationModel.find_by_id(_id=org_id)
        if organization is None:
            return {"data": {},
                    "message": "Organization with given id does not exist.",
                    "success": False
                    }, 400

        try:
            organization.name = cls.data["name"]
            organization.location = cls.data["location"]
            organization.contact_no = cls.data["contact_no"]
            organization.save_to_db()

            return {"message": "Organization profile updated successfully",
                    "data":None,
                    "success": True}, 201
        except:
            return {"message": "Organization could not be updated",
                    "data": None,
                    "success": False}, 500


class OrganizationList(Resource):
    def get(self):
        organizations = OrganizationModel.find_all()

        if organizations is None:
            return {"data":{},
                    "message": "Organization does not exist.",
                    "success": False
                    }, 400

        return {"message": "Data retrieved successfully",
                "data": organizations_schema.dump(organizations),
                "success":True}, 201
