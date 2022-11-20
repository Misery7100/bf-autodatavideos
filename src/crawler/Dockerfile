FROM python:3.10-slim

WORKDIR /autodatavideos

RUN apt-get update
COPY . .

RUN pip install -r requirements.txt

CMD ["python", "-u", "main.py"]
