import dotenv
import logging

import numpy
# import tensorflow
# print(tensorflow.__version__)


print('IN')

# import jwt
import datetime
from validate_email import validate_email
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from flask_restful import Api, Resource
from flask_uploads import configure_uploads, patch_request_class
from flask_migrate import Migrate
from flask_login import LoginManager,login_user, login_required, current_user, logout_user
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity,create_refresh_token
)

from marshmallow import ValidationError
import strgen

from config import *
from speech_tagging.commons.audio_helper import AUDIO_SET
from speech_tagging.commons.text_helper import TEXT_FILE_SET
from speech_tagging.definitions import *
from speech_tagging.ma import ma

from speech_tagging.resources.user import UserDetail, UserDetailFromEmail,UserLogin, UserAppleLogin, WixTestUrl
from speech_tagging.resources.attendee import Attendee, AttendeeVoice, AttendeeRegister, AttendeeDelete
from speech_tagging.resources.audio import MeetingAudioUpload, MeetingAudio, MeetingAudios, Audio
from speech_tagging.resources.meeting import Meeting
from speech_tagging.resources.organization import (OrganizationLogin, OrganizationDetail,
                                                     OrganizationList, OrganizationDetailById)
from speech_tagging.resources.train_speaker import TrainSpeaker, DeleteAttendeeEmbeding
from speech_tagging.resources.transcribe import Transcribe, UpdateTranscribeJsonFile, GetTextFile
from speech_tagging.resources.recognize_speaker import RecognizeSpeaker
from speech_tagging.resources.attendee import AllAttendee
from speech_tagging.resources.custom_language_model import (
    LanguageModel, LanguageModelList, LanguageModelDetail, TrainLanguageModel,
    Corpus, ListCorpus, AvailableLanguageModelList, AddCorpus, DeleteLanguageModel
)

from speech_tagging.db import db

from speech_tagging.models.user_registration import User
from speech_tagging.models.organization import OrganizationModel
from speech_tagging.models.audio import AudioModel

from speech_tagging.schemas.user import UserSchema
from speech_tagging.schemas.organization import OrganizationSchema
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


dotenv.load_dotenv(PATH_ENV)

from authlib.integrations.flask_client import OAuth
from flask import Flask, redirect, url_for, session
from flask_mail import Mail, Message

from itsdangerous import URLSafeTimedSerializer




user_schema = UserSchema()

mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    # "MAIL_PORT": 465,
    "MAIL_PORT": 587,
    "MAIL_USE_TLS": True,
    "MAIL_USE_SSL": False,
    "MAIL_USERNAME": 'newruntech@gmail.com',
    "MAIL_PASSWORD": 'wbyknlbcizxlplsn',
    "MAIL_DEFAULT_SENDER": 'newruntech@gmail.com'
}
# mail_settings = {
#     "MAIL_SERVER": os.environ.get("MAIL_SERVER"),
#     "MAIL_PORT": os.environ.get("MAIL_PORT"),
#     "MAIL_USE_TLS": False,
#     "MAIL_USE_SSL": True,
#     "MAIL_USERNAME": os.environ.get("MAIL_USERNAME"),
#     "MAIL_PASSWORD": os.environ.get("MAIL_PASSWORD"),
#     "MAIL_DEFAULT_SENDER": os.environ.get("MAIL_DEFAULT_SENDER")
# }

organization_schema = OrganizationSchema()
user_schema = UserSchema()

app = Flask(__name__,static_folder='speech_tagging/static')

handler = logging.FileHandler("test.log")  # Create the file logger
app.logger.addHandler(handler)             # Add it to the built-in logger
app.logger.setLevel(logging.DEBUG)         # Set the log level to debug

# logging.basicConfig(filename='error.log',level=logging.DEBUG)

app.config.update(mail_settings)
mail = Mail(app)

CORS(app,resources=r'/speech-meeting-app/*')



app.secret_key = os.environ.get("secret_key")
app.config['SECRETE_KEY'] = os.environ.get("secret_key")
app.config['SECURITY_PASSWORD_SALT'] = os.environ.get('security_password_salt')

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://{user:}:{password}@{host:}:3306/{db:}'.format(
    user=os.environ.get("USER_MYSQL"), password=os.environ.get("PASSWORD"), host=DB_URL, db=os.environ.get("DATABASE"))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['UPLOADED_AUDIOS_DEST'] = PATH_AUDIO

# Setup the Flask-JWT-Extended extension
app.config['JWT_SECRET_KEY'] = os.environ.get("secret_key")
jwt = JWTManager(app)

# for login
login_manager = LoginManager()
login_manager.init_app(app)

patch_request_class(app, 500 * 1024 * 1024)  # restrict max upload image size to 100MB
configure_uploads(app, AUDIO_SET)



# oAuth Setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',  # This is only needed if using openId to fetch user info
    client_kwargs={'scope': 'openid email profile'},
)

api = Api(app, prefix='/speech-meeting-app')


@app.before_first_request
def create_tables():
    db.create_all()  # creates 'data.db' with all the tables unless they already exist


@app.errorhandler(ValidationError)
def handle_marshmallow_validation(err):
    return jsonify(err.normalized_messages()), 400


# for mail confirmation
def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])


def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except:
        return False
    return email

# API end points
api.add_resource(UserDetail, "/user/<int:user_id>")
api.add_resource(UserDetailFromEmail, "/user-detail/<string:email>")
api.add_resource(UserLogin, "/login")
api.add_resource(UserAppleLogin, "/apple/login")
api.add_resource(WixTestUrl, "/wix/test/url")

api.add_resource(OrganizationLogin, "/organization-login")
api.add_resource(OrganizationList, "/organizations")
api.add_resource(OrganizationDetail, "/organization-detail/<string:email>")
api.add_resource(OrganizationDetailById, "/organization/<int:org_id>")




api.add_resource(Meeting, "/meeting")
api.add_resource(MeetingAudioUpload, "/upload/audio")
api.add_resource(MeetingAudio, "/audio/<int:audio_id>")
api.add_resource(MeetingAudios, "/audios")
api.add_resource(Audio, "/audio")

api.add_resource(AttendeeRegister, "/register-attendee")
api.add_resource(Attendee, "/attendee/<int:attendee_id>")
# api.add_resource(AttendeeDetail, "/get/attendee/<int:attendee_id>")
api.add_resource(AttendeeVoice, "/attendee-voice")
api.add_resource(AllAttendee, "/attendees")
api.add_resource(AttendeeDelete, "/organization/<int:organization_id>/attendee/<int:attendee_id>/delete")
api.add_resource(DeleteAttendeeEmbeding, "/attendee/<int:attendee_id>")

api.add_resource(TrainSpeaker, "/train-attendee")

# api.add_resource(Transcribe, "/transcribe/<string:filename>")
api.add_resource(Transcribe, "/transcribe/<int:organization_id>/<string:model_name>/<int:audio_id>")
api.add_resource(UpdateTranscribeJsonFile, "/transcribe-file/update/<int:audio_id>")
api.add_resource(GetTextFile, "/get/transcribe-files")
# api.add_resource(GetTranscribeJsonFile, "/transcribe-files/<int:audio_id>")

# api.add_resource(RecognizeSpeaker, "/recognize-speaker/<int:meeting_id>")

api.add_resource(RecognizeSpeaker, "/recognize-speaker/<int:audio_id>")

api.add_resource(LanguageModel, "/create-language-model")
api.add_resource(DeleteLanguageModel, "/delete-language-model/<int:organization_id>/<string:model_name>")

api.add_resource(LanguageModelList, "/language-models/<int:organization_id>")
api.add_resource(LanguageModelDetail, "/language-model-details/<int:organization_id>/<string:model_name>")
api.add_resource(TrainLanguageModel, "/train-language-model/<int:organization_id>/<string:model_name>")

api.add_resource(Corpus, "/create-corpus")
api.add_resource(ListCorpus, "/list-corpus/<int:organization_id>/<string:model_name>")
api.add_resource(AvailableLanguageModelList, "/list-available-language-model/<int:organization_id>")
api.add_resource(AddCorpus, "/add-corpus/<int:organization_id>/<string:model_name>/<int:corpus_id>")


# Social Auth
# api.add_resource(GoogleLogin, "/login/google")
# api.add_resource(GoogleAuthorize, "/login/google/authorized", endpoint="google.authorize")


db.init_app(app)
ma.init_app(app)


migrate = Migrate(app, db)


# home route
@app.route('/')
def home():    
    return render_template('index.html')


# @app.route('/sas')
# def sas():    
#     return print('SAS')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# decorator to check token
# def token_required(f):
#     @wraps(f)
#     def decorated(*args,**kwargs):
#         token = None
#         if 'token' in request.headers:
#             token = request.headers['token']
#         else:
#             return jsonify(message="Token is missing"), 401
#         # print(token)
#         try:
#             data = jwt.decode(token,app.config['SECRETE_KEY'])
#             # print("-------------------------------------------------------")
#             # print(data)
#             current_user = User.query.filter_by(id = data['user_id']).first()
#             # print(current_user)
#         except Exception as e:
#             # return jsonify(message=str(e)), 401
#             return jsonify(message="Token is invalid"), 401
        
#         return f(current_user,*args,**kwargs)
    
#     return decorated
            
@app.route('/protected')
@jwt_required
def protected():
    # print(current_user.username)
    userid = get_jwt_identity()
    print(userid)
    return jsonify(user_id=userid)

# @app.route('/unprotected')
# def unprotected():
#     return jsonify({"message":"Anyone can view this"})

@app.route('/speech-meeting-app/signup',methods=['POST'])
def user_signup():
    if request.method == 'POST':
        data = request.get_json()

        organization_id = data.get("organization_id")
        if organization_id:
            organization = OrganizationModel.find_by_organization_id(organization_id)
            if not organization:
                return jsonify({"data":
                                    {},
                                "message": "Organization with the id not found",
                                "success": False
                                }), 400

        else:
            return jsonify({"data":
                                {},
                            "message": "Organization with the id not found",
                            "success": False
                            }), 400
        try:
            confirm_password = data['confirm_password']
        except:
            return jsonify({"data":
                                {},
                            "message": "Please send password confirmation too ",
                            "success": False
                            }), 400

        data.update({"organization_id": organization.id})
        data2 = data.copy()
        del data2["confirm_password"]
        user_detail = user_schema.load(data2)

                
        if not organization :
            return {"data":
                        {},
                    "message": "Organization not found",
                    # "message": str(e),
                    "success": False
                    }, 400        
        
        username = data['username']
        email = data['email']
        password = data['password']
        # first_name = data["first_name"]
        # last_name = data["last_name"]
        # gender = data["gender"]

        is_valid = validate_email(data["email"])
        if is_valid:
            pass
        else:
            return jsonify({"data":
                                {},
                            "message":"Enter valid email",
                            "success":False})


        if (password != confirm_password):
            return jsonify(message="Password doesn't match",success="False"), 400

        user1 = User.query.filter_by(username=username).first()
        user2 = User.query.filter_by(email=email).first()
        # org2 = OrganizationModel.query.filter_by(email=email).first()
        
        if user1:
            return jsonify({"data": 
                                {},
                            "message":"Username already exists",
                            "success":False
                            }), 400
        
        if user2 :
            return jsonify({"data": 
                                {},
                            "message":"Email already exists",
                            "success":False
                            }), 400
        try:
            # new_user = User(username=username,
            #                 email=email,
            #                 password=generate_password_hash(password, method='sha256'),
            #                 organization_id=organization_id,
            #                 first_name=first_name,
            #                 last_name=last_name,
            #                 gender=gender)
            # db.session.add(new_user)
            # db.session.commit()

            try:
                data2.update({"password":generate_password_hash(data2["password"],method='sha256')})
                user_detail = user_schema.load(data2)

                user_detail.save_to_db()
            except:
                return {"message": "Error while inserting"}, 500

            token = generate_confirmation_token(email)
            confirm_url = url_for('confirm_email', token=token, _external=True)
            html = render_template('activate_account.html', confirm_url=confirm_url)
            subject = "Please confirm your email"
            send_email(email, subject, html)  
            
        except Exception as e:
            return jsonify({"data": 
                                {},
                            # "message":"Something goes error in server",
                            "message":str(e),
                            "success":False
                            }), 500
        return jsonify({"data": 
                            {
                                "user":user_schema.dump(user_detail)
                            },
                        "message":"Account created successfully. A confirmation email has been sent via email. Activate the account within a hour",
                        "success":True
                        }), 201

@app.route('/speech-meeting-app/organization-signup',methods=['POST'])
def organization_signUp():
    """
    register organization
    """
    organization_json = request.get_json()
    data = organization_schema.load(organization_json)
    if organization_json is None:
        return {"data": 
                        {},
                "message":"Invalid data",
                "success":False
                }, 400
    
    for key,value in organization_json.items():
        if value:
            pass
        else:
            return {"data": 
                            {},
                    "message":"This " + key + " field is required",
                    "success":False
                    }, 400

    for key, value in organization_json.items():
        if value:
            if key == "email":
                if value:
                    is_valid = validate_email(value)
                    if is_valid:
                        pass
                    else:
                        return {"data":
                                            {},
                                        "message": "Enter valid email",
                                        "success": False
                                        }, 400
            else:
                pass
        else:
            return {"data":
                                {},
                            "message": "This " + key + " field is required",
                            "success": False
                            }, 400

    organization1 = OrganizationModel.query.filter_by(email=organization_json['email']).first()
    user1 = User.query.filter_by(email=organization_json['email']).first()
        
    if organization1 or user1:
        return  {"data": 
                        {},
                    "message":"Email already exists",
                    "success":False
                    }, 400

    password = organization_json["password"]

    while True:
        organization_id = strgen.StringGenerator("[\d\w]{10}").render()
        old_org_id = OrganizationModel.query.filter_by(organization_id=organization_id).first()
        if not old_org_id:
            break

    organization_json.update({"password":generate_password_hash(password,method='sha256'),"organization_id":organization_id})
    organization = organization_schema.load(organization_json)


    try:
        organization.save_to_db()

        token = generate_confirmation_token(organization_json['email'])
        confirm_url = url_for('confirm_email', token=token, _external=True)
        html = render_template('activate_account.html', confirm_url=confirm_url)
        subject = "Please confirm your email"
        send_email(organization_json['email'], subject, html)  
        
    except Exception as e:
        return {"data": 
                        {},
                # "message": "Something goes wrong in server",
                "message": str(e),
                "success":False
                }, 500

    organization_json.pop('password')

    return {"data":
                    {
                    "organization": organization_json
                    },
            "message":"Organization created successfully. A confirmation email has been sent via email. Activate the account within a hour",
            "success":True
            }, 201


def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=app.config['MAIL_DEFAULT_SENDER']
    )
    mail.send(msg)

@app.route('/speech-meeting-app/confirm/<token>')
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        # flash('The confirmation link is invalid or has expired.', 'danger')
        return jsonify({"data": 
                            {},
                        "message":"The confirmation link is invalid or has expired.",
                        "success":False
                        }), 400
    try:
        user = User.query.filter_by(email=email).first()
        if user.is_email_confirmed:
            # flash('Account already confirmed. Please login.', 'success')
            return jsonify({"data": 
                                {},
                            "message":"Your account has been activated. Please login",
                            "success":True
                            }), 200
        else:
            user.is_email_confirmed = True
            # user.confirmed_on = datetime.datetime.now()
            db.session.add(user)
            db.session.commit()
            # flash('You have confirmed your account. Thanks!', 'success')
            return jsonify({"data": 
                                {},
                            "message":"Your account has been activated. Please login",
                            "success":True
                            }), 200
    except Exception as e:
        pass

    try:   
        organization = OrganizationModel.query.filter_by(email=email).first_or_404()

        if organization.is_email_confirmed:
            return jsonify({"data": 
                                {},
                            "message":"Your account has been activated. Please login",
                            "success":True
                            }), 200
        else:
            organization.is_email_confirmed = True
            db.session.add(organization)
            db.session.commit()
            return jsonify({"data": 
                                {},
                            "message":"Your account has been activated. Please login",
                            "success":True
                            }), 200
    except Exception as e:
        pass

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify(success="You have successfully logged out")



# Social Auth
@app.route('/speech-meeting-app/google/login')
def login():
    google = oauth.create_client('google')  # create the google oauth client
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/authorize')
def authorize():
    google = oauth.create_client('google')  # create the google oauth client
    token = google.authorize_access_token()  # Access token from google (needed to get user info)
    resp = google.get('userinfo')  # userinfo contains stuff u specificed in the scrope
    user_info = resp.json()
    user = oauth.google.userinfo()  # uses openid endpoint to fetch user info
    # Here you use the profile/user data that you got and query your database find/register the user
    # and set ur own data in the session not the profile from google
    session['profile'] = user_info
    session.permanent = True  # make the session permanant so it keeps existing after broweser gets closed
    email = user.get("email")

    organization = OrganizationModel.query.filter_by(email=email).first()

    if not organization:

        while True:
            organization_id = strgen.StringGenerator("[\d\w]{10}").render()
            old_org_id = OrganizationModel.query.filter_by(organization_id=organization_id).first()
            if not old_org_id:
                break
        organization = OrganizationModel(email=email,organization_id=organization_id)
        organization.save_to_db()


    access_token = create_access_token(identity=organization.id, fresh=True)
    refresh_token = create_refresh_token(organization.id)

    return {"data":
        {
            # "token":token.decode('UTF-8'),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "id":organization.id,
            "organization_id": organization.organization_id
        },
               "message": "User logged in successfully",
               "success": True
           }, 201


# @app.route('/speech-meeting-app/apple-login', methods=['POST'])
# def login():

#     print("In Apple Login")

#     loginDetails = request.get_json()

#     email = loginDetails.email

#     organization = OrganizationModel.query.filter_by(email=email).first()

#     if not organization:

#         while True:
#             organization_id = strgen.StringGenerator("[\d\w]{10}").render()
#             old_org_id = OrganizationModel.query.filter_by(organization_id=organization_id).first()
#             if not old_org_id:
#                 break
#         organization = OrganizationModel(email=email,organization_id=organization_id)
#         organization.save_to_db()

#     else:
#         return {
#             "message": "User already exists!!"
#         }, 400

#     return {"data":
#         {
#             "access_token": loginDetails.authorizationCode,
#             "refresh_token": loginDetails.identityToken,
#             "id":organization.id,
#             "organization_id": organization.organization_id
#         },
#                "message": "User logged in successfully",
#                "success": True
#            }, 201

def send_token_via_mail(user):
    try:
        token = strgen.StringGenerator("[\d\w]{8}").render()
        user.password = generate_password_hash(token,method='sha256')
        user.save_to_db()


        html = render_template('forgot_password.html', user=user, token=token)
        subject = "Reset Your Password"
        send_email(user.email, subject, html) 
        return jsonify({"data": 
                            {},
                        "message":"Please check your mail for new password",
                        "success":True
                        }), 200
    except Exception as e:
        return jsonify({"data": 
                            {},
                        "message":"Something goes error in server",
                        # "message":str(e),
                        "success":False
                        }), 500
    


@app.route('/speech-meeting-app/forgot-password/<string:email>')
def forgot_password(email):
    is_valid = validate_email(email)
    if is_valid:
        pass
    else:
        return jsonify({"data":
                            {},
                        "message":"Enter valid email",
                        "success":False})


    user = User.query.filter_by(email=email).first()
    organization = OrganizationModel.query.filter_by(email=email).first()
    if user:
        return send_token_via_mail(user)
    elif organization:
        return send_token_via_mail(organization)
    else:
        return jsonify({"data": 
                            {},
                        "message":"Invalid user or organization",
                        "success":False
                        }), 500

        # try:
        #     token = strgen.StringGenerator("[\d\w]{8}").render()
        #     user.password = generate_password_hash(token,method='sha256')
        #     user.save_to_db()


        #     html = render_template('forgot_password.html', user=user, token=token)
        #     subject = "Reset Your Password"
        #     send_email(user.email, subject, html) 
        #     return jsonify({"data": 
        #                         {},
        #                     "message":"Please check your mail for new password",
        #                     "success":True
        #                     }), 200
        # except Exception as e:
        #     return jsonify({"data": 
        #                         {},
        #                     "message":"Something goes error in server",
        #                     # "message":str(e),
        #                     "success":False
        #                     }), 500
    
def save_new_password(user, data):
    if (check_password_hash(user.password, data["current_password"])):
        pass
    else:
        return jsonify(message="Current Password doesn't matched",success=False), 400

    if (data['password'] != data['confirm_password']):
        return jsonify(message="Password doesn't match",success=False), 400

    try:
        user.password = generate_password_hash(data["password"],method='sha256')
        user.save_to_db()

        return jsonify({"data": 
                            {},
                        "message":"Password changed successfully",
                        "success":True
                        }), 201        

    except Exception as e:
        return jsonify({"data": 
                            {},
                        "message":"Error while inserting",
                        "success":False
                        }), 500   


@app.route('/speech-meeting-app/reset-password/<string:email>',methods=['POST'])
def reset_password(email):
    is_valid = validate_email(email)
    if is_valid:
        pass
    else:
        return jsonify({"data":
                            {},
                        "message":"Enter valid email",
                        "success":False})
    data = request.get_json()
    organization = OrganizationModel.query.filter_by(email=email).first()
    user = User.query.filter_by(email=email).first()
        
    if request.method == 'POST':

        if user:
            return save_new_password(user, data)
        elif organization:
            return save_new_password(organization, data)
        else:
            return jsonify({"data": 
                                {},
                            "message":"Invalid user or organization",
                            "success":False
                            }), 500

            # if (data['password'] != data['confirm_password']):
            #     return jsonify(message="Password doesn't match",success=False), 400

            # try:
            #     user.password = generate_password_hash(data["password"],method='sha256')
            #     user.save_to_db()
            
            #     return jsonify({"data": 
            #                         {},
            #                     "message":"Password changed successfully",
            #                     "success":True
            #                     }), 201        

            # except Exception as e:
            #     return jsonify({"data": 
            #                         {},
            #                     "message":"Error while inserting",
            #                     "success":False
            #                     }), 500



if __name__ == '__main__':

    # app.run(port=5000, use_reloader=False, host='0.0.0.0')
     app.run(port=5002)
