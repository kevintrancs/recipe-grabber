from python:2.7 

MAINTAINER Kevin Tran 'kevintrancs@gmail.com'

RUN apt-get update -y

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY ./app

ENTRYPOINT ["python"]

CMD ["links.py"]