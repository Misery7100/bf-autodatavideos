FROM python:3.10-slim

WORKDIR /bf-autodatavideos-crawler

RUN apt-get update -y && apt-get upgrade -y

COPY /crawler /bf-autodatavideos-crawler/crawler
COPY /core /bf-autodatavideos-crawler/crawler/core
COPY /database /bf-autodatavideos-crawler/crawler/database
COPY /config.yml /bf-autodatavideos-crawler/crawler/config.yml
COPY /requirements.txt /bf-autodatavideos-crawler/crawler/requirements.txt

WORKDIR /bf-autodatavideos-crawler/crawler

RUN pip install -r requirements.txt

CMD ["python", "-u", "main.py"]
