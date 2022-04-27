
# base image
FROM python:3.6
# setup environment variable
#ENV DockerHOME=/home/project

# set work directory RUN mkdir -p $DockerHOME
RUN mkdir /project

# where your code lives  WORKDIR $DockerHOME
WORKDIR /project

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN python -m pip install --upgrade pip

# run this command to install all dependencies
ADD requirements.txt /project
RUN pip install -r requirements.txt

# copy whole project to your docker home directory. COPY . $DockerHOME
COPY . /project


# port where the Django app runs
EXPOSE 9100
# start server
#CMD python manage.py makemigrations
CMD python manage.py migrate
CMD python manage.py runserver 0.0.0.0:9100
