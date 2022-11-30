FROM python:3.10-slim

WORKDIR /bf-autodatavideos-crawler

ENV PLAINLY_AUTH_KEY ${PLAINLY_AUTH_KEY}

RUN apt-get update -y && apt-get upgrade -y
COPY . /bf-autodatavideos-crawler/crawler/

WORKDIR /bf-autodatavideos-crawler/crawler

RUN pip install -r requirements.txt

CMD ["python", "-u", "main.py"]
