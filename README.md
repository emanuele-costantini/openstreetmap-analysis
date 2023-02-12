# OpenStreetMap Data

### Script Overview

This script performs data extraction through OSM Api, retrieving the graph of roads and other interesting items like traffic lights and road surface.

### How to launch locally

1. Be sure to have Python 3.10 and packages from requirements.txt properly installed.
2. Open a terminal window, then type:

```
python src/main.py --city <city_you_want>
```

and replace "city_you_want" with the city you are interested in.

### How to launch as Docker container

Trying to install gdal could result in dependencies issues (especially on Linux).
Build the app as a container if you can't resolve issues while installing required libraries.

1. Be sure to have Docker installed on your machine.
2. From the openstreetmap-analysis project folder, build the Docker image:
   ```
   docker build . -t osm
   ```
3. Create the Docker_volume folder under directory Data:
   ```
   mkdir -p Data/Docker_volume
   ```
4. Run the container mounting the volume:
   ```
   docker run -v $(readlink -f Data/Docker_volume):/osm/Data osm <city_you_want>
   ```
   The created data will be saved in Docker_volume folder.
