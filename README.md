# Speech Tagging Application

### STEPS TO RUN THE PROJECT

```
1. Create new folder speech_tagging
2. Clone the git repository in speech_tagging folder
   - git clone https://gitlab.com/lakhabishal/speech-tagging.git
3. Create virtual environment 'venv' 
    - virtualenv -p python3.6 venv
4. Activate virtual environment 
    - venv/bin/activate
5. Install MySQL
    - sudo apt update
    - sudo apt install mysql-server
6. Securing MySQL
    - sudo mysql_secure_installation

    As you run this command, the first thing you will be asked to do is to setup the Validate Password plugin.
    This lets you set a secure password for root depending on the strength of the password you want to choose.
    Enter Y in order to run the Validate Password Plugin or enter any key for No.
    The system will then ask you for the new password of root. Enter and then re-enter the password.
    The system will now ask you with a series of questions, one by one, and you can set the security of your system 
    depending on your answers to these questions. 

    a. The first question will ask you if you want to remove the anonymous test users.
       Press y and hit Enter.
    b. The second question will ask if you want to disallow root login from a remote system. 
       This should normally be your choice because, for a secure system, root should only be allowed to connect from the localhost.
       Thus, we recommend entering y.
    c. The 3rd question will ask you if you want to remove the default MySQL database named “test” from your system
       and also remove the access to it. Enter y to remove this test database.
    d. In order for all your above-configured changes to take effect, the system needs to reload the privilege tables.
       Enter y and all your security changes will be committed.
7.  Configuring Root to use MySQL shell
    a. Start MySQL shell
        - sudo mysql
    b. Check authentication method for MySQL users 
        - SELECT user,authentication_string,plugin,host FROM mysql.user;
            You can see that root is using the auth-socket plugin for authentication by default.
    c. Change the authentication method for root
        - ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'enter_password';
    d. Reload grant tables
        - FLUSH PRIVILEGES;
    e. Recheck authentication method for MySQL users
        - SELECT user,authentication_string,plugin,host FROM mysql.user;
            You will see that your root user is now using the mysql_native_password plugin for authentication.
8.  Create Database
    - CREATE DATABASE database_name; 
    - exit
9.  Configure database to the project
    a. Create .env file along the side of .env.example file. 
    b. Copy the contents of the .env.example file to .env file.
    c. Update password and database in .env file 
10. pip install -r requirements.txt
11. Run the module app.py
```

### Using Docker
```
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io
sudo apt-get install     apt-transport-https     ca-certificates     curl     gnupg-agent     software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo apt-key fingerprint 0EBFCD88
sudo add-apt-repository    "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"

sudo curl -L "https://github.com/docker/compose/releases/download/1.27.4/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version

cd speech-tagging/
sudo docker-compose up --build
sudo docker-compose up --build
sudo docker-compose build
sudo docker-compose up -d

cd src/
vi dockerfile 

docker ps -a
docker image ls
sudo docker container ls
docker exec -it ed6d57840664 bash
sudo docker exec -it ed6d57840664 bash

docker system prune     // Remove caches
```

### Base URL: hostname/speech-meeting-app/

1. Audio Upload

   **Endpoint:** audio/upload

   **HTTP Request Type:** POST

   **Request  parameters**

   audio: filenamme.wav or filename.mp3 ( with valid audio extension)

   **API Sample result:**

   If same audio name exists:

   ```json
   {
       "message": "An audio with name'heuju.wav' already exists."
   }
   ```

   Else:

   ```json
   {
       "message": "Audio 'heuju_17.wav' uploaded"
   }
   ```

   Make PUT request if you want to ignore checking name.

2. Get list of name of all uploaded audio files

   **Endpoint:** audios

   **HTTP Request Type:** GET

   **API Sample result:**

   

   ```json
   {
       "filenames": [
           "audio3.wav",
           "audio2.wav",
           "The_Expert_Short_Comedy_Sketch.mp3",
           "audio6.wav",
           "media.io_The_Expert_Short_Comedy_Sketch.wav",
           "heuju.wav",
           "audio4.wav",
           "audio5.wav"
       ]
   }
   ```

   

3. Access Audio

   **Endpoint:** /audio/<string:filename>

   **HTTP Request Type:** GET

   **API Sample result:**

   ```json
   {
       "audio_url": "/static/audios/meeting_audio_files/heuju.wav"
   }
   ```

   

   

4. Audio Speech-to-text

   **Endpoint:** transcribe/<string:audio_filename>

   **HTTP Request Type:** GET

   **API Sample result:**

   ```json
   {   
       "message": "Transcription successful",
       "data": {
           "results": [
               {
                   "alternatives": [
                       {
                           "timestamps": [
                               [
                                   "that",
                                   1.11,
                                   1.26
                               ],
                               [
                                   "is",
                                   1.26,
                                   1.38
                               ],
                               [
                                   "big",
                                   1.38,
                                   1.59
                               ]
                           ],
                           "confidence": 0.5,
                           "transcript": "that is big"
                       }
                   ],
                   "final": true
               }
           ],
           "result_index": 0,
           "speaker_labels": [
               {
                   "from": 1.11,
                   "to": 1.26,
                   "speaker": 0,
                   "confidence": 0.48,
                   "final": false
               },
               {
                   "from": 1.26,
                   "to": 1.38,
                   "speaker": 0,
                   "confidence": 0.48,
                   "final": false
               },
               {
                   "from": 1.38,
                   "to": 1.59,
                   "speaker": 0,
                   "confidence": 0.48,
                   "final": false
               }
           ]
       },
       "recognized_speakers": {
           "0": {
               "first_name": "Bishal",
               "last_name": "Heuju",
               "gender": null,
               "email": "heuju.bishal@gmail.com",
               "phone": null
           },
           "1": {
               "first_name": "Bishal",
               "last_name": "Heuju",
               "gender": null,
               "email": "heuju.bishal@gmail.com",
               "phone": null
           },
           "2": {
               "first_name": "Bishal",
               "last_name": "Heuju",
               "gender": null,
               "email": "heuju.bishal@gmail.com",
               "phone": null
           }
       }
   }
   ```

   

   

5. Add Meeting

   **Endpoint:** /meeting

   **HTTP Request Type:** POST

   **Payload**: 

   ```json
   {
   "total_attendee":"1",
   "audio_filename":"media.io_The_Expert_Short_Comedy_Sketch.wav",
   "transcription_filename":"media.io_The_Expert_Short_Comedy_Sketch.json",
   "organization":"Newrun Tech",
   "meeting_location":"Bhaktapur"
   }
   ```

   **API Sample result:**

   ```json
   {
       "message": "Meeting created successfully",
       "meeting": {
           "audio_filename": "media.io_The_Expert_Short_Comedy_Sketch.wav",
           "meeting_location": "Bhaktapur",
           "total_attendee": 1,
           "transcription_filename": "media.io_The_Expert_Short_Comedy_Sketch.json",
           "organization": "Newrun Tech",
           "id": 8
       }
   }
   ```

6. Add Meeting Attendee

   **Endpoint:** /attendee

   **HTTP Request Type:** POST

   **Payload**: 

   ```json
   {
       "email":"heuju.bishal94@gmail.com",
       "first_name":"Bishal",
       "last_name":"Heuju"
       
   }
   ```

   **API Sample result:**

   ````json
   {
       "message": "Attendee added successfully",
       "attendee": {
           "last_name": "Heuju",
           "phone": null,
           "gender": null,
           "email": "heuju.bishal94@gmail.com",
           "first_name": "Bishal",
           "id": 2
       }
   }
   ````

7. Add Attendee's voice sample

   **Endpoint:** /attendee

   **HTTP Request Type:** POST

   **Payload**: 

   ```json
   {
       "attendee_id":1,
       "audio_name":"heuju.wav",
       "voice_list":[{
          "start":0  ,
          "end":5
       },
       {
          "start":0  ,
          "end":3}]
   }
   ```

   **API Sample result:**

   ```json
   {
       "message": "Voice samples saved  successfully"
   }
   ```

8. Train voice sample of attendee for speaker recognition

   **Endpoint:** /train-attendee/<int:attendee_id>

   **HTTP Request Type:** POST

   **API Sample result:**

   ```json
   {
       "message": "Training for attendee with id 1 successful!"
   }
   ```

9. Recognize speakers of a meeting

   **Endpoint:** /recognize-speaker/<int:meeting_id>

   **HTTP Request Type:** POST

   **API Sample result:**

   ```json
   {
       "message": "Speaker recognition completed",
       "speakers": {
           "0": {
               "first_name": "Bishal",
               "last_name": "Heuju",
               "gender": null,
               "email": "heuju.bishal@gmail.com",
               "phone": null
           },
           "1": {
               "first_name": "Bishal",
               "last_name": "Heuju",
               "gender": null,
               "email": "heuju.bishal@gmail.com",
               "phone": null
           },
           "2": {
               "first_name": "Bishal",
               "last_name": "Heuju",
               "gender": null,
               "email": "heuju.bishal@gmail.com",
               "phone": null
           }
       }
   }
   ```

   

10. Not yet