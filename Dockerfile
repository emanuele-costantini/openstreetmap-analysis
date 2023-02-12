FROM python:3.10
MAINTAINER "Emanuele Costantini"

RUN set -ex && mkdir /osm
WORKDIR /osm

COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip~=23.0
RUN pip install -r requirements.txt

COPY ./openstreetmap.analysis/ ./openstreetmap.analysis
ENV PYTHONPATH /osm

CMD ["python", "main.py", "--city"]
ENTRYPOINT ["Milan"]
