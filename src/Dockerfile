# FROM ubuntu:latest
# RUN apt-get update -y
# RUN apt-get install -y  python3-pip python3.7-dev build-essential
# COPY . /app
# WORKDIR /app
# RUN pip3  install -r requirements.txt -t /app
# EXPOSE 5002
# ENTRYPOINT ["python3.7"]
# CMD ["app.py"]

# start from an official image
FROM python:3.7

#working directory path in container
WORKDIR /speech_tagging

COPY ./requirements.txt /speech_tagging/requirements.txt

RUN apt-get update \
    && apt-get install gcc -y \
    && apt-get clean
RUN apt-get install ffmpeg -y

RUN pip install --upgrade pip
RUN pip install -r requirements.txt


# RUN pip install gunicorn

# copy our project code to container
COPY . .

# sudo apt install ffmpeg
# migrate db
# RUN flask db init
# RUN flask db migrate
# RUN flask db upgrade


# expose port 5002 to outside world
#define the default command to run when starting the container
# CMD ["gunicorn","--bind",":5002",]
CMD ["python","app.py"]
