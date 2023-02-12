FROM osgeo/gdal:ubuntu-small-latest
MAINTAINER "Emanuele Costantini"

RUN set -ex && mkdir /osm
WORKDIR /osm

COPY requirements.txt ./requirements.txt

RUN apt update
RUN apt install -y python3-pip

RUN pip install --upgrade pip~=23.0
RUN pip install -r requirements.txt

COPY /src ./src
ENV PYTHONPATH /osm

CMD ["Milan"]
ENTRYPOINT ["python", "/osm/src/main.py", "--city"]
