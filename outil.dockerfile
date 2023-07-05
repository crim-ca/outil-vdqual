FROM python:3.9

RUN apt-get install gcc
# set the working directory in the container
WORKDIR /app

COPY requirements.txt requirements.txt

# install dependencies
RUN pip install -r requirements.txt --no-cache-dir

RUN python -c 'import stanza; stanza.download("EN")'
RUN python -c 'import stanza; stanza.download("FR")'
RUN python -m coreferee install en
RUN python -m coreferee install fr
RUN python -m spacy download en_core_web_lg
RUN python -m spacy download en_core_web_trf
RUN python -m spacy download fr_core_news_lg

COPY . .

CMD ["python3", "app.py"]
