FROM osgeo/gdal:ubuntu-small-latest
LABEL org.opencontainers.image.authors="Emanuele Costantini"

RUN set -ex && mkdir /osm
WORKDIR /osm

COPY requirements.txt ./requirements.txt

RUN apt update
RUN apt install -y python3-pip

RUN pip install --upgrade pip~=23.0
RUN pip install -r requirements.txt

COPY /OSM_extraction_and_processing ./OSM_extraction_and_processing
ENV PYTHONPATH /osm

CMD ["Milan"]
ENTRYPOINT ["python", "/osm/OSM_extraction_and_processing/main.py", "--city"]
