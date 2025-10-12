FROM python:3.14
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
         gdal-bin libgdal-dev \
         libgeos-dev geos-bin \
         proj-bin libproj-dev \
    && rm -rf /var/lib/apt/lists/* \
ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so
WORKDIR /app
COPY /requirements/ /app/requirements/
RUN pip install --upgrade pip
RUN pip install -r requirements/dev.txt && \
    pip install -r requirements/test.txt && \
    pip install -r requirements/prod.txt
