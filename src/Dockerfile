FROM python:3.10-slim

WORKDIR /bf-autodatavideos-crawler

ENV PLAINLY_AUTH_KEY ${PLAINLY_AUTH_KEY}

RUN apt-get update
COPY /crawler /bf-autodatavideos-crawler/crawler
COPY /core /bf-autodatavideos-crawler/crawler/core
COPY /database /bf-autodatavideos-crawler/crawler/database

WORKDIR /bf-autodatavideos-crawler/crawler

RUN pip install -r requirements.txt

CMD ["python", "-u", "main.py"]
