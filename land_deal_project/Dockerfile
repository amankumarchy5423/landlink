FROM python:3.10-slim-buster

WORKDIR ./app

COPY . /app 

RUN apt update -y 

CMD [ "python3","app.py" ]

EXPOSE 8080