FROM python:3.10-slim

WORKDIR /bf-autodatavideos-crawler

RUN apt-get update
COPY /crawler /bf-autodatavideos-crawler/crawler
COPY /utils /bf-autodatavideos-crawler/crawler/utils
COPY /database /bf-autodatavideos-crawler/crawler/database

WORKDIR /bf-autodatavideos-crawler/crawler

RUN pip install -r requirements.txt

CMD ["python", "-u", "main.py"]
