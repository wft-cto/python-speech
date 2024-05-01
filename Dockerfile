
# start from an official image
FROM python:3.8

#working directory path in container
WORKDIR /speech_tagging

COPY requirements.txt .

RUN apt-get update \
    && apt-get install gcc -y \
    && apt-get clean    
#RUN apt-get install ffmpeg -y
RUN apt-get install -y libsndfile1

RUN pip install --upgrade pip
RUN pip install -r requirements.txt


# RUN pip install gunicorn

# copy our project code to container
COPY . .

# migrate db
CMD flask src/db init
CMD flask src/db migrate
CMD flask src/db upgrade


# expose port 5002 to outside world
#define the default command to run when starting the container
# CMD ["gunicorn","--bind",":5002",]
CMD python src/app.py
