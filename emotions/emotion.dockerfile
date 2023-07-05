FROM python:3.9

RUN apt-get install gcc
# set the working directory in the container
WORKDIR /app

# copy the dependencies file to the working directory
COPY requirements.txt .

# install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copying all the files in the container
COPY . .

# Exporting an environment variable for the path of the Emotion configuration file
ENV EMOTION_CONFIG='/app/emotion_config.ini'

# Port listening to if you run the dockerfile alone (not docker compose)
# EXPOSE 5007

CMD [ "python3", "app.py"]